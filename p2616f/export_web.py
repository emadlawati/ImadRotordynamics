"""Precompute unit-unbalance responses and build the interactive HTML page.

    python -m p2616f.export_web [--out web/p2616f_balancer.html]

The page works by superposition: for every station it holds the complex
response to 1 kg.m of unbalance (ROSS phase 0) at
  * both bearings (x, y) over a speed grid  -> probe readings and Bode plots
  * every station (x, y) at rated speed     -> deflected shape along the shaft
"""

import argparse
import json
import warnings
from pathlib import Path

import numpy as np

from . import data_tables as dt
from .model import PumpModel, read_shaft_table, rpm2rads

warnings.filterwarnings("ignore")

CONDITIONS = ("process_1x", "process_2x", "water_1x")
SPEEDS = sorted(set(list(range(300, 4001, 100)) + [int(dt.RATED_RPM)]))
TEMPLATE = Path(__file__).parent / "web_template.html"


def _round(a, sig=5):
    return [float(f"{v:.{sig}g}") for v in np.ravel(a)]


def unit_responses(model, rpm):
    """Complex response matrix (ndof x n_stations) for 1 kg.m at each station."""
    w = float(rpm2rads(rpm))
    r = model.rotor
    stations = sorted(model.station_nodes)
    F = np.zeros((r.ndof, len(stations)), dtype=complex)
    for j, s in enumerate(stations):
        F[:, j] = r._unbalance_force(model.node(s), 1.0, 0.0, np.array([w]))[:, 0]
    Z = r.K(w, w) - w**2 * r.M(w, w) + 1j * w * (r.C(w, w) + w * r.G())
    return np.linalg.solve(Z, F)


def pack(z):
    """complex array -> flat [re, im, re, im, ...]"""
    z = np.asarray(z).ravel()
    return _round(np.column_stack([z.real, z.imag]))


def build_data():
    rows = read_shaft_table()
    m0 = PumpModel("process_1x")
    stations = sorted(m0.station_nodes)
    z_st = [round(float(m0.z(s) * 1e3), 2) for s in stations]
    segs = []
    for r in rows:
        if r["sub"] < 0:
            dl, dr = r["mass_od_mm"], r["stiff_od_mm"]
        else:
            dl = dr = r["stiff_od_mm"]
        segs.append([round(r["left_loc_mm"], 3), round(r["length_mm"], 4), dl, dr])
    disks = []
    for stn, m, Id, Ip, tag in dt.DISKS:
        dia = 2e3 * np.sqrt(2 * Ip / m) if Ip > 0 else 60.0
        disks.append(dict(stn=stn, m=m, tag=tag, dia=round(float(dia), 1)))
    seals = [dict(stn=s, name=name) for name, ss in dt.SEAL_STATIONS.items() for s in ss]

    nde, de = m0.node(dt.NDE_BEARING_STN), m0.node(dt.DE_BEARING_STN)
    resp = {}
    for c in CONDITIONS:
        m = m0 if c == "process_1x" else PumpModel(c)
        brg = []  # [speed][station][NDEx, NDEy, DEx, DEy]
        shape = None
        for n in SPEEDS:
            Q = unit_responses(m, n)
            nd = m.rotor.number_dof
            idx = [nde * nd, nde * nd + 1, de * nd, de * nd + 1]
            brg.append(pack(Q[idx, :].T))
            if n == int(dt.RATED_RPM):
                rows_xy = []
                for s in stations:
                    k = m.node(s) * nd
                    rows_xy += [k, k + 1]
                shape = pack(Q[rows_xy, :].T)  # [unb station][resp station][x,y]
        resp[c] = dict(bearings=brg, shape=shape)
        print(f"  {c}: done")

    return dict(
        meta=dict(
            pump="P-2616F", type="NP 10x16 MSND, 7 stages", rpm=dt.RATED_RPM,
            source="Baker Hughes lateral analysis SOA700000035 rev.0",
            mass=round(float(m0.rotor.m), 2),
        ),
        stations=stations, z=z_st, segs=segs, disks=disks, seals=seals,
        bearings=dict(NDE=dt.NDE_BEARING_STN, DE=dt.DE_BEARING_STN),
        coupling=dt.COUPLING_STN, speeds=SPEEDS, conditions=list(CONDITIONS),
        resp=resp,
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="web/p2616f_balancer.html")
    args = ap.parse_args()
    data = build_data()
    html = TEMPLATE.read_text().replace("/*__DATA__*/null", json.dumps(data, separators=(",", ":")))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
