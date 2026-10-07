"""Command line: simulate a coupling trial weight and compute a one-shot correction.

    python -m p2616f.balance balancing_input.toml [--out report.md]
"""

import argparse
import tomllib
import warnings

import numpy as np

from . import balancing as bal
from .model import PumpModel

warnings.filterwarnings("ignore")

CANDIDATE_PLANES = {
    1: "screw pump (NDE end)",
    29: "1st stage impeller",
    60: "mid impeller (stg 4)",
    81: "last impeller",
    111: "coupling",
}


def load(path):
    with open(path, "rb") as f:
        cfg = tomllib.load(f)
    probes = [bal.Probe(p["name"], int(p["station"]), float(p["angle_deg"]),
                        p.get("location", "shaft")) for p in cfg["probe"]]
    setup = bal.Setup(
        probes=probes,
        keyphasor_angle_deg=cfg["instrumentation"].get("keyphasor_angle_deg", 0.0),
        rpm=cfg["machine"].get("rpm", 2980.0),
        balance_station=cfg["balance_plane"].get("station", 111),
        balance_radius_mm=cfg["balance_plane"]["radius_mm"],
        measurement=cfg["instrumentation"].get("measurement", "displacement"),
        amplitude_unit=cfg["instrumentation"].get("amplitude_unit", "um_pp"),
        weight_angle_with_rotation=cfg["balance_plane"].get("weight_angle_with_rotation", False),
    )
    names = [p.name for p in probes]
    v0 = np.array([bal.polar(*cfg["initial"][n]) for n in names])
    weights = None
    if "weights" in cfg:
        weights = np.array([cfg["weights"].get(n, 1.0) for n in names])
    return cfg, setup, v0, weights


def fmt(z, dec=2):
    a, p = bal.to_polar(z)
    return f"{a:8.{dec}f} @ {p:5.0f}"


def run(path):
    cfg, setup, v0, weights = load(path)
    unit = setup.amplitude_unit
    pedestal = cfg.get("pedestal")
    out = []
    p = out.append
    p(f"# P-2616F coupling balance - {setup.rpm:.0f} rpm\n")
    p(f"Balance plane: station {setup.balance_station}, radius {setup.balance_radius_mm} mm; "
      f"amplitudes in {unit}, phase lag in deg, weight angles "
      f"{'with' if setup.weight_angle_with_rotation else 'against'} rotation from KP notch.\n")

    # 1) model influence coefficients for all fluid conditions
    p("## 1. Model influence coefficients (response per 100 g at 0 deg)\n")
    p("```")
    p(f"{'probe':>8} " + " ".join(f"{c:>20}" for c in ("process_1x", "process_2x", "water_1x")))
    models = {c: PumpModel(c, pedestal=pedestal) for c in ("process_1x", "process_2x", "water_1x")}
    Hs = {c: bal.model_influence_coefficients(m, setup) for c, m in models.items()}
    for i, pr in enumerate(setup.probes):
        p(f"{pr.name:>8} " + " ".join(f"{fmt(100 * Hs[c][i], 3):>20}" for c in Hs))
    p("```\n")

    cond = cfg["machine"].get("condition", "process_1x")
    model = models.get(cond) or PumpModel(cond, pedestal=pedestal)
    H = Hs.get(cond)
    if H is None:
        H = bal.model_influence_coefficients(model, setup)

    # 2) is the coupling the right plane?
    p("## 2. Which single plane explains the measured 1X? (model: %s)\n" % cond)
    p("Relative residual 0 = perfect single-plane fit, 1 = no fit.\n")
    p("```")
    for stn, gmm, ang, fit in bal.plane_fit(model, setup, v0, CANDIDATE_PLANES):
        p(f"stn {stn:>3} {CANDIDATE_PLANES[stn]:<24} equiv. unbalance {gmm:10,.0f} g.mm @ {ang:5.0f} deg"
          f"   residual {fit:5.2f}")
    p("```\n")

    # 3) simulated trial run
    trial_g = bal.suggest_trial_weight(H, v0)
    trial_g = float(np.ceil(trial_g / 5.0) * 5.0)
    p(f"## 3. Simulated trial run: {trial_g:.0f} g @ 0 deg (sized for ~30 % change on the largest reading)\n")
    p("```")
    p(f"{'probe':>8} {'run 0 (meas.)':>16} {'trial effect':>16} {'run 1 (pred.)':>16}")
    eff = H * bal.polar(trial_g, 0.0)
    for i, pr in enumerate(setup.probes):
        p(f"{pr.name:>8} {fmt(v0[i]):>16} {fmt(eff[i]):>16} {fmt(v0[i] + eff[i]):>16}")
    p("```\n")

    # 4) one-shot correction from model IC (all conditions -> spread)
    p("## 4. One-shot correction from model influence coefficients\n")
    p("```")
    for c, Hc in Hs.items():
        g, a, _, txt = bal.correction_report(Hc, v0, setup, weights, label=c)
        p(txt)
    p("```\n")

    # 5) measured IC from trial run if available
    if "trial" in cfg:
        t = cfg["trial"]
        v1 = np.array([bal.polar(*t[pr.name]) for pr in setup.probes])
        Hm = bal.measured_influence_coefficients(v0, v1, t["grams"], t["angle_deg"], setup)
        p("## 5. Measured vs model influence coefficients\n")
        p("```")
        p(f"{'probe':>8} {'measured':>16} {'model':>16}  ratio  dphase")
        for i, pr in enumerate(setup.probes):
            r = Hm[i] / H[i]
            p(f"{pr.name:>8} {fmt(Hm[i]):>16} {fmt(H[i]):>16}  {abs(r):5.2f}  "
              f"{np.rad2deg(np.angle(r)):6.0f}")
        g, a, _, txt = bal.correction_report(Hm, v0, setup, weights, label="measured IC")
        p(txt)
        p("```\n")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("config")
    ap.add_argument("--out", help="write the report to this markdown file")
    args = ap.parse_args()
    report = run(args.config)
    print(report)
    if args.out:
        with open(args.out, "w") as f:
            f.write(report)


if __name__ == "__main__":
    main()
