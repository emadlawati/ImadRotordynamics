"""Input data for the P-2616F HP injection water pump rotor.

Source: Baker Hughes / Nuovo Pignone lateral analysis report SOA700000035 rev. 0
(job 2200377), pump 10x16 MSND / 7 stages, coupling Rexnord 8GBH-220-D.

Station numbers are the DyRoBeS stations of the report (1 = NDE end with the
screw pump, 113 = coupling end).  Units are those of the report (mm, kg, N/mm,
N.s/mm); conversion to SI is done in ``model.py``.
"""

from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
SHAFT_CSV = DATA_DIR / "shaft_elements.csv"

RATED_RPM = 2980.0

# Tab. 1 - material
MATERIAL = dict(rho=7833.4, E=1.9995e11, G_s=7.6904e10)

# Tab. 1 - rigid body summary used to check the model
REF_TOTAL_MASS_KG = 605.78
REF_SHAFT_MASS_KG = 342.0
REF_DRY_CRITICALS_RPM = (955.0, 3807.0, 7612.0)

# Bearing stations (zero static deflection in Tab. 4; Tab. 5 & 6 titles)
NDE_BEARING_STN = 15
DE_BEARING_STN = 103
COUPLING_STN = 111

# Tab. 3 - added masses: station -> (mass kg, Id kg.m2, Ip kg.m2, tag)
DISKS = [
    (23, 2.6532, 0.65279e-02, 0.93130e-02, "Shaft sleeve"),
    (62, 5.7826, 0.23402e-01, 0.27913e-01, "Intermediate sleeve"),
    (7, 4.8036, 0.10218e-01, 0.19632e-01, "Collar"),
    (44, 30.240, 0.27000, 0.48000, "Series impeller"),
    (52, 30.240, 0.27000, 0.48000, "Series impeller"),
    (60, 30.240, 0.27000, 0.48000, "Series impeller"),
    (64, 30.240, 0.27000, 0.48000, "Series impeller"),
    (72, 30.240, 0.27000, 0.48000, "Series impeller"),
    (81, 30.240, 0.27000, 0.48000, "Series impeller"),
    (29, 52.630, 0.54000, 0.87000, "1st stage impeller"),
    (111, 53.000, 0.28000, 0.56000, "Coupling"),
    (39, 1.5798, 0.11455e-01, 0.22704e-01, "Series front wear ring"),
    (47, 1.5798, 0.11455e-01, 0.22704e-01, "Series front wear ring"),
    (56, 1.5798, 0.11455e-01, 0.22704e-01, "Series front wear ring"),
    (67, 1.5798, 0.11455e-01, 0.22704e-01, "Series front wear ring"),
    (77, 1.5798, 0.11455e-01, 0.22704e-01, "Series front wear ring"),
    (86, 1.5798, 0.11455e-01, 0.22704e-01, "Series front wear ring"),
    (45, 0.73077, 0.26984e-02, 0.53012e-02, "Series rear wear ring"),
    (53, 0.73077, 0.26984e-02, 0.53012e-02, "Series rear wear ring"),
    (71, 0.73077, 0.26984e-02, 0.53012e-02, "Series rear wear ring"),
    (80, 0.73077, 0.26984e-02, 0.53012e-02, "Series rear wear ring"),
    (27, 2.0558, 0.18888e-01, 0.37426e-01, "1st stage wear ring"),
    (31, 2.0558, 0.18888e-01, 0.37426e-01, "1st stage wear ring"),
    (34, 4.7857, 0.14466e-01, 0.20055e-01, "1st/2nd sleeve"),
    (1, 1.5000, 0.0, 0.0, "Screw pump"),
    (26, 1.9843, 0.51510e-02, 0.73173e-02, "Shaft sleeve"),
    (94, 5.3164, 0.15074e-01, 0.21288e-01, "Balance sleeve"),
]

