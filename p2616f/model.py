"""ROSS model of the P-2616F pump rotor (10x16 MSND, 7 stages).

Every DyRoBeS sub-element of Tab. 2 becomes one ROSS ``ShaftElement``, so the
ROSS model has more nodes than the report has stations.  ``station_nodes``
maps a report station number to its ROSS node index, so everything outside
this module talks in report station numbers.

Coordinate system (same as DyRoBeS / ROSS):
    z  along the shaft, from the NDE end (station 1) towards the coupling,
    y  vertical up (gravity along -y),
    x  horizontal,
    rotation from +x towards +y (the cross-coupled bearing coefficients of
    the report are written for this direction).
"""

import csv
import warnings

import numpy as np
import ross as rs

from . import data_tables as dt

CONDITIONS = ("dry", "process_1x", "process_2x", "water_1x")

_RPM_TO_RADS = np.pi / 30.0


def rpm2rads(rpm):
    return np.asarray(rpm, dtype=float) * _RPM_TO_RADS


def material():
    E = dt.MATERIAL["E"]
    G = dt.MATERIAL["G_s"]
    return rs.Material(name="P2616F_shaft", rho=dt.MATERIAL["rho"], E=E, G_s=G)


def read_shaft_table():
    rows = []
    with open(dt.SHAFT_CSV) as f:
        lines = [line for line in f if not line.startswith("#")]
    for r in csv.DictReader(lines):
        rows.append({k: float(v) if k not in ("element", "sub") else int(v)
                     for k, v in r.items()})
    return rows


def build_shaft(mat=None):
    """Return (shaft_elements, station_nodes, node_z_m)."""
    mat = mat or material()
    rows = read_shaft_table()
    elements = []
    station_nodes = {}
    z = [0.0]
    for i, r in enumerate(rows):
        station_nodes.setdefault(r["element"], i)
        L = r["length_mm"] / 1e3
        if r["sub"] < 0:  # conical: mass cols = left end, stiffness cols = right end
            idl, odl = r["mass_id_mm"] / 1e3, r["mass_od_mm"] / 1e3
            idr, odr = r["stiff_id_mm"] / 1e3, r["stiff_od_mm"] / 1e3
        else:
            idl = idr = r["stiff_id_mm"] / 1e3
            odl = odr = r["stiff_od_mm"] / 1e3
        elements.append(
            rs.ShaftElement(L=L, idl=idl, odl=odl, idr=idr, odr=odr,
                            material=mat, n=i, shear_effects=True,
                            rotary_inertia=True, gyroscopic=True)
        )
        z.append(z[-1] + L)
    station_nodes[max(station_nodes) + 1] = len(rows)  # last station (113)
    return elements, station_nodes, np.array(z)


def build_disks(station_nodes):
    return [
        rs.DiskElement(n=station_nodes[stn], m=m, Id=Id, Ip=Ip,
                       tag=f"{tag} (stn {stn})")
        for stn, m, Id, Ip, tag in dt.DISKS
    ]


def _bearing(table, node, tag, n_link=None):
    a = np.array(table)
    rpm = a[:, 0]
    k = a[:, 1:5] * 1e3   # N/mm -> N/m
    c = a[:, 5:9] * 1e3   # N.s/mm -> N.s/m
    return rs.BearingElement(
        n=node, n_link=n_link, tag=tag, frequency=rpm2rads(rpm),
        kxx=k[:, 0], kxy=k[:, 1], kyx=k[:, 2], kyy=k[:, 3],
        cxx=c[:, 0], cxy=c[:, 1], cyx=c[:, 2], cyy=c[:, 3],
    )


def build_bearings(station_nodes, pedestal=None, n_shaft_nodes=None):
    """Journal bearings, optionally on a flexible pedestal.

    pedestal: None (rigid ground, default) or dict with keys ``m`` [kg],
    ``kxx``, ``kyy`` [N/m], ``cxx``, ``cyy`` [N.s/m] (same for both bearings),
    or {"DE": {...}, "NDE": {...}}.
    """
    nde, de = station_nodes[dt.NDE_BEARING_STN], station_nodes[dt.DE_BEARING_STN]
    if pedestal is None:
        return [_bearing(dt.NDE_BEARING, nde, "NDE bearing"),
                _bearing(dt.DE_BEARING, de, "DE bearing")], []

    if "DE" not in pedestal:
        pedestal = {"DE": pedestal, "NDE": pedestal}
    out, pms = [], []
    for name, table, node, ped_node in (
        ("NDE", dt.NDE_BEARING, nde, n_shaft_nodes + 1),
        ("DE", dt.DE_BEARING, de, n_shaft_nodes + 2),
    ):
        p = pedestal[name]
        out.append(_bearing(table, node, f"{name} bearing", n_link=ped_node))
        out.append(rs.BearingElement(
            n=ped_node, tag=f"{name} pedestal",
            kxx=p["kxx"], kyy=p["kyy"], cxx=p.get("cxx", 0.0), cyy=p.get("cyy", 0.0)))
        pms.append(rs.PointMass(n=ped_node, m=p["m"], tag=f"{name} pedestal mass"))
    return out, pms


