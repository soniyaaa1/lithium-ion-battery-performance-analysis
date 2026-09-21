
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

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        ".."
    )
)

DATA_PATH = os.path.join(
    PROJECT_ROOT,
    "data",
    "B0005.mat"
)

RESULTS_PATH = os.path.join(
    PROJECT_ROOT,
    "results"
)

SRC_PATH = os.path.join(
    PROJECT_ROOT,
    "src"
)

sys.path.insert(
    0,
    SRC_PATH
)


# ================================================================
# IMPORT BATTERY ANALYSIS FUNCTIONS
# ================================================================

from battery_analysis import (
    load_battery,
    extract_charge_data,
    extract_discharge_data,
    extract_impedance_data,
    create_capacity_soh_data,
    create_temperature_summary,
    calculate_soc_for_discharge,
    calculate_discharge_energy,
    create_cycle_summary,
    save_results
)


# ================================================================
# PAGE CONFIGURATION
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
    RESULTS_PATH,
    exist_ok=True
)


# ================================================================
# LOAD ALL BATTERY DATA
# ================================================================

@st.cache_data
def load_all_data():

    battery_name, cycles = load_battery(
        DATA_PATH
    )

    charging_df = extract_charge_data(
        cycles
    )

    discharging_df = extract_discharge_data(
        cycles
    )

    impedance_df = extract_impedance_data(
        cycles
    )

    capacity_df = create_capacity_soh_data(
        discharging_df
    )

    energy_df = calculate_discharge_energy(
        discharging_df
    )

    temperature_df = create_temperature_summary(
        discharging_df
    )

    summary_df = create_cycle_summary(
        discharging_df,
        capacity_df,
        energy_df
    )

    return (
        battery_name,
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

try:

    (
        battery_name,
        charging_df,
        discharging_df,
        impedance_df,
        capacity_df,
        energy_df,
        temperature_df,
        summary_df

    ) = load_all_data()

except Exception as e:

    st.error(
        f"Error loading battery data: {e}"
    )

    st.stop()


# ================================================================
# SAVE PROCESSED CSV DATA
# ================================================================

save_results(
    charging_df,
    discharging_df,
    capacity_df,
    energy_df,
    summary_df,
    RESULTS_PATH
)


# ================================================================
# DASHBOARD TITLE
# ================================================================

st.title(
    "🔋 NASA Li-ion Battery Performance & Degradation Analysis"
)

st.markdown(
    """
Interactive analysis of experimental Li-ion battery data,
including charging behavior, discharge performance,
energy delivery, capacity degradation, State of Health,
and thermal behavior.
"""
)


# ================================================================
# SIDEBAR NAVIGATION
# ================================================================

st.sidebar.title(
    "Dashboard Navigation"
)

page = st.sidebar.radio(
    "Select analysis",
    [
        "🔋 Charging Analysis",
        "⚡ Discharging Analysis",
        "📉 Battery Degradation",
        "📊 Battery Summary"
    ]
)


# ================================================================
# CHARGING ANALYSIS
# ================================================================

if page == "🔋 Charging Analysis":

    st.header(
        "Charging Behavior"
    )

    if charging_df.empty:

        st.warning(
            "No charging data available."
        )

        st.stop()

    charge_numbers = sorted(
        charging_df[
            "charge_number"
        ].unique()
    )

    selected_charge = st.selectbox(
        "Select charging operation",
        charge_numbers,
        key="charge_operation_select"
    )

    data = charging_df[
        charging_df[
            "charge_number"
        ] == selected_charge
    ].copy()


    # ------------------------------------------------------------
    # KPI CARDS
    # ------------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Initial Voltage",
        f"{data['voltage_V'].iloc[0]:.2f} V"
    )

    col2.metric(
        "Final Voltage",
        f"{data['voltage_V'].iloc[-1]:.2f} V"
    )

    col3.metric(
        "Average Current",
        f"{data['current_A'].mean():.2f} A"
    )

    col4.metric(
        "Maximum Temperature",
        f"{data['temperature_C'].max():.2f} °C"
    )


    # ------------------------------------------------------------
    # CHARGING GRAPH
    # ------------------------------------------------------------

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=data["time_s"],
            y=data["voltage_V"],
            name="Voltage",
            mode="lines"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=data["time_s"],
            y=data["current_A"],
            name="Current",
            mode="lines",
            yaxis="y2"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=data["time_s"],
            y=data["temperature_C"],
            name="Temperature",
            mode="lines",
            yaxis="y3"
        )
    )

    fig.update_layout(

        title="Charging Voltage, Current and Temperature",

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
            position=0.90
        ),

        height=600,

        hovermode="x unified"
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key="charging_voltage_current_temperature"
    )


