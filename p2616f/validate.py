"""Compare the ROSS model with the OEM lateral analysis and plot coupling sensitivity.

    python -m p2616f.validate [--html outputs/]
"""

import argparse
import warnings
from pathlib import Path

import numpy as np
import ross as rs

from . import data_tables as dt
from . import balancing as bal
from .model import PumpModel, build_disks, build_shaft, rpm2rads

warnings.filterwarnings("ignore")


def dry_criticals(k_bearing=1e12):
    """Forward synchronous critical speeds on rigid supports (rpm)."""
    shaft, sn, _ = build_shaft()
    b = [rs.BearingElement(n=sn[s], kxx=k_bearing, cxx=0)
         for s in (dt.NDE_BEARING_STN, dt.DE_BEARING_STN)]
    rotor = rs.Rotor(shaft, build_disks(sn), b)
    cs = rotor.run_critical_speed(num_modes=24)
    return np.asarray(cs.wn(frequency_units="rpm"))


def damped_modes(condition, rpm=dt.RATED_RPM, fmax_cpm=9000):
    m = PumpModel(condition)
    md = m.rotor.run_modal(speed=float(rpm2rads(rpm)), num_modes=24)
    wd = md.wd * 30 / np.pi
    ld = md.log_dec
    zeta = ld / np.sqrt(4 * np.pi**2 + ld**2)
    whirl = md.whirl_direction()
    return [(f, z, w) for f, z, w in zip(wd, zeta, whirl) if 50 < f < fmax_cpm]


def coupling_sensitivity(condition="process_1x", rpms=None, grams=100.0, radius_mm=100.0):
    """Response at the bearing probes (um pk-pk, lag) to a coupling weight vs speed."""
    rpms = np.arange(300, 4001, 50) if rpms is None else rpms
    m = PumpModel(condition)
    probes = [bal.Probe("NDE X", 15, 315), bal.Probe("NDE Y", 15, 45),
              bal.Probe("DE X", 103, 315), bal.Probe("DE Y", 103, 45)]
    out = []
    for n in rpms:
        s = bal.Setup(probes=probes, rpm=n, balance_radius_mm=radius_mm)
        out.append(bal.model_response_to_weight(m, s, grams, 0.0))
    return rpms, probes, np.array(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--html", help="directory for plotly html plots")
    args = ap.parse_args()

    m = PumpModel("dry")
    print(f"Rotor mass  ROSS {m.rotor.m:8.2f} kg   report {dt.REF_TOTAL_MASS_KG} kg")
    print(f"Rotor CG    ROSS {m.rotor.CG * 1e3:8.1f} mm   report 1971.5 mm")
    print(f"Bearing span ROSS {(m.z(103) - m.z(15)) * 1e3:7.1f} mm   report 2997.3 mm\n")

    cs = dry_criticals()
    fw = cs[1::2][:3] if len(cs) >= 6 else cs[:3]
    print("Dry critical speeds (rigid supports, forward synchronous):")
    for i, (a, b) in enumerate(zip(fw, dt.REF_DRY_CRITICALS_RPM), 1):
        print(f"  mode {i}: ROSS {a:7.0f} rpm   report {b:7.0f} rpm   ({(a / b - 1) * 100:+.1f} %)")

    for c in ("process_1x", "process_2x", "water_1x"):
        print(f"\nDamped modes at 2980 rpm - {c}  (report: {dt.REF_DAMPED_2980[c]})")
        for f, z, w in damped_modes(c):
            print(f"  {f:7.0f} cpm  zeta {z:5.3f}  {w}")

    rpms, probes, R = coupling_sensitivity()
    print("\nResponse to 100 g @ r=100 mm on the coupling (process_1x), um pk-pk @ phase lag:")
    print("   rpm " + "".join(f"{p.name:>16}" for p in probes))
    for n, r in zip(rpms, R):
        if n % 500 == 0 or n == 2950 or n == 3000:
            a, ph = bal.to_polar(r)
            print(f"{n:6.0f} " + "".join(f"{x:8.2f} @ {y:4.0f}" for x, y in zip(a, ph)))

    if args.html:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        out = Path(args.html)
        out.mkdir(parents=True, exist_ok=True)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                            subplot_titles=("Amplitude [um pk-pk]", "Phase lag [deg]"))
        for i, p in enumerate(probes):
            a, ph = bal.to_polar(R[:, i])
            fig.add_trace(go.Scatter(x=rpms, y=a, name=p.name, legendgroup=p.name), 1, 1)
            fig.add_trace(go.Scatter(x=rpms, y=ph, name=p.name, legendgroup=p.name,
                                     showlegend=False), 2, 1)
        fig.add_vline(x=dt.RATED_RPM, line_dash="dash")
        fig.update_layout(title="P-2616F: Bode for 100 g @ 100 mm on coupling (process 1x)")
        fig.update_xaxes(title_text="Speed [rpm]", row=2, col=1)
        fig.write_html(out / "coupling_bode.html")

        pm = PumpModel("process_1x")
        pm.rotor.plot_rotor().write_html(out / "rotor_model.html")
        print(f"\nPlots written to {out}/")


if __name__ == "__main__":
    main()
