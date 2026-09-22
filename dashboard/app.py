# ================================================================
# NASA LI-ION BATTERY PERFORMANCE & DEGRADATION DASHBOARD
# ================================================================

import os
import sys

import streamlit as st
import pandas as pd
import plotly.graph_objects as go


# ================================================================
# PROJECT PATHS
# ================================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_PATH = os.path.join(
    PROJECT_ROOT,
    "data",
    "B0005.mat"
)

RESULTS_DIR = os.path.join(
    PROJECT_ROOT,
    "results"
)

SRC_DIR = os.path.join(
    PROJECT_ROOT,
    "src"
)

sys.path.append(SRC_DIR)


# ================================================================
# IMPORT BATTERY ANALYSIS FUNCTIONS
# ================================================================

from battery_analysis import (
    load_battery,
    extract_charge_data,
    extract_discharge_data,
    extract_impedance_data,
    create_capacity_soh_data,
    calculate_discharge_energy,
    create_temperature_summary,
    calculate_soc_for_discharge,
    create_cycle_summary,
    save_results
)


# ================================================================
# STREAMLIT PAGE CONFIGURATION
# ================================================================

st.set_page_config(
    page_title="NASA Li-ion Battery Analysis",
    page_icon="🔋",
    layout="wide"
)


# ================================================================
# CREATE RESULTS FOLDER
# ================================================================

os.makedirs(
    RESULTS_DIR,
    exist_ok=True
)


# ================================================================
# LOAD AND PROCESS ALL DATA
# ================================================================

@st.cache_data
def load_all_data():

    # ------------------------------------------------------------
    # Load NASA battery data
    # ------------------------------------------------------------

    battery_name, cycles = load_battery(
        DATA_PATH
    )

    # ------------------------------------------------------------
    # Extract charging data
    # ------------------------------------------------------------

    charging_df = extract_charge_data(
        cycles
    )

    # ------------------------------------------------------------
    # Extract discharging data
    # ------------------------------------------------------------

    discharging_df = extract_discharge_data(
        cycles
    )

    # ------------------------------------------------------------
    # Extract impedance data
    # ------------------------------------------------------------

    impedance_df = extract_impedance_data(
        cycles
    )

    # ------------------------------------------------------------
    # Capacity and SOH
    # ------------------------------------------------------------

    capacity_df = create_capacity_soh_data(
        discharging_df
    )

    # ------------------------------------------------------------
    # Energy delivered during discharge
    # ------------------------------------------------------------

    energy_df = calculate_discharge_energy(
        discharging_df
    )

    # ------------------------------------------------------------
    # Temperature summary
    # ------------------------------------------------------------

    temperature_df = create_temperature_summary(
        discharging_df
    )

    # ------------------------------------------------------------
    # Complete cycle summary
    # ------------------------------------------------------------

    summary_df = create_cycle_summary(
        discharging_df,
        capacity_df,
        energy_df
    )

    return (
        battery_name,
        cycles,
        charging_df,
        discharging_df,
        impedance_df,
        capacity_df,
        energy_df,
        temperature_df,
        summary_df
    )


# ================================================================
# LOAD DATA
# ================================================================

(
    battery_name,
    cycles,
    charging_df,
    discharging_df,
    impedance_df,
    capacity_df,
    energy_df,
    temperature_df,
    summary_df
) = load_all_data()


# ================================================================
# SAVE PROCESSED RESULTS
# ================================================================

try:

    save_results(
        charging_df,
        discharging_df,
        capacity_df,
        energy_df,
        summary_df,
        RESULTS_DIR
    )

except Exception:
    pass


# ================================================================
# MAIN TITLE
# ================================================================

st.title(
    "🔋 NASA Li-ion Battery Performance & Degradation Analysis"
)