# ================================================================
# DISCHARGING ANALYSIS
# ================================================================

elif page == "⚡ Discharging Analysis":

    st.header(
        "Discharging Performance"
    )

    if discharging_df.empty:

        st.warning(
            "No discharge data available."
        )

        st.stop()

    discharge_numbers = sorted(
        discharging_df[
            "discharge_number"
        ].unique()
    )

    selected_discharge = st.selectbox(
        "Select discharge operation",
        discharge_numbers,
        key="discharge_operation_select"
    )

    data = discharging_df[
        discharging_df[
            "discharge_number"
        ] == selected_discharge
    ].copy()

    data = calculate_soc_for_discharge(
        data
    )

    selected_summary = summary_df[
        summary_df[
            "discharge_number"
        ] == selected_discharge
    ].iloc[0]


    # ------------------------------------------------------------
    # KPI CARDS
    # ------------------------------------------------------------

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        "Capacity",
        f"{selected_summary['capacity_Ah']:.3f} Ah"
    )

    col2.metric(
        "Energy Delivered",
        f"{selected_summary['energy_Wh']:.2f} Wh"
    )

    col3.metric(
        "Average Power",
        f"{selected_summary['average_power_W']:.2f} W"
    )

    max_temperature = data[
        "temperature_C"
    ].max()

    col4.metric(
        "Maximum Temperature",
        f"{max_temperature:.2f} °C"
    )

    col5.metric(
        "SOH",
        f"{selected_summary['SOH_percent']:.2f}%"
    )


    # ------------------------------------------------------------
    # DISCHARGE VOLTAGE / CURRENT / TEMPERATURE
    # ------------------------------------------------------------

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=data["time_s"],
            y=data["voltage_V"],
            name="Voltage",
            mode="lines"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=data["time_s"],
            y=data["current_A"],
            name="Current",
            mode="lines",
            yaxis="y2"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=data["time_s"],
            y=data["temperature_C"],
            name="Temperature",
            mode="lines",
            yaxis="y3"
        )
    )

    fig.update_layout(

        title="Discharge Voltage, Current and Temperature",

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
            position=0.90
        ),

        height=600,

        hovermode="x unified"
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key="discharge_voltage_current_temperature"
    )


    # ------------------------------------------------------------
    # POWER
    # ------------------------------------------------------------

    st.subheader(
        "Discharge Power"
    )

    power_fig = go.Figure()

    power_fig.add_trace(
        go.Scatter(
            x=data["time_s"],
            y=data["power_W"],
            mode="lines",
            name="Power"
        )
    )

    power_fig.update_layout(

        title="Instantaneous Discharge Power",

        xaxis_title="Time (s)",

        yaxis_title="Power (W)",

        height=450
    )

    st.plotly_chart(
        power_fig,
        use_container_width=True,
        key="discharge_power"
    )


    # ------------------------------------------------------------
    # RELATIVE DISCHARGE PROGRESS
    # ------------------------------------------------------------

    st.subheader(
        "Relative Discharge Progress"
    )

    progress_fig = go.Figure()

    progress_fig.add_trace(
        go.Scatter(
            x=data[
                "discharge_progress_percent"
            ],
            y=data["voltage_V"],
            mode="lines",
            name="Voltage"
        )
    )

    progress_fig.update_layout(

        title="Voltage During Relative Discharge Progress",

        xaxis_title="Discharge Progress (%)",

        yaxis_title="Voltage (V)",

        height=450
    )

    st.plotly_chart(
        progress_fig,
        use_container_width=True,
        key="relative_discharge_progress"
    )


# ================================================================
# BATTERY DEGRADATION
# ================================================================