def build_seals(station_nodes, condition, speed_scaling=True):
    """Annular seal elements (Childs) from Tab. 7/8/9.

    The report gives seal coefficients at 2980 rpm only.  With
    ``speed_scaling`` the pressure-driven terms are scaled with pump head
    (K, k ~ N^2; C, c ~ N; M constant) so that Campbell diagrams make sense.
    At 2980 rpm the coefficients are exactly the report values.
    """
    if condition == "dry":
        return []
    rpm = np.array([250, 500, 750, 1000, 1500, 2000, 2500, 2980, 3500, 4000,
                    5000, 6000, 8000, 10000], dtype=float)
    r = rpm / dt.RATED_RPM if speed_scaling else np.ones_like(rpm)
    seals = []
    for name, (K, k, C, c, M) in dt.SEALS[condition].items():
        for stn in dt.SEAL_STATIONS[name]:
            seals.append(rs.SealElement(
                n=station_nodes[stn], tag=f"{name} (stn {stn})",
                frequency=rpm2rads(rpm),
                kxx=K * 1e3 * r**2, kyy=K * 1e3 * r**2,
                kxy=k * 1e3 * r**2, kyx=-k * 1e3 * r**2,
                cxx=C * 1e3 * r, cyy=C * 1e3 * r,
                cxy=c * 1e3 * r, cyx=-c * 1e3 * r,
                mxx=M, myy=M,
            ))
    return seals


class PumpModel:
    """Container for the ROSS rotor plus the station <-> node bookkeeping."""

    def __init__(self, condition="process_1x", pedestal=None, seal_speed_scaling=True):
        if condition not in CONDITIONS:
            raise ValueError(f"condition must be one of {CONDITIONS}")
        self.condition = condition
        mat = material()
        shaft, self.station_nodes, self.node_z = build_shaft(mat)
        disks = build_disks(self.station_nodes)
        bearings, pms = build_bearings(self.station_nodes, pedestal,
                                       n_shaft_nodes=len(shaft))
        seals = build_seals(self.station_nodes, condition, seal_speed_scaling)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.rotor = rs.Rotor(shaft, disks, bearings + seals,
                                  point_mass_elements=pms or None,
                                  tag=f"P-2616F {condition}")
        self.has_pedestal = pedestal is not None
        self.pedestal_nodes = {"NDE": len(shaft) + 1, "DE": len(shaft) + 2} if pms else {}

    def node(self, station):
        return self.station_nodes[station]

    def z(self, station):
        return self.node_z[self.node(station)]

    def dof(self, node, direction):
        """Global dof index of x (0) or y (1) at ``node``."""
        for pm in self.rotor.point_mass_elements:
            if pm.n == node:  # pedestal nodes: 3 dofs each, after the shaft
                return pm.dof_global_index[f"{'xy'[direction]}_{node}"]
        return node * self.rotor.number_dof + direction

    # ------------------------------------------------------------------
    def harmonic_response(self, rpm, forces):
        """Steady synchronous response at ``rpm``.

        forces: list of (station, me_kgm, phase_rad) unbalances; phase is the
        angular position of the unbalance at t=0 measured from +x in the
        direction of rotation.
        Returns the complex response vector q (x(t) = Re(q exp(j w t))).
        """
        w = float(rpm2rads(rpm))
        F = np.zeros(self.rotor.ndof, dtype=complex)
        for stn, me, ph in forces:
            F += self.rotor._unbalance_force(self.node(stn), me, ph, np.array([w]))[:, 0]
        Z = (self.rotor.K(w, w) - w**2 * self.rotor.M(w, w)
             + 1j * w * (self.rotor.C(w, w) + w * self.rotor.G()))
        return np.linalg.solve(Z, F)