st.markdown(
    """
This interactive dashboard analyzes experimental Lithium-Ion battery
measurements from the NASA B0005 battery dataset.

Explore charging behavior, discharging behavior, energy delivery,
capacity degradation, State of Health (SOH), and thermal behavior
across repeated battery cycles.
"""
)


# ================================================================
# SIDEBAR
# ================================================================

st.sidebar.title(
    "🔋 Analysis"
)

page = st.sidebar.radio(
    "Select Analysis",
    [
        "🔋 Charging Analysis",
        "⚡ Discharging Analysis",
        "📉 Battery Degradation",
        "📊 Battery Summary"
    ]
)


# ================================================================
# 1. CHARGING ANALYSIS
# ================================================================

if page == "🔋 Charging Analysis":

    st.header(
        "🔋 Charging Analysis"
    )

    st.markdown(
        """
This section shows the electrical and thermal behavior of the
battery during charging operations.
"""
    )

    # ------------------------------------------------------------
    # Select charging operation
    # ------------------------------------------------------------

    charge_numbers = sorted(
        charging_df[
            "charge_number"
        ].unique()
    )

    selected_charge = st.selectbox(
        "Select Charging Operation",
        charge_numbers
    )

    charge_data = charging_df[
        charging_df[
            "charge_number"
        ] == selected_charge
    ].copy()

    # ------------------------------------------------------------
    # KPIs
    # ------------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Maximum Voltage",
            f"{charge_data['voltage_V'].max():.2f} V"
        )

    with col2:

        st.metric(
            "Maximum Current",
            f"{charge_data['current_A'].max():.2f} A"
        )

    with col3:

        st.metric(
            "Maximum Temperature",
            f"{charge_data['temperature_C'].max():.2f} °C"
        )

    with col4:

        duration = (
            charge_data["time_s"].max()
            -
            charge_data["time_s"].min()
        )

        st.metric(
            "Charging Duration",
            f"{duration / 60:.1f} min"
        )

    # ------------------------------------------------------------
    # Charging Voltage / Current / Temperature
    # ------------------------------------------------------------

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=charge_data["time_s"],
            y=charge_data["voltage_V"],
            name="Voltage",
            yaxis="y"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=charge_data["time_s"],
            y=charge_data["current_A"],
            name="Current",
            yaxis="y2"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=charge_data["time_s"],
            y=charge_data["temperature_C"],
            name="Temperature",
            yaxis="y3"
        )
    )

    fig.update_layout(

        title=(
            f"Charging Behavior — "
            f"Operation {selected_charge}"
        ),

        xaxis=dict(
            title="Time (s)"
        ),

        yaxis=dict(
            title="Voltage (V)"
        ),

        yaxis2=dict(
            title="Current (A)",
            overlaying="y",
            side="right"
        ),

        yaxis3=dict(
            title="Temperature (°C)",
            overlaying="y",
            side="right",
            position=0.95
        ),

        hovermode="x unified",

        height=550
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key="charging_voltage_current_temperature"
    )


# ================================================================
# 2. DISCHARGING ANALYSIS
# ================================================================