elif page == "📉 Battery Degradation":

    st.header(
        "Battery Aging & Degradation"
    )

    if capacity_df.empty:

        st.warning(
            "No degradation data available."
        )

        st.stop()


    # ------------------------------------------------------------
    # BATTERY HEALTH KPIs
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

    total_loss = (
        capacity_df[
            "capacity_loss_percent"
        ].iloc[-1]
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Initial Capacity",
        f"{initial_capacity:.3f} Ah"
    )

    col2.metric(
        "Final Capacity",
        f"{final_capacity:.3f} Ah"
    )

    col3.metric(
        "Final SOH",
        f"{final_soh:.2f}%"
    )

    col4.metric(
        "Capacity Loss",
        f"{total_loss:.2f}%"
    )


    # ============================================================
    # 1. CAPACITY DEGRADATION
    # ============================================================

    st.subheader(
        "Capacity Degradation"
    )

    capacity_fig = go.Figure()

    capacity_fig.add_trace(
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

    capacity_fig.update_layout(

        title="Battery Capacity Degradation",

        xaxis_title="Discharge Number",

        yaxis_title="Capacity (Ah)",

        template="plotly_white",

        height=600,

        hovermode="x unified"
    )

    st.plotly_chart(
        capacity_fig,
        use_container_width=True,
        key="capacity_degradation"
    )


    # ============================================================
    # 2. SOH VS DISCHARGE
    # ============================================================

    st.subheader(
        "State of Health"
    )

    soh_fig = go.Figure()

    soh_fig.add_trace(
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

    soh_fig.update_layout(

        title="Battery State of Health vs Discharge Number",

        xaxis_title="Discharge Number",

        yaxis_title="State of Health (%)",

        template="plotly_white",

        height=600,

        hovermode="x unified"
    )

    st.plotly_chart(
        soh_fig,
        use_container_width=True,
        key="soh_degradation"
    )


    # ============================================================
    # 3. ENERGY VS DISCHARGE
    # ============================================================

    st.subheader(
        "Energy Delivered vs Battery Use"
    )

    energy_fig = go.Figure()

    energy_fig.add_trace(
        go.Scatter(
            x=energy_df[
                "discharge_number"
            ],
            y=energy_df[
                "energy_Wh"
            ],
            mode="lines+markers",
            name="Energy Delivered"
        )
    )

    energy_fig.update_layout(

        title="Energy Delivered vs Discharge Number",

        xaxis_title="Discharge Number",

        yaxis_title="Energy Delivered (Wh)",

        template="plotly_white",

        height=600,

        hovermode="x unified"
    )

    st.plotly_chart(
        energy_fig,
        use_container_width=True,
        key="energy_degradation"
    )


    # ============================================================
    # 4. TEMPERATURE VS DISCHARGE
    # ============================================================

    st.subheader(
        "Thermal Behavior During Aging"
    )

    temperature_fig = go.Figure()

    temperature_fig.add_trace(
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

    temperature_fig.add_trace(
        go.Scatter(
            x=temperature_df[
                "discharge_number"
            ],
            y=temperature_df[
                "mean_temperature_C"
            ],
            mode="lines",
            name="Average Temperature"
        )
    )

    temperature_fig.update_layout(

        title="Battery Temperature vs Discharge Number",

        xaxis_title="Discharge Number",

        yaxis_title="Temperature (°C)",

        template="plotly_white",

        height=600,

        hovermode="x unified"
    )

    st.plotly_chart(
        temperature_fig,
        use_container_width=True,
        key="temperature_degradation"
    )


# ================================================================
# BATTERY SUMMARY
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


    # ------------------------------------------------------------
    # SUMMARY TABLE
    # ------------------------------------------------------------

    st.subheader(
        "Discharge-Level Battery Dataset"
    )

    st.dataframe(
        summary_df,
        use_container_width=True
    )


    # ------------------------------------------------------------
    # DOWNLOAD SUMMARY
    # ------------------------------------------------------------

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


    # ------------------------------------------------------------
    # PROJECT INFORMATION
    # ------------------------------------------------------------

    st.subheader(
        "Project Information"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.write(
            "**Battery:** NASA Li-ion B0005"
        )

        st.write(
            f"**Discharge operations:** "
            f"{len(capacity_df)}"
        )

        st.write(
            f"**Charge operations:** "
            f"{charging_df['charge_number'].nunique()}"
        )

    with col2:

        st.write(
            "**Analysis:** Battery performance "
            "and degradation"
        )

        st.write(
            "**Platform:** Python + Streamlit"
        )

        st.write(
            "**Visualization:** Plotly"
        )


# ================================================================
# SIDEBAR FOOTER
# ================================================================

st.sidebar.markdown("---")

st.sidebar.info(
    "NASA Li-ion Battery Performance & "
    "Degradation Analysis\n\n"
    "Python • Pandas • SciPy • Plotly • Streamlit"
)

