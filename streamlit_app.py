import streamlit as st
import numpy as np
import ross as rs
from ross.units import Q_
from ross.probe import Probe
import plotly.graph_objects as go
import numba

# Initialize session state
if "shaft_elems" not in st.session_state:
    st.session_state.shaft_elems = []
if "disk_elems" not in st.session_state:
    st.session_state.disk_elems = []
if "bearing_elems" not in st.session_state:
    st.session_state.bearing_elems = []


menu = st.sidebar.radio("Select step", ["Home", "General tips", "Shaft Elements", "Disk Elements", "Bearings & Seals", "Analyses"])

if menu == "Home":
    st.title("🌀 Interactive Rotor Dynamics Solver!")

    st.header("Welcome to the front page of the interactive Rotor Dynamics Solver")

    st.markdown("The purpose of this solver is to make rotordynamics modeling more accessible to those who are interested, such that they can for themselves build a " \
    "rotordynamic model with shaft, disk, bearing & seal elements, and run analysis on the created model to obtain outputs such as Static deflection, " \
    "Undamped critical speed map, Unbalance responses and much more, to become more familiar with the topic ")

    st.markdown("Below is an example of a Rotor model built for RHIP MP MGI K6111 through utilizing this solver")
    st.image("Rotor model.PNG", width = 1500)

    st.badge("")

steel = rs.Material(name="Steel", rho=7850, E=2.059e11, Poisson=0.3)

if menu == "General tips":
    st.title("General tips in building a rotor model")
    st.markdown("""
                1) Number of rotor stations should be at least four times the number of natural frequencies to be calculated. (Ex if you want first four, then 16 stations at least)    
                2) Shrink fit effect on added stiffness can be ignored especially due to the fact that centrifugal force at operating speed tends to alleviate the fit
                3) In sections with abrupt change in cross-section, the effective stiffness diameter is less than the actual. This is compensated by code when entering effective diameter for mass and for stiffness
                4) If modeling pumps, be aware that the dry critical speeds are much lower than the wet critical speeds which will be encountred in the actual condition due to the effect of the fluid interaction within the seals/impeller""")
# ---------- Shaft Elements ----------
if menu == "Shaft Elements":
    st.header("Add Shaft Element")
    st.subheader("Note: Do not create elements with L/D above 1, or L/D much below 0.1. Optimal is L/D 0.6 or less")
    n = st.number_input("Node number", min_value=0, value=0)
    L = st.number_input("Length [mm]", value=50.0)
    od_mass = st.number_input("Outer diameter for mass [mm]", value=100.0)
    od_stiff = st.number_input("Outer diameter for stiffness [mm]", value=100.0)
    id_ = st.number_input("Inner diameter [mm]", value=0.0)

    if st.button("Add Shaft Element"):
        L_m = L / 1000
        od_mass_m = od_mass / 1000
        od_stiff_m = od_stiff / 1000
        id_m = id_ / 1000

        if od_mass != od_stiff:
            rho_adj = steel.rho * (od_mass_m / od_stiff_m) ** 2
            mat = rs.Material(name=f"adj_{n}", rho=rho_adj, E=steel.E, Poisson=steel.Poisson)
        else:
            mat = steel

        elem = rs.ShaftElement(L=L_m, idl=id_m, odl=od_stiff_m, material=mat, n=n,
                               shear_effects=True, rotary_inertia=True, gyroscopic=True)
        st.session_state.shaft_elems.append(elem)
        st.success(f"Added shaft element at node {n}")

    if st.session_state.shaft_elems:
        rotor = rs.Rotor(st.session_state.shaft_elems,
                        st.session_state.disk_elems,
                        st.session_state.bearing_elems,
                        )

        fig = rotor.plot_rotor(nodes = 1)
        st.plotly_chart(fig)

# ---------- Disk Elements ----------
elif menu == "Disk Elements":
    st.header("Add Disk Element")

    n = st.number_input("Node number", min_value=0, value=0)
    m = st.number_input("Mass [kg]", value=10.0)
    Ip = st.number_input("Polar inertia [kg.m²]", value=0.1)
    Id = st.number_input("Transverse inertia [kg.m²]", value=0.05)

    if st.button("Add Disk Element"):
        elem = rs.DiskElement(n=n, m=m, Ip=Ip, Id=Id)
        st.session_state.disk_elems.append(elem)
        st.success(f"Added disk element at node {n}")

    if st.session_state.shaft_elems:
        rotor = rs.Rotor(st.session_state.shaft_elems,
                        st.session_state.disk_elems,
                        st.session_state.bearing_elems,
                        )

        fig = rotor.plot_rotor(nodes = 1)
        st.plotly_chart(fig)