elif page == "⚡ Discharging Analysis":

    st.header(
        "⚡ Discharging Analysis"
    )

    st.markdown(
        """
This section examines voltage, current, temperature, power,
and relative discharge progress for individual discharge cycles.
"""
    )

    # ------------------------------------------------------------
    # Select discharge
    # ------------------------------------------------------------

    discharge_numbers = sorted(
        discharging_df[
            "discharge_number"
        ].unique()
    )

    selected_discharge_number = st.selectbox(
        "Select Discharge Cycle",
        discharge_numbers
    )

    discharge_data = discharging_df[
        discharging_df[
            "discharge_number"
        ]
        ==
        selected_discharge_number
    ].copy()

    # ------------------------------------------------------------
    # Relative discharge progress
    # ------------------------------------------------------------

    progress_data = calculate_soc_for_discharge(
        discharge_data
    )

    # ------------------------------------------------------------
    # Power
    # ------------------------------------------------------------

    discharge_data["power_W"] = (
        discharge_data["voltage_V"]
        *
        discharge_data["current_A"].abs()
    )

    # ------------------------------------------------------------
    # KPIs
    # ------------------------------------------------------------

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:

        st.metric(
            "Initial Voltage",
            f"{discharge_data['voltage_V'].iloc[0]:.2f} V"
        )

    with col2:

        st.metric(
            "Final Voltage",
            f"{discharge_data['voltage_V'].iloc[-1]:.2f} V"
        )

    with col3:

        st.metric(
            "Maximum Temperature",
            f"{discharge_data['temperature_C'].max():.2f} °C"
        )

    with col4:

        st.metric(
            "Maximum Power",
            f"{discharge_data['power_W'].max():.2f} W"
        )

    with col5:

        duration = (
            discharge_data["time_s"].max()
            -
            discharge_data["time_s"].min()
        )

        st.metric(
            "Discharge Duration",
            f"{duration / 60:.1f} min"
        )

    # ------------------------------------------------------------
    # Voltage / Current / Temperature
    # ------------------------------------------------------------

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=discharge_data["time_s"],
            y=discharge_data["voltage_V"],
            name="Voltage",
            yaxis="y"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=discharge_data["time_s"],
            y=discharge_data["current_A"],
            name="Current",
            yaxis="y2"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=discharge_data["time_s"],
            y=discharge_data["temperature_C"],
            name="Temperature",
            yaxis="y3"
        )
    )

    fig.update_layout(

        title=(
            f"Discharge Behavior — "
            f"Cycle {selected_discharge_number}"
        ),

        xaxis=dict(
            title="Time (s)"
        ),

        yaxis=dict(
            title="Voltage (V)"
        ),

        yaxis2=dict(
            title="Current (A)",
            overlaying="y",
            side="right"
        ),

        yaxis3=dict(
            title="Temperature (°C)",
            overlaying="y",
            side="right",
            position=0.95
        ),

        hovermode="x unified",

        height=550
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key="discharge_voltage_current_temperature"
    )

    # ------------------------------------------------------------
    # Power Plot
    # ------------------------------------------------------------

    fig_power = go.Figure()

    fig_power.add_trace(
        go.Scatter(
            x=discharge_data["time_s"],
            y=discharge_data["power_W"],
            name="Power"
        )
    )

    fig_power.update_layout(
        title=(
            f"Instantaneous Discharge Power — "
            f"Cycle {selected_discharge_number}"
        ),
        xaxis_title="Time (s)",
        yaxis_title="Power (W)",
        height=450
    )

    st.plotly_chart(
        fig_power,
        use_container_width=True,
        key="discharge_power"
    )

    # ------------------------------------------------------------
    # Relative Discharge Progress
    # ------------------------------------------------------------

    if (
        "discharge_progress_percent"
        in progress_data.columns
    ):

        fig_progress = go.Figure()

        fig_progress.add_trace(
            go.Scatter(
                x=progress_data["time_s"],
                y=progress_data[
                    "discharge_progress_percent"
                ],
                name="Discharge Progress"
            )
        )

        fig_progress.update_layout(
            title=(
                f"Relative Discharge Progress — "
                f"Cycle {selected_discharge_number}"
            ),
            xaxis_title="Time (s)",
            yaxis_title="Discharge Progress (%)",
            height=450
        )

        st.plotly_chart(
            fig_progress,
            use_container_width=True,
            key="relative_discharge_progress"
        )


# ================================================================
# 3. BATTERY DEGRADATION
# ================================================================

