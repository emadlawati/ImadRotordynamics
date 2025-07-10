import streamlit as st
import numpy as np
import ross as rs
from ross.units import Q_
import plotly.graph_objects as go

# Initialize session state
if "shaft_elems" not in st.session_state:
    st.session_state.shaft_elems = []
if "disk_elems" not in st.session_state:
    st.session_state.disk_elems = []
if "bearing_elems" not in st.session_state:
    st.session_state.bearing_elems = []

st.title("🌀 Interactive Rotor Dynamics Solver!")

menu = st.sidebar.radio("Select step", ["Home", "Shaft Elements", "Disk Elements", "Bearings & Seals", "Analyses"])

if menu == "Home":

    st.header("Welcome to the front page of the interactive Rotor Dynamics Solver")

    st.markdown("The purpose of this solver is to make rotordynamics modeling more accessible to those who are interested, such that they can for themselves build a " \
    "rotordynamic model with shaft, disk, bearing & seal elements, and run analysis on the created model to obtain outputs such as Static deflection, " \
    "Undamped critical speed map, Unbalance responses and much more, to become more familiar with the topic ")

    st.markdown("Below is an example of a Rotor model built for RHIP MP MGI K6111 through utilizing this solver")
    

    st.badge("Created by Imad al-Lawati")

steel = rs.Material(name="Steel", rho=7850, E=2.059e11, Poisson=0.3)

# ---------- Shaft Elements ----------
if menu == "Shaft Elements":
    st.header("Add Shaft Element")

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

# ---------- Bearings & Seals ----------
elif menu == "Bearings & Seals":
    st.header("Add Bearing or Seal Element")

    n = st.number_input("Node number", min_value=0, value=0)
    kxx = st.number_input("Stiffness kxx [N/m]", value=1e6)
    cxx = st.number_input("Damping cxx [N.s/m]", value=1e3)
    seal = st.checkbox("Add as seal (advanced)")

    if st.button("Add Bearing/Seal"):
        if seal:
            elem = rs.SealElement(n=n, kxx=kxx, kxy=0, kyx=0, kyy=kxx, cxx=cxx, cxy=0, cyx=0, cyy=cxx)
            st.session_state.bearing_elems.append(elem)
            st.success(f"Added seal element at node {n}")
        else:
            elem = rs.BearingElement(n=n, kxx=kxx, kyy=kxx, cxx=cxx, cyy=cxx)
            st.session_state.bearing_elems.append(elem)
            st.success(f"Added bearing element at node {n}")

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

        analysis = st.selectbox("Select analysis", ["Static", "Modal", "UCS", "Unbalance", "Level 1 Stability"])

        if analysis == "Static":
            static = rotor.run_static()
            st.plotly_chart(static.plot_deformation())
            st.plotly_chart(static.plot_free_body_diagram())
            st.write(f"Rotor mass: {rotor.m:.2f} kg, CG: {rotor.CG:.3f} m")

        elif analysis == "Modal":
            modes = st.number_input("Number of modes", min_value=1, value=6)
            modal = rotor.run_modal(speed=0, num_modes=modes)
            st.plotly_chart(modal.plot())

        elif analysis == "UCS":
            ucs = rotor.run_ucs()
            st.plotly_chart(ucs.plot())

        elif analysis == "Unbalance":
            n_unb = st.number_input("Node number", min_value=0, value=0)
            m_unb = st.number_input("Mass [kg.m]", value=0.0005)
            p_unb = st.number_input("Phase [deg]", value=0)
            freq_range = np.linspace(0, 25000, 200)
            freq_range = Q_(freq_range, "RPM")

            response = rotor.run_unbalance_response(n_unb, m_unb, p_unb, freq_range)
            st.plotly_chart(response.plot())

        elif analysis == "Level 1 Stability":
            stiffness_min = st.number_input("Min stiffness [N/m]", value=5.4e6)
            stiffness_max = st.number_input("Max stiffness [N/m]", value=6.0e6)
            level1 = rotor.run_level1(n=30, stiffness_range=(stiffness_min, stiffness_max))
            fig5 = level1.plot()
            api_limit = 0.1
            fig5.add_trace(go.Scatter(x=level1.stiffness_range,
                                      y=[api_limit]*len(level1.stiffness_range),
                                      mode='lines', name='API Limit', line=dict(color='red', dash='dash')))
            fig5.update_layout(title="Level 1 Stability with API Limit")
            st.plotly_chart(fig5)
    else:
        st.warning("Please add at least one shaft element first!")