# ---------- Bearings & Seals ----------
# Bearing Element
elif menu == "Bearings & Seals":
    st.header("Add Bearing Element")

    
    # Let user choose between a simple (linear) bearing or a fluid‐film bearing
    bearing_type = st.selectbox("Bearing Type", ["I have dynamic coeffcient", "I have bearing geometry (Journal bearing)"])
    
    if bearing_type == "I have dynamic coeffcient":
        # — your existing Linear BearingElement code here —
        n_b = st.number_input("Node number", min_value=0, value=0)

        st.write("Enter stiffness coefficients (N/m):")
        kxx = st.text_input("kxx (comma-separated)", "1e7,2e7,3e7,4e7,5e7")
        kyy = st.text_input("kyy (comma-separated)", "1e7,2e7,3e7,4e7,5e7")
        kxy = st.text_input("kxy (comma-separated)", "0,0,0,0,0")
        kyx = st.text_input("kyx (comma-separated)", "0,0,0,0,0")

        st.write("Enter damping coefficients (N.s/m):")
        cxx = st.text_input("cxx (comma-separated)", "1e3,2e3,3e3,4e3,5e3")
        cyy = st.text_input("cyy (comma-separated)", "1e3,2e3,3e3,4e3,5e3")
        cxy = st.text_input("cxy (comma-separated)", "0,0,0,0,0")
        cyx = st.text_input("cyx (comma-separated)", "0,0,0,0,0")

        freq_str = st.text_input("Frequencies (RPM, comma-separated, optional)", "5000,10000,15000,20000,25000")

        if st.button("Add Bearing Element"):
            def parse_list(text):
                return np.array([float(x) for x in text.split(",")])

            kxx_arr = parse_list(kxx)
            kyy_arr = parse_list(kyy)
            kxy_arr = parse_list(kxy)
            kyx_arr = parse_list(kyx)
            cxx_arr = parse_list(cxx)
            cyy_arr = parse_list(cyy)
            cxy_arr = parse_list(cxy)
            cyx_arr = parse_list(cyx)

            if freq_str.strip():
                freqs_rpm = parse_list(freq_str)
                frequencies = freqs_rpm * 2 * np.pi / 60  # convert to rad/s

                elem = rs.BearingElement(
                    n=n_b, kxx=kxx_arr, kyy=kyy_arr, kxy=kxy_arr, kyx=kyx_arr,
                    cxx=cxx_arr, cyy=cyy_arr, cxy=cxy_arr, cyx=cyx_arr,
                    frequency=frequencies
                )
            else:
                elem = rs.BearingElement(
                    n=n_b, kxx=kxx_arr[0], kyy=kyy_arr[0], kxy=kxy_arr[0], kyx=kyx_arr[0],
                    cxx=cxx_arr[0], cyy=cyy_arr[0], cxy=cxy_arr[0], cyx=cyx_arr[0]
                )

            st.session_state.bearing_elems.append(elem)
            st.success(f"Bearing element at node {n_b} added.")
        if st.session_state.shaft_elems:
            rotor = rs.Rotor(st.session_state.shaft_elems,
                            st.session_state.disk_elems,
                            st.session_state.bearing_elems,
                            )

            fig = rotor.plot_rotor(nodes = 1)
            st.plotly_chart(fig)

    
    else:  # Fluid Film Bearing
        n_b = st.number_input("Node number", min_value=0, value=0)
        cols = st.columns(2)
        with cols[0]:
            nz      = st.number_input("Axial grid points (nz)",      min_value=2,  value=30)
            ntheta  = st.number_input("Circumferential grid points (ntheta)", min_value=3, step=2, value=21)
            length  = st.number_input("Bearing length [mm]",         value=30.0)
            j_diam  = st.number_input("Journal diameter [mm]",       value=100.0)
            s_diam  = st.number_input("Stator diameter [mm]",        value=100.2)
        with cols[1]:
            viscosity     = st.number_input("Oil viscosity [Pa·s]",  value=0.1)
            fluid_density = st.number_input("Oil density [kg/m³]",   value=860.0)
            load          = st.number_input("Static load [N]",       value=525.0)
            p_in          = st.number_input("Inlet pressure [Pa]",   value=0.0)
            p_out         = st.number_input("Outlet pressure [Pa]",  value=0.0)
        
        speed_str = st.text_input("Speeds (RPM, comma-separated)", "500,1000,1500,2000")
        
        if st.button("Add Fluid Film Bearing"):
            # parse speeds
            speeds = np.array([float(s) for s in speed_str.split(",")])
            omega  = speeds * 2 * np.pi / 60.0  # rad/s
            
            # convert mm→m
            L = length / 1000.0
            r_rotor  = (j_diam / 2.0) / 1000.0
            r_stator = (s_diam / 2.0) / 1000.0
            
            # instantiate a frequency-dependent bearing
            fb = rs.BearingFluidFlow(
                n            = n_b,
                nz           = int(nz),
                ntheta       = int(ntheta),
                length       = L,
                omega        = omega,
                p_in         = p_in,
                p_out        = p_out,
                radius_rotor = r_rotor,
                radius_stator= r_stator,
                visc         = viscosity,
                rho          = fluid_density,
                load         = load,
            )
            st.session_state.bearing_elems.append(fb)
            st.success(f"Added fluid‐film bearing at node {n_b}")
            if st.session_state.shaft_elems:
                rotor = rs.Rotor(st.session_state.shaft_elems,
                                st.session_state.disk_elems,
                                st.session_state.bearing_elems,
                                )

                fig = rotor.plot_rotor(nodes = 1)
                st.plotly_chart(fig)

