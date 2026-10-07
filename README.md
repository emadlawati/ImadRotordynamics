# 🎈 Blank app template

A simple Streamlit app template for you to modify!

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://blank-app-template.streamlit.app/)

### How to run it on your own machine

1. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

2. Run the app

   ```
   $ streamlit run streamlit_app.py
   ```

---

## P-2616F pump: ROSS rotor model and coupling balancing

`p2616f/` is a [ROSS](https://github.com/petrobras/ross) model of the P-2616F HP injection
water pump (NP 10x16 MSND, 7 stages, 2980 rpm). It is built from the OEM lateral analysis report
SOA700000035 rev. 0 and includes:

* the shaft (Tab. 2), using all 123 DyRoBeS sub-elements. Conical sub-elements are kept as
  tapered ROSS elements.
* the 27 added masses/inertias (Tab. 3): impellers, sleeves, wear rings, screw pump and the coupling at station 111.
* the speed-dependent DE (stn 103) and NDE (stn 15) sleeve-bearing coefficients (Tab. 5/6), including cross-coupling.
* the annular seals (Tab. 7/8/9) for process 1x, process 2x and water 1x. Each seal has K, k, C, c and the added mass M.
  The report gives these at 2980 rpm only. For other speeds they are scaled with head
  (K ~ N^2, C ~ N, M constant).

### How the model compares with the report

Run `python -m p2616f.validate`:

| | ROSS | OEM report |
|---|---|---|
| Rotor mass | 605.78 kg | 605.78 kg |
| Dry critical 1 / 2 / 3 | 961 / 3775 / 7674 rpm | 955 / 3807 / 7612 rpm |
| Process 1x @2980: 1st / 2nd / 3rd FW | 1671 (ζ 0.54) / 2467 (0.76) / 3971 (0.72) cpm | ~1650 (0.54) / ~2450 (0.76) / ~4000 (0.71) |
| Process 2x @2980 | 2414 (0.54) / 4258 (0.42) / 7192 (0.29) cpm | ~2420 (0.54) / ~4250 (0.43) / ~7150 (0.29) |
| Water 1x @2980 | 1741 (0.56) / 3287 (0.67) / 4822 (0.71) cpm | ~1720 (0.56) / ~3250 (0.67) / ~4870 (0.69) |
| Oil-whirl modes DE / NDE | 1530 (0.23) / 1510 (0.20) cpm | ζ 0.23 / 0.20 |

The impeller-volute interaction coefficients in the report are not tabulated, so they are not in the model.

### Coupling balance

1. Edit `balancing_input.toml`. Set the probe angles, the keyphasor angle, the coupling balance
   radius and the 1X readings (amplitude and phase lag) for NDE X/Y and DE X/Y.
2. Run `python -m p2616f.balance balancing_input.toml --out balance_report.md`. The report gives:
   1. the model influence coefficients for process 1x, process 2x and water 1x, so you can see how
      much they depend on seal condition.
   2. a single-plane fit at the screw pump, 1st impeller, mid impeller, last impeller and coupling.
      This shows whether a coupling unbalance explains the measured 1X pattern.
   3. a simulated trial run, with the trial weight sized to change the largest reading by about 30%.
   4. a one-shot correction weight from least squares over all probes, with the predicted residuals
      and a separate solution from each probe as a cross-check.
   5. if you fill in `[trial]` after a trial run, the measured and model influence coefficients side by
      side, and a correction from the measured coefficients.

Conventions: probe angles are measured from TDC in the direction of rotation. Phase is phase lag.
Weight angles are measured from the keyphasor notch against rotation. The tests in
`tests/test_p2616f.py` check these conventions.

Run the tests with `python -m pytest tests`.