# Tab. 5 / Tab. 6 - sleeve bearings (ISO VG46, D=107.95 mm, L=104 mm, Cr=0.085 mm)
# columns: rpm, Kxx, Kxy, Kyx, Kyy [N/mm], Cxx, Cxy, Cyx, Cyy [N.s/mm]
# DyRoBeS axes: y vertical (gravity along -y), rotation from +x to +y.
_DE_BEARING = """
250 4.80E+04 1.64E+04 -1.47E+05 1.17E+05 1.89E+03 -2.38E+03 -2.38E+03 1.19E+04
500 4.24E+04 2.00E+04 -1.64E+05 9.66E+04 9.65E+02 -9.32E+02 -9.32E+02 6.45E+03
750 3.95E+04 2.37E+04 -1.88E+05 8.90E+04 7.01E+02 -5.47E+02 -5.47E+02 4.88E+03
1000 3.79E+04 2.78E+04 -2.16E+05 8.51E+04 5.89E+02 -3.83E+02 -3.83E+02 4.18E+03
1250 3.70E+04 3.22E+04 -2.47E+05 8.27E+04 5.30E+02 -2.94E+02 -2.94E+02 3.81E+03
1500 3.64E+04 3.68E+04 -2.79E+05 8.13E+04 4.95E+02 -2.39E+02 -2.39E+02 3.58E+03
1750 3.60E+04 4.15E+04 -3.13E+05 8.03E+04 4.73E+02 -2.01E+02 -2.01E+02 3.44E+03
2000 3.57E+04 4.63E+04 -3.48E+05 7.96E+04 4.58E+02 -1.74E+02 -1.74E+02 3.34E+03
2250 3.55E+04 5.12E+04 -3.83E+05 7.91E+04 4.47E+02 -1.53E+02 -1.53E+02 3.27E+03
2500 3.54E+04 5.62E+04 -4.20E+05 7.87E+04 4.39E+02 -1.37E+02 -1.37E+02 3.21E+03
2750 3.52E+04 6.12E+04 -4.56E+05 7.84E+04 4.33E+02 -1.24E+02 -1.24E+02 3.18E+03
3000 3.52E+04 6.62E+04 -4.93E+05 7.82E+04 4.29E+02 -1.13E+02 -1.13E+02 3.14E+03
3250 3.51E+04 7.13E+04 -5.30E+05 7.80E+04 4.25E+02 -1.04E+02 -1.04E+02 3.12E+03
3500 3.50E+04 7.64E+04 -5.68E+05 7.79E+04 4.22E+02 -9.61E+01 -9.61E+01 3.10E+03
3750 3.50E+04 8.15E+04 -6.05E+05 7.78E+04 4.20E+02 -8.95E+01 -8.95E+01 3.09E+03
4000 3.49E+04 8.66E+04 -6.43E+05 7.77E+04 4.18E+02 -8.37E+01 -8.37E+01 3.07E+03
4500 3.49E+04 9.70E+04 -7.19E+05 7.75E+04 4.15E+02 -7.42E+01 -7.42E+01 3.05E+03
5000 3.48E+04 1.07E+05 -7.95E+05 7.74E+04 4.13E+02 -6.66E+01 -6.66E+01 3.04E+03
6000 3.47E+04 1.28E+05 -9.48E+05 7.73E+04 4.10E+02 -5.54E+01 -5.54E+01 3.02E+03
7000 3.47E+04 1.49E+05 -1.10E+06 7.72E+04 4.08E+02 -4.74E+01 -4.74E+01 3.01E+03
8000 3.47E+04 1.70E+05 -1.26E+06 7.71E+04 4.07E+02 -4.14E+01 -4.14E+01 3.00E+03
9000 3.46E+04 1.91E+05 -1.41E+06 7.71E+04 4.06E+02 -3.67E+01 -3.67E+01 3.00E+03
10000 3.46E+04 2.12E+05 -1.57E+06 7.71E+04 4.06E+02 -3.30E+01 -3.30E+01 2.99E+03
"""