# ---------- Analyses ----------
elif menu == "Analyses":
    st.header("Rotor Model & Analyses")

    if st.session_state.shaft_elems:
        rotor = rs.Rotor(st.session_state.shaft_elems,
                         st.session_state.disk_elems,
                         st.session_state.bearing_elems,
                         )

        fig = rotor.plot_rotor(nodes = 5)
        st.plotly_chart(fig)
        if st.button ("Clear all Shaft Elements"):
            st.session_state.shaft_elems.clear()
        if st.button ("Clear all Disk Elements"):
            st.session_state.disk_elems.clear()
        if st.button ("Clear all Bearing Elements"):
            st.session_state.bearing_elems.clear()

        analysis = st.selectbox("Select analysis", ["Static", "Modal", "UCS", "Unbalance", "Level 1 Stability"])

        if analysis == "Static":
            static = rotor.run_static()
            st.plotly_chart(static.plot_deformation())
            st.plotly_chart(static.plot_free_body_diagram())
            st.write(f"Rotor mass: {rotor.m:.2f} kg, CG: {rotor.CG:.3f} m")

        elif analysis == "Modal":
            st.header("Modal Analysis")

            # Number of modes
            modes = st.number_input("Number of modes to show", min_value=1, value=6)

            # Speed selection
            speed_rpm = st.number_input("Rotor speed (RPM)", min_value=0, value=0)
            speed_rad = speed_rpm * np.pi / 30

            # Run modal
            modal = rotor.run_modal(speed=speed_rad)

            # Modal summary table
            frequencies = modal.wn[:modes] / (2 * np.pi)  # Hz
            damp_ratios = modal.damping_ratio[:modes]
            log_dec = modal.log_dec[:modes]

            modal_data = {
                "Mode": list(range(1, modes + 1)),
                "Frequency [Hz]": np.round(frequencies, 2),
                "Damping Ratio [-]": np.round(damp_ratios, 3),
                "Log Dec [-]": np.round(log_dec, 3),
            }
            st.write("### Modal Summary")
            st.table(modal_data)

            # Choose mode shape
            mode_to_plot = st.selectbox("Select mode shape to plot", list(range(1, modes + 1)))

            fig_mode = modal.plot_mode_2d(mode=mode_to_plot - 1)
            st.plotly_chart(fig_mode)

            # Optional Campbell diagram
            if st.checkbox("Show Campbell diagram"):
                campbell = rotor.run_campbell(n_modes=modes)
                fig_campbell = campbell.plot(w_speed_units="rpm", log_dec=True)
                st.plotly_chart(fig_campbell)

        elif analysis == "UCS":
            ucs = rotor.run_ucs(stiffness_range=(7, 10),)
            st.plotly_chart(ucs.plot(frequency_units="RPM", yaxis=dict(type="linear", range=(0, 25000)), width=600, height=800))


                # --- before your `analysis == "Unbalance"` ---
        if "unbalances" not in st.session_state:
            st.session_state.unbalances = []

        elif analysis == "Unbalance":
            st.subheader("Define Unbalance Masses")
            with st.expander("Add a new unbalance mass"):
                u_node = st.number_input("Node", min_value=0, key="u_node")
                u_mass = st.number_input("Mass [kg·m]", min_value=0.0, format="%.6f", key="u_mass")
                u_phase = st.number_input("Phase [deg]", min_value=0.0, max_value=360.0, key="u_phase")
                if st.button("Add Unbalance Mass"):
                    st.session_state.unbalances.append({
                        "node": int(u_node),
                        "mass": float(u_mass),
                        "phase": float(u_phase)
                    })
                    st.success(f"Added: node={u_node}, m={u_mass}, φ={u_phase}°")

            # Display current list with remove buttons
            if st.session_state.unbalances:
                st.write("#### Current Unbalances")
                for i, u in enumerate(st.session_state.unbalances):
                    cols = st.columns([3,1])
                    cols[0].write(f"{i+1}. Node {u['node']}, m={u['mass']:.6f}, φ={u['phase']}°")
                    if cols[1].button("❌", key=f"del_{i}"):
                        st.session_state.unbalances.pop(i)
                        st.experimental_rerun()

            # Frequency range (same as before)
            freq_range = Q_(np.linspace(0, 20000, 200), "RPM")

            # Run button
            if st.button("Run Unbalance Response") and st.session_state.unbalances:
                # extract three lists
                nodes   = [u["node"]  for u in st.session_state.unbalances]
                masses  = [u["mass"]  for u in st.session_state.unbalances]
                phases  = [u["phase"] for u in st.session_state.unbalances]

                response = rotor.run_unbalance_response(nodes, masses, phases, freq_range)
            
                # at top of your Analyses block, alongside unbalances init
            if "probes" not in st.session_state:
                st.session_state.probes = []

            # inside `elif analysis == "Unbalance":`
            st.subheader("Define Measurement Probes")

            with st.expander("Add a new probe"):
                p_node  = st.number_input("Probe node",    min_value=0, key="p_node")
                p_phase = st.number_input("Probe phase [°]", min_value=0.0, max_value=360.0, key="p_phase")
                if st.button("Add Probe"):
                    st.session_state.probes.append({
                        "node":  int(p_node),
                        "phase": float(p_phase)
                    })
                    st.success(f"Probe at node {p_node}, φ={p_phase}° added")

        # show current probes with delete buttons
            if st.session_state.probes:
                st.write("#### Current Probes")
                for i, pr in enumerate(st.session_state.probes):
                    cols = st.columns([3,1])
                    cols[0].write(f"{i+1}. Node {pr['node']}, φ={pr['phase']}°")
                    if cols[1].button("❌", key=f"del_pr_{i}"):
                        st.session_state.probes.pop(i)
                        st.experimental_rerun()

        # (keep your freq_range and Run button logic)
            if st.button("Run Unbalance Response", key ="run_unbalance") and st.session_state.unbalances:
                # collect unbalance lists as before
                nodes  = [u["node"]  for u in st.session_state.unbalances]
                masses = [u["mass"]  for u in st.session_state.unbalances]
                phases = [u["phase"] for u in st.session_state.unbalances]

                resp = rotor.run_unbalance_response(nodes, masses, phases, freq_range)

                # now build Probe objects from session_state.probes
                probe_list = [
                    Probe(pr["node"], Q_(pr["phase"], "deg"))
                    for pr in st.session_state.probes
                ]

                st.plotly_chart(
                    resp.plot(
                        probe=probe_list,
                        frequency_units="RPM",
                        amplitude_units="um",
                        phase_units="deg"
                    ),
                    use_container_width=True
                )
            elif st.button("Run Unbalance Response", key="unbalance"):
                st.error("Add at least one unbalance mass first.")

        elif analysis == "Level 1 Stability":
            stiffness_min = st.number_input("Min stiffness [N/m]", value=5.4e6)
            stiffness_max = st.number_input("Max stiffness [N/m]", value=6.0e6)
            node_number = st.number_input( "Node where cross-coupled stiffness is applied", value = 0)
            CompressorRPM = st.number_input (" Enter rated speed in RPM", value = 0)
            if st.button ("Start level 1 analysis"):
                rotor1 = rs.Rotor(st.session_state.shaft_elems,
                         st.session_state.disk_elems,
                         st.session_state.bearing_elems,
                         rated_w = CompressorRPM * np.pi/30)
                level1 = rotor1.run_level1(n=node_number, stiffness_range=(stiffness_min, stiffness_max))

                fig5 = level1.plot()

                api_limit = 0.1
                fig5.add_trace(go.Scatter(x=level1.stiffness_range,
                                      y=[api_limit]*len(level1.stiffness_range),
                                      mode='lines', name='API Limit', line=dict(color='red', dash='dash')))
                fig5.update_layout(title="Level 1 Stability with API Limit")
                st.plotly_chart(fig5)
    else:
        st.warning("Please add at least one shaft element first!")