elif page == "📉 Battery Degradation":

    st.header(
        "📉 Battery Degradation"
    )

    st.markdown(
        """
This section shows how battery capacity, State of Health (SOH),
energy delivery, and temperature behavior change with repeated
discharge cycles.
"""
    )

    # ------------------------------------------------------------
    # Initial and final values
    # ------------------------------------------------------------

    initial_capacity = (
        capacity_df[
            "capacity_Ah"
        ].iloc[0]
    )

    final_capacity = (
        capacity_df[
            "capacity_Ah"
        ].iloc[-1]
    )

    final_soh = (
        capacity_df[
            "SOH_percent"
        ].iloc[-1]
    )

    capacity_loss = (
        (
            initial_capacity
            -
            final_capacity
        )
        /
        initial_capacity
        *
        100
    )

    # ------------------------------------------------------------
    # KPIs
    # ------------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Initial Capacity",
            f"{initial_capacity:.3f} Ah"
        )

    with col2:

        st.metric(
            "Final Capacity",
            f"{final_capacity:.3f} Ah"
        )

    with col3:

        st.metric(
            "Final SOH",
            f"{final_soh:.2f}%"
        )

    with col4:

        st.metric(
            "Capacity Loss",
            f"{capacity_loss:.2f}%"
        )

    # ------------------------------------------------------------
    # Capacity Degradation
    # ------------------------------------------------------------

    fig_capacity = go.Figure()

    fig_capacity.add_trace(
        go.Scatter(
            x=capacity_df[
                "discharge_number"
            ],
            y=capacity_df[
                "capacity_Ah"
            ],
            mode="lines+markers",
            name="Capacity"
        )
    )

    fig_capacity.update_layout(
        title="Battery Capacity Degradation",
        xaxis_title="Discharge Cycle",
        yaxis_title="Capacity (Ah)",
        height=450
    )

    st.plotly_chart(
        fig_capacity,
        use_container_width=True,
        key="capacity_degradation"
    )

    # ------------------------------------------------------------
    # SOH
    # ------------------------------------------------------------

    fig_soh = go.Figure()

    fig_soh.add_trace(
        go.Scatter(
            x=capacity_df[
                "discharge_number"
            ],
            y=capacity_df[
                "SOH_percent"
            ],
            mode="lines+markers",
            name="SOH"
        )
    )

    fig_soh.update_layout(
        title="Battery State of Health",
        xaxis_title="Discharge Cycle",
        yaxis_title="SOH (%)",
        height=450
    )

    st.plotly_chart(
        fig_soh,
        use_container_width=True,
        key="soh_degradation"
    )

    # ------------------------------------------------------------
    # Energy Delivered
    # ------------------------------------------------------------

    fig_energy = go.Figure()

    fig_energy.add_trace(
        go.Scatter(
            x=energy_df[
                "discharge_number"
            ],
            y=energy_df[
                "energy_Wh"
            ],
            mode="lines+markers",
            name="Energy"
        )
    )

    fig_energy.update_layout(
        title="Energy Delivered During Discharge",
        xaxis_title="Discharge Cycle",
        yaxis_title="Energy (Wh)",
        height=450
    )

    st.plotly_chart(
        fig_energy,
        use_container_width=True,
        key="energy_degradation"
    )

    # ------------------------------------------------------------
    # Maximum Temperature
    # ------------------------------------------------------------

    fig_temperature = go.Figure()

    fig_temperature.add_trace(
        go.Scatter(
            x=temperature_df[
                "discharge_number"
            ],
            y=temperature_df[
                "maximum_temperature_C"
            ],
            mode="lines+markers",
            name="Maximum Temperature"
        )
    )

    fig_temperature.update_layout(
        title="Maximum Battery Temperature",
        xaxis_title="Discharge Cycle",
        yaxis_title="Temperature (°C)",
        height=450
    )

    st.plotly_chart(
        fig_temperature,
        use_container_width=True,
        key="temperature_degradation"
    )


# ================================================================
# 4. BATTERY SUMMARY
# ================================================================