_NDE_BEARING = """
250 3.77E+04 1.40E+04 -1.22E+05 8.99E+04 1.53E+03 -1.79E+03 -1.79E+03 9.78E+03
500 3.33E+04 1.76E+04 -1.42E+05 7.55E+04 8.14E+02 -7.11E+02 -7.11E+02 5.56E+03
750 3.13E+04 2.16E+04 -1.69E+05 7.03E+04 6.17E+02 -4.25E+02 -4.25E+02 4.36E+03
1000 3.03E+04 2.59E+04 -1.99E+05 6.77E+04 5.35E+02 -3.01E+02 -3.01E+02 3.84E+03
1250 2.97E+04 3.05E+04 -2.31E+05 6.62E+04 4.92E+02 -2.33E+02 -2.33E+02 3.56E+03
1500 2.93E+04 3.52E+04 -2.66E+05 6.53E+04 4.67E+02 -1.90E+02 -1.90E+02 3.40E+03
1750 2.91E+04 4.01E+04 -3.01E+05 6.47E+04 4.51E+02 -1.61E+02 -1.61E+02 3.29E+03
2000 2.89E+04 4.50E+04 -3.37E+05 6.43E+04 4.41E+02 -1.40E+02 -1.40E+02 3.22E+03
2250 2.88E+04 5.00E+04 -3.73E+05 6.40E+04 4.33E+02 -1.23E+02 -1.23E+02 3.17E+03
2500 2.87E+04 5.51E+04 -4.10E+05 6.38E+04 4.28E+02 -1.10E+02 -1.10E+02 3.14E+03
2750 2.86E+04 6.02E+04 -4.47E+05 6.36E+04 4.24E+02 -1.00E+02 -1.00E+02 3.11E+03
3000 2.86E+04 6.53E+04 -4.85E+05 6.35E+04 4.20E+02 -9.14E+01 -9.14E+01 3.09E+03
3250 2.85E+04 7.04E+04 -5.22E+05 6.34E+04 4.18E+02 -8.41E+01 -8.41E+01 3.07E+03
3500 2.85E+04 7.56E+04 -5.60E+05 6.33E+04 4.16E+02 -7.80E+01 -7.80E+01 3.06E+03
3750 2.84E+04 8.07E+04 -5.98E+05 6.33E+04 4.14E+02 -7.27E+01 -7.27E+01 3.05E+03
4000 2.84E+04 8.59E+04 -6.36E+05 6.32E+04 4.13E+02 -6.80E+01 -6.80E+01 3.04E+03
4500 2.84E+04 9.63E+04 -7.13E+05 6.31E+04 4.11E+02 -6.03E+01 -6.03E+01 3.03E+03
5000 2.83E+04 1.07E+05 -7.90E+05 6.31E+04 4.10E+02 -5.42E+01 -5.42E+01 3.02E+03
6000 2.83E+04 1.28E+05 -9.44E+05 6.30E+04 4.08E+02 -4.51E+01 -4.51E+01 3.01E+03
7000 2.83E+04 1.49E+05 -1.10E+06 6.29E+04 4.06E+02 -3.86E+01 -3.86E+01 3.00E+03
8000 2.82E+04 1.70E+05 -1.25E+06 6.29E+04 4.06E+02 -3.37E+01 -3.37E+01 2.99E+03
9000 2.82E+04 1.91E+05 -1.41E+06 6.29E+04 4.05E+02 -2.99E+01 -2.99E+01 2.99E+03
10000 2.82E+04 2.12E+05 -1.56E+06 6.29E+04 4.05E+02 -2.69E+01 -2.69E+01 2.99E+03
"""


def _parse(block):
    return [tuple(float(v) for v in line.split()) for line in block.strip().splitlines()]


DE_BEARING = _parse(_DE_BEARING)
NDE_BEARING = _parse(_NDE_BEARING)

