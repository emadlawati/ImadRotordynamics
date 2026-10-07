"""Single-plane (coupling) influence coefficients and one-shot balancing.

Angle and phase conventions
---------------------------
All physical angles are given the way they are read on site:

* probe / keyphasor location ``angle_deg``: measured from top dead centre
  (vertical up) **in the direction of rotation**.  Example with API 670
  probes (X 45 deg left, Y 45 deg right of TDC, viewed from the driver):
  CW rotation viewed from driver -> X = 315, Y = 45;
  CCW rotation viewed from driver -> X = 45,  Y = 315.
* vibration phase: **phase lag** (degrees from the keyphasor pulse to the
  next positive peak), the usual convention of Bently/ADRE/System 1 and of
  most portable analysers.
* weight angle: measured from the keyphasor notch (with the notch lined up
  under the keyphasor probe) **against rotation**.  This is the convention
  that pairs with phase lag: moving a weight by +d deg against rotation
  increases every phase lag by d deg, so responses are linear in the
  complex weight w*exp(j*angle).

If your weight angles are measured *with* rotation, set
``weight_angle_with_rotation = true`` and they are converted.

Internally the model works in ROSS axes (y up, rotation from +x to +y), so
a physical angle psi maps to the model angle 90 deg + psi.
"""

from dataclasses import dataclass, field

import numpy as np

from .data_tables import DE_BEARING_STN
from .model import PumpModel, rpm2rads


@dataclass
class Probe:
    name: str
    station: int
    angle_deg: float
    location: str = "shaft"  # "shaft" (proximity probe) or "pedestal"


@dataclass
class Setup:
    probes: list
    keyphasor_angle_deg: float = 0.0
    rpm: float = 2980.0
    balance_station: int = 111          # coupling
    balance_radius_mm: float = 100.0
    measurement: str = "displacement"   # "displacement" | "velocity"
    amplitude_unit: str = "um_pp"       # um_pp, um_pk, mm_s_pk, mm_s_rms
    weight_angle_with_rotation: bool = False
    extra: dict = field(default_factory=dict)


# ---------------------------------------------------------------- helpers
def polar(amp, phase_deg):
    return amp * np.exp(1j * np.deg2rad(phase_deg))


def to_polar(z):
    z = np.asarray(z)
    return np.abs(z), np.mod(np.rad2deg(np.angle(z)), 360.0)


def _unit_scale(setup):
    """Factor from 0-pk metres (or m/s) to the requested amplitude unit."""
    return {
        "um_pp": 2e6, "um_pk": 1e6,
        "mm_s_pk": 1e3, "mm_s_rms": 1e3 / np.sqrt(2),
    }[setup.amplitude_unit]


def weight_to_lag_frame(angle_deg, setup):
    """User weight angle -> 'against rotation' angle used internally."""
    return np.mod(-angle_deg, 360.0) if setup.weight_angle_with_rotation else angle_deg


def weight_from_lag_frame(angle_deg, setup):
    return np.mod(-angle_deg, 360.0) if setup.weight_angle_with_rotation else angle_deg


# ---------------------------------------------------------------- model IC
def probe_readings(model: PumpModel, q, setup: Setup):
    """Complex 'lag-convention' readings (amp * exp(j*lag)) for every probe."""
    w = float(rpm2rads(setup.rpm))
    out = []
    for p in setup.probes:
        if p.location == "pedestal":
            side = "DE" if p.station == DE_BEARING_STN else "NDE"
            node = model.pedestal_nodes[side]
        else:
            node = model.node(p.station)
        a = np.deg2rad(90.0 + p.angle_deg)
        P = q[model.dof(node, 0)] * np.cos(a) + q[model.dof(node, 1)] * np.sin(a)
        if setup.measurement == "velocity":
            P = 1j * w * P
        # p(t) = Re(P e^{jwt}); lag = -angle(P)  ->  lag-complex = conj(P)
        out.append(np.conj(P) * _unit_scale(setup))
    return np.array(out)