elif page == "📊 Battery Summary":

    st.header(
        "Battery Engineering Summary"
    )

    st.markdown(
        """
### What this analysis shows

This project uses experimental battery measurements to examine:

- Charging electrical behavior
- Discharging electrical behavior
- Instantaneous power
- Energy delivered during discharge
- Capacity degradation
- State of Health (SOH)
- Thermal behavior
- Battery aging with repeated use
"""
    )


    # ============================================================
    # DISCHARGE-LEVEL BATTERY DATASET
    # ============================================================

    st.subheader(
        "Discharge-Level Battery Dataset"
    )

    st.dataframe(
        summary_df,
        use_container_width=True
    )

    csv_data = summary_df.to_csv(
        index=False
    )

    st.download_button(
        label="⬇️ Download Battery Summary CSV",
        data=csv_data,
        file_name="battery_summary.csv",
        mime="text/csv",
        key="download_battery_summary"
    )


    # ============================================================
    # PROCESSED BATTERY DATA
    # ============================================================

    st.subheader(
        "Processed Battery Data"
    )

    st.markdown(
        """
Explore the processed datasets used to generate the
dashboard results.
"""
    )


    # ------------------------------------------------------------
    # TABS
    # ------------------------------------------------------------

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "📉 Capacity & SOH",
            "⚡ Discharge Energy",
            "🔋 Charging Data",
            "⚡ Discharging Data"
        ]
    )


    # ============================================================
    # TAB 1 — CAPACITY & SOH
    # ============================================================

    with tab1:

        st.markdown(
            "### Capacity and State of Health"
        )

        st.dataframe(
            capacity_df,
            use_container_width=True,
            height=500
        )

        capacity_csv = capacity_df.to_csv(
            index=False
        )

        st.download_button(
            label="⬇️ Download Capacity & SOH Data",
            data=capacity_csv,
            file_name="capacity_soh.csv",
            mime="text/csv",
            key="download_capacity_soh"
        )


    # ============================================================
    # TAB 2 — DISCHARGE ENERGY
    # ============================================================

    with tab2:

        st.markdown(
            "### Discharge Energy Data"
        )

        st.dataframe(
            energy_df,
            use_container_width=True,
            height=500
        )

        energy_csv = energy_df.to_csv(
            index=False
        )

        st.download_button(
            label="⬇️ Download Discharge Energy Data",
            data=energy_csv,
            file_name="discharge_energy.csv",
            mime="text/csv",
            key="download_discharge_energy"
        )


    # ============================================================
    # TAB 3 — CHARGING DATA
    # ============================================================

    with tab3:

        st.markdown(
            "### Charging Data"
        )

        st.dataframe(
            charging_df,
            use_container_width=True,
            height=500
        )

        charging_csv = charging_df.to_csv(
            index=False
        )

        st.download_button(
            label="⬇️ Download Charging Data",
            data=charging_csv,
            file_name="charging_data.csv",
            mime="text/csv",
            key="download_charging_data"
        )


    # ============================================================
    # TAB 4 — DISCHARGING DATA
    # ============================================================

    with tab4:

        st.markdown(
            "### Discharging Data"
        )

        st.dataframe(
            discharging_df,
            use_container_width=True,
            height=500
        )

        discharging_csv = discharging_df.to_csv(
            index=False
        )

        st.download_button(
            label="⬇️ Download Discharging Data",
            data=discharging_csv,
            file_name="discharging_data.csv",
            mime="text/csv",
            key="download_discharging_data"
        )


    # ============================================================
    # PROJECT INFORMATION
    # ============================================================

    st.subheader(
        "Project Information"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.markdown(
            """
**Dataset:** NASA Ames Battery Dataset

**Battery:** B0005

**Analysis:** Battery Performance and Degradation

**Programming:** Python

**Dashboard:** Streamlit
"""
        )

    with col2:

        st.markdown(
            """
**Key Parameters**

- Voltage
- Current
- Temperature
- Capacity
- State of Health
- Energy
- Discharge behavior
"""
        )