# Tab. 7 / 8 / 9 - annular seals at 2980 rpm (skew-symmetric coefficients)
# name -> (stations, K, k, C, c, M)   K,k [N/mm]  C,c [N.s/mm]  M [kg]
# Kxx=Kyy=K, Kxy=-Kyx=k, Cxx=Cyy=C, Cxy=-Cyx=c, Mxx=Myy=M
SEAL_STATIONS = {
    "intermediate_sleeve": (62,),
    "stage1_2_sleeve": (34,),
    "balance_sleeve": (94,),
    "front_ring_series": (39, 47, 56, 67, 77, 86),
    "front_ring_1st_stage": (27, 31),
    "back_ring_series": (45, 53, 71, 80),
    "shaft_sleeve": (23,),
}

SEALS = {
    # Tab. 7 - process fluid, 1x new clearances
    "process_1x": {
        "intermediate_sleeve": (13221.9, 92688.3, 594.032, 84.8595, 271.929),
        "stage1_2_sleeve": (4042.47, 28177.4, 180.587, 32.6459, 104.612),
        "balance_sleeve": (30784.8, 56181.5, 360.063, 31.6182, 101.319),
        "front_ring_series": (11941.8, 4357.17, 21.2651, 3.04102, 7.38361),
        "front_ring_1st_stage": (14717.0, 5888.42, 29.7566, 4.66521, 11.7534),
        "back_ring_series": (2213.43, 1479.49, 8.04470, 1.94723, 5.30656),
        "shaft_sleeve": (-771.745, 1709.12, 10.9536, 10.0886, 32.3285),
    },
    # Tab. 8 - process fluid, 2x new clearances (worn)
    "process_2x": {
        "intermediate_sleeve": (17403.7, 35548.7, 227.829, 42.1032, 134.918),
        "stage1_2_sleeve": (5358.56, 11457.9, 73.4330, 15.9953, 51.2562),
        "balance_sleeve": (29219.5, 23479.0, 150.475, 15.3751, 49.2689),
        "front_ring_series": (5344.79, 2914.15, 12.7541, 2.19927, 4.77248),
        "front_ring_1st_stage": (7181.50, 4073.70, 18.1242, 3.50533, 7.72729),
        "back_ring_series": (923.986, 498.280, 2.42123, 0.511147, 1.23400),
        "shaft_sleeve": (-364.562, 518.538, 3.32327, 5.02668, 16.1078),
    },
    # Tab. 9 - water, 1x new clearances
    "water_1x": {
        "intermediate_sleeve": (13127.0, 74426.6, 476.995, 71.3336, 228.586),
        "stage1_2_sleeve": (4059.00, 22743.9, 145.764, 27.4322, 87.9055),
        "balance_sleeve": (28845.5, 45623.3, 292.396, 26.5594, 85.1087),
        "front_ring_series": (10197.7, 3835.13, 18.3582, 2.71791, 6.46261),
        "front_ring_1st_stage": (12701.0, 5194.36, 25.6794, 4.19056, 10.3065),
        "back_ring_series": (1930.10, 1297.98, 6.88988, 1.75911, 4.66655),
        "shaft_sleeve": (-640.201, 1349.43, 8.64842, 8.48289, 27.1831),
    },
}

# Damped results from the report at 2980 rpm (Fig. 7-14), read off the plots,
# used only for a qualitative comparison.
REF_DAMPED_2980 = {
    "process_1x": {"1st FW cpm": 1650, "2nd FW cpm": 2450, "3rd FW cpm": 4000,
                   "zeta 1st": 0.54, "zeta 2nd": 0.76, "zeta 3rd": 0.71},
    "process_2x": {"1st FW cpm": 2420, "2nd FW cpm": 4250, "3rd FW cpm": 7150,
                   "zeta 1st": 0.54, "zeta 2nd": 0.43, "zeta 3rd": 0.29},
    "water_1x": {"1st FW cpm": 1720, "2nd FW cpm": 3250, "3rd FW cpm": 4870,
                 "zeta 1st": 0.56, "zeta 2nd": 0.67, "zeta 3rd": 0.69},
}
