import warnings

import numpy as np
import pytest
import ross as rs

from p2616f import balancing as bal
from p2616f import data_tables as dt
from p2616f.model import PumpModel, build_disks, build_shaft

warnings.filterwarnings("ignore")


@pytest.fixture(scope="module")
def process_1x():
    return PumpModel("process_1x")


def test_mass_and_geometry():
    m = PumpModel("dry")
    assert m.rotor.m == pytest.approx(dt.REF_TOTAL_MASS_KG, rel=1e-3)
    assert (m.z(dt.DE_BEARING_STN) - m.z(dt.NDE_BEARING_STN)) * 1e3 == pytest.approx(2997.3, abs=0.1)
    assert m.node_z[-1] * 1e3 == pytest.approx(3616.046, abs=0.01)


def test_damped_modes_match_report(process_1x):
    md = process_1x.rotor.run_modal(speed=2980 * np.pi / 30, num_modes=24)
    wd = md.wd * 30 / np.pi
    zeta = md.log_dec / np.sqrt(4 * np.pi**2 + md.log_dec**2)
    ref = dt.REF_DAMPED_2980["process_1x"]
    for f_ref, z_ref in ((ref["1st FW cpm"], ref["zeta 1st"]),
                         (ref["2nd FW cpm"], ref["zeta 2nd"]),
                         (ref["3rd FW cpm"], ref["zeta 3rd"])):
        i = np.argmin(np.abs(wd - f_ref) + 1e4 * np.abs(zeta - z_ref))
        assert wd[i] == pytest.approx(f_ref, rel=0.05)
        assert zeta[i] == pytest.approx(z_ref, abs=0.03)


def _isotropic_model():
    """Pump geometry on soft isotropic undamped bearings (no cross coupling)."""
    m = PumpModel("dry")
    shaft, sn, _ = build_shaft()
    b = [rs.BearingElement(n=sn[s], kxx=1e7, cxx=0.0) for s in (15, 103)]
    m.rotor = rs.Rotor(shaft, build_disks(sn), b)
    return m


@pytest.mark.parametrize("kp, probe, beta", [(0, 0, 0), (0, 90, 0), (0, 0, 30),
                                             (45, 315, 200), (270, 45, 10)])
def test_phase_lag_convention(kp, probe, beta):
    # Far below the first critical the high spot follows the heavy spot, so
    # lag = (probe angle - keyphasor angle) + weight angle (against rotation).
    m = _isotropic_model()
    s = bal.Setup(probes=[bal.Probe("p", 111, probe)], keyphasor_angle_deg=kp, rpm=60.0)
    amp, lag = bal.to_polar(bal.model_response_to_weight(m, s, 100.0, beta))
    expected = np.mod(probe - kp + beta, 360)
    d = np.mod(lag[0] - expected + 180, 360) - 180
    assert abs(d) < 2.0


def _setup():
    return bal.Setup(
        probes=[bal.Probe("NDE X", 15, 315), bal.Probe("NDE Y", 15, 45),
                bal.Probe("DE X", 103, 315), bal.Probe("DE Y", 103, 45)],
        keyphasor_angle_deg=20.0, balance_radius_mm=120.0)


@pytest.mark.parametrize("with_rotation", [False, True])
def test_one_shot_recovers_coupling_unbalance(process_1x, with_rotation):
    s = _setup()
    s.weight_angle_with_rotation = with_rotation
    v0 = bal.model_response_to_weight(process_1x, s, 150.0, 70.0)
    H = bal.model_influence_coefficients(process_1x, s)
    grams, ang, resid = bal.solve_correction(H, v0)
    assert grams == pytest.approx(150.0, rel=1e-6)
    assert np.mod(bal.weight_from_lag_frame(ang, s) - 250.0 + 180, 360) - 180 == pytest.approx(0, abs=1e-6)
    assert np.linalg.norm(resid) < 1e-6 * np.linalg.norm(v0)


def test_measured_ic_equals_model_ic(process_1x):
    s = _setup()
    v0 = bal.model_response_to_weight(process_1x, s, 80.0, 300.0)
    v1 = v0 + bal.model_response_to_weight(process_1x, s, 40.0, 135.0)
    Hm = bal.measured_influence_coefficients(v0, v1, 40.0, 135.0, s)
    np.testing.assert_allclose(Hm, bal.model_influence_coefficients(process_1x, s), rtol=1e-9)