def model_response_to_weight(model, setup, grams, angle_deg, station=None,
                             radius_mm=None):
    """Probe readings caused by one weight (user angle convention)."""
    station = station or setup.balance_station
    radius_mm = radius_mm or setup.balance_radius_mm
    me = grams * 1e-3 * radius_mm * 1e-3
    beta = weight_to_lag_frame(angle_deg, setup)
    a_k = 90.0 + setup.keyphasor_angle_deg
    ross_phase = np.deg2rad(a_k - beta)  # notch at keyphasor at t=0
    q = model.harmonic_response(setup.rpm, [(station, me, ross_phase)])
    return probe_readings(model, q, setup)


def model_influence_coefficients(model, setup, station=None, radius_mm=None):
    """Response per gram at 0 deg (lag frame) -> complex IC per probe."""
    return model_response_to_weight(model, setup, 1.0, 0.0, station, radius_mm)


def measured_influence_coefficients(v0, v1, trial_grams, trial_angle_deg, setup):
    """IC from a site trial run: (V1 - V0) / W_trial."""
    W = polar(trial_grams, weight_to_lag_frame(trial_angle_deg, setup))
    return (np.asarray(v1) - np.asarray(v0)) / W


# ---------------------------------------------------------------- solve
def solve_correction(H, v0, weights=None):
    """Least-squares single-plane correction W minimising |V0 + H W|.

    Returns (grams, angle_deg in the internal lag/against-rotation frame,
    predicted residual vector).
    """
    H = np.asarray(H, dtype=complex)
    v0 = np.asarray(v0, dtype=complex)
    s = np.ones(len(H)) if weights is None else np.asarray(weights, float)
    Hw, vw = H * s, v0 * s
    W = -np.vdot(Hw, vw) / np.vdot(Hw, Hw)
    return abs(W), np.mod(np.rad2deg(np.angle(W)), 360.0), v0 + H * W


def correction_report(H, v0, setup, weights=None, label=""):
    grams, ang, resid = solve_correction(H, v0, weights)
    ang_user = weight_from_lag_frame(ang, setup)
    lines = [f"--- {label} ---" if label else ""]
    lines.append(
        f"Correction weight: {grams:8.1f} g @ {ang_user:6.1f} deg "
        f"(r = {setup.balance_radius_mm:.0f} mm, "
        f"{'with' if setup.weight_angle_with_rotation else 'against'} rotation from KP notch)"
    )
    lines.append(f"  = {grams * setup.balance_radius_mm:,.0f} g.mm")
    lines.append(f"{'probe':>10} {'before':>18} {'predicted after':>18}")
    a0, p0 = to_polar(v0)
    a1, p1 = to_polar(resid)
    for i, p in enumerate(setup.probes):
        lines.append(f"{p.name:>10} {a0[i]:8.1f} @ {p0[i]:5.0f}  {a1[i]:8.1f} @ {p1[i]:5.0f}")
    # per-probe single-sensor solutions (consistency check)
    lines.append("Single-probe solutions (consistency check):")
    for i, p in enumerate(setup.probes):
        if abs(H[i]) == 0:
            continue
        W = -v0[i] / H[i]
        lines.append(f"{p.name:>10}: {abs(W):8.1f} g @ "
                     f"{weight_from_lag_frame(np.mod(np.rad2deg(np.angle(W)), 360), setup):6.1f} deg")
    return grams, ang_user, resid, "\n".join(lines)


def plane_fit(model, setup, v0, stations):
    """Equivalent unbalance at each candidate station that best explains V0.

    Low relative residual means the measured 1X pattern is consistent with an
    unbalance at that station (single-plane diagnosis).
    """
    out = []
    for stn in stations:
        H = model_influence_coefficients(model, setup, station=stn)
        grams, ang, resid = solve_correction(H, v0)
        fit = np.linalg.norm(resid) / np.linalg.norm(v0)
        out.append((stn, grams * setup.balance_radius_mm, weight_from_lag_frame(np.mod(ang + 180, 360), setup), fit))
    return out


def suggest_trial_weight(H, v0, target_fraction=0.3, min_change=None):
    """Trial mass (g) that changes the largest reading by ``target_fraction``."""
    i = int(np.argmax(np.abs(v0)))
    target = max(target_fraction * abs(v0[i]), min_change or 0.0)
    return target / abs(H[i])
