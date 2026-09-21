# ================================================================
# NASA LI-ION BATTERY PERFORMANCE & DEGRADATION ANALYSIS
# ================================================================

import os
import numpy as np
import pandas as pd
from scipy.io import loadmat


# ================================================================
# 1. LOAD BATTERY DATA
# ================================================================

def load_battery(file_path):
    """
    Load NASA Li-ion battery MATLAB file.

    Returns:
        battery_name
        cycles
    """

    mat = loadmat(file_path)

    battery_names = [
        key for key in mat.keys()
        if not key.startswith("__")
    ]

    if not battery_names:
        raise ValueError("No battery data found in MAT file.")

    battery_name = battery_names[0]

    battery = mat[battery_name]

    battery_data = battery[0, 0]

    cycles = battery_data["cycle"]

    return battery_name, cycles


# ================================================================
# 2. EXTRACT CHARGING DATA
# ================================================================

def extract_charge_data(cycles):

    charge_records = []

    charge_number = 0

    for i in range(cycles.shape[1]):

        record = cycles[0, i]

        record_type = record["type"][0]

        if record_type == "charge":

            charge_number += 1

            data = record["data"][0, 0]

            voltage = np.asarray(
                data["Voltage_measured"]
            ).flatten()

            current = np.asarray(
                data["Current_measured"]
            ).flatten()

            temperature = np.asarray(
                data["Temperature_measured"]
            ).flatten()

            time = np.asarray(
                data["Time"]
            ).flatten()

            n = min(
                len(voltage),
                len(current),
                len(temperature),
                len(time)
            )

            temp_df = pd.DataFrame({

                "charge_number":
                    charge_number,

                "record_index":
                    i + 1,

                "time_s":
                    time[:n],

                "voltage_V":
                    voltage[:n],

                "current_A":
                    current[:n],

                "temperature_C":
                    temperature[:n]
            })

            # Electrical power
            temp_df["power_W"] = (
                temp_df["voltage_V"]
                * temp_df["current_A"]
            )

            charge_records.append(temp_df)

    if charge_records:

        charging_df = pd.concat(
            charge_records,
            ignore_index=True
        )

    else:

        charging_df = pd.DataFrame()

    return charging_df


# ================================================================
# 3. EXTRACT DISCHARGING DATA
# ================================================================

def extract_discharge_data(cycles):

    discharge_records = []

    discharge_number = 0

    for i in range(cycles.shape[1]):

        record = cycles[0, i]

        record_type = record["type"][0]

        if record_type == "discharge":

            discharge_number += 1

            data = record["data"][0, 0]

            voltage = np.asarray(
                data["Voltage_measured"]
            ).flatten()

            current = np.asarray(
                data["Current_measured"]
            ).flatten()

            temperature = np.asarray(
                data["Temperature_measured"]
            ).flatten()

            time = np.asarray(
                data["Time"]
            ).flatten()

            capacity = float(
                np.asarray(
                    data["Capacity"]
                ).flatten()[0]
            )

            n = min(
                len(voltage),
                len(current),
                len(temperature),
                len(time)
            )

            temp_df = pd.DataFrame({

                "discharge_number":
                    discharge_number,

                "record_index":
                    i + 1,

                "time_s":
                    time[:n],

                "voltage_V":
                    voltage[:n],

                "current_A":
                    current[:n],

                "temperature_C":
                    temperature[:n],

                "capacity_Ah":
                    capacity
            })

            # Electrical power
            temp_df["power_W"] = (
                temp_df["voltage_V"]
                * temp_df["current_A"]
            )

            discharge_records.append(temp_df)

    if discharge_records:

        discharging_df = pd.concat(
            discharge_records,
            ignore_index=True
        )

    else:

        discharging_df = pd.DataFrame()

    return discharging_df


# ================================================================
# 4. EXTRACT IMPEDANCE DATA
# ================================================================

def extract_impedance_data(cycles):

    impedance_records = []

    impedance_number = 0

    for i in range(cycles.shape[1]):

        record = cycles[0, i]

        record_type = record["type"][0]

        if record_type == "impedance":

            impedance_number += 1

            data = record["data"][0, 0]

            fields = data.dtype.names

            record_data = {

                "impedance_number":
                    impedance_number,

                "record_index":
                    i + 1
            }

            for field in fields:

                try:

                    value = data[field]

                    value = np.asarray(
                        value
                    ).flatten()

                    if len(value) == 1:

                        record_data[field] = float(
                            value[0]
                        )

                except Exception:

                    pass

            impedance_records.append(
                record_data
            )

    impedance_df = pd.DataFrame(
        impedance_records
    )

    return impedance_df


# ================================================================
# 5. CAPACITY + SOH
# ================================================================

def create_capacity_soh_data(
    discharging_df
):

    if discharging_df.empty:

        return pd.DataFrame()

    capacity_df = (

        discharging_df[
            [
                "discharge_number",
                "capacity_Ah"
            ]
        ]

        .drop_duplicates(
            subset=[
                "discharge_number"
            ]
        )

        .reset_index(drop=True)
    )

    initial_capacity = (
        capacity_df[
            "capacity_Ah"
        ].iloc[0]
    )

    # State of Health
    capacity_df[
        "SOH_percent"
    ] = (

        capacity_df[
            "capacity_Ah"
        ]

        / initial_capacity

        * 100
    )

    # Capacity loss
    capacity_df[
        "capacity_loss_percent"
    ] = (

        (
            initial_capacity
            - capacity_df["capacity_Ah"]
        )

        / initial_capacity

        * 100
    )

    return capacity_df


# # ================================================================
# 6. ENERGY DELIVERED DURING DISCHARGE
# ================================================================

def calculate_discharge_energy(
    discharging_df
):

    if discharging_df.empty:

        return pd.DataFrame()

    energy_records = []

    grouped = discharging_df.groupby(
        "discharge_number"
    )

    for discharge_number, group in grouped:

        group = group.sort_values(
            "time_s"
        )

        time_seconds = (
            group["time_s"]
            .to_numpy()
        )

        voltage = (
            group["voltage_V"]
            .to_numpy()
        )

        # NASA discharge current is negative.
        # Use magnitude for discharge power/energy.
        current = (
            group["current_A"]
            .abs()
            .to_numpy()
        )

        # Discharge power in watts
        power = voltage * current

        # Numerical integration of power over time
        energy_joules = np.trapezoid(
            power,
            time_seconds
        )

        # Convert joules to watt-hours
        energy_Wh = (
            energy_joules / 3600
        )

        energy_records.append({

            "discharge_number":
                discharge_number,

            "energy_Wh":
                energy_Wh,

            "average_power_W":
                np.mean(power),

            "maximum_power_W":
                np.max(power),

            "minimum_power_W":
                np.min(power),

            "minimum_voltage_V":
                np.min(voltage),

            "maximum_voltage_V":
                np.max(voltage),

            "maximum_temperature_C":
                np.max(
                    group[
                        "temperature_C"
                    ]
                )
        })

    return pd.DataFrame(
        energy_records
    )


# ================================================================
# 7. TEMPERATURE SUMMARY
# ================================================================

def create_temperature_summary(
    discharging_df
):

    if discharging_df.empty:

        return pd.DataFrame()

    temperature_df = (

        discharging_df

        .groupby(
            "discharge_number"
        )[

            "temperature_C"

        ]

        .agg(

            mean_temperature_C="mean",

            minimum_temperature_C="min",

            maximum_temperature_C="max"

        )

        .reset_index()
    )

    return temperature_df


# ================================================================
# 8. RELATIVE DISCHARGE PROGRESSION
# ================================================================

def calculate_soc_for_discharge(
    discharge_df
):

    """
    Creates relative discharge progression.

    NOTE:
    This is NOT a measured or physically estimated SOC.
    It simply represents progression from the beginning
    to the end of a discharge operation.
    """

    if discharge_df.empty:

        return discharge_df

    result = discharge_df.copy()

    result[
        "discharge_progress_percent"
    ] = (

        (
            result["time_s"]
            - result["time_s"].min()
        )

        /

        (
            result["time_s"].max()
            - result["time_s"].min()
        )

        * 100
    )

    return result


# ================================================================
# 9. COMPLETE DISCHARGE SUMMARY
# ================================================================

def create_cycle_summary(
    discharging_df,
    capacity_df,
    energy_df
):

    if discharging_df.empty:

        return pd.DataFrame()

    summary = (

        discharging_df

        .groupby(
            "discharge_number"
        )

        .agg(

            average_voltage_V=(
                "voltage_V",
                "mean"
            ),

            minimum_voltage_V=(
                "voltage_V",
                "min"
            ),

            maximum_voltage_V=(
                "voltage_V",
                "max"
            ),

            average_current_A=(
                "current_A",
                "mean"
            ),

            maximum_current_A=(
                "current_A",
                "max"
            ),

            average_temperature_C=(
                "temperature_C",
                "mean"
            ),

            maximum_temperature_C=(
                "temperature_C",
                "max"
            )
        )

        .reset_index()
    )

    summary = summary.merge(
        capacity_df,
        on="discharge_number",
        how="left"
    )

    summary = summary.merge(
        energy_df,
        on="discharge_number",
        how="left"
    )

    return summary


# ================================================================
# 10. SAVE IMPORTANT DATA
# ================================================================

def save_results(
    charging_df,
    discharging_df,
    capacity_df,
    energy_df,
    summary_df,
    results_folder
):

    os.makedirs(
        results_folder,
        exist_ok=True
    )

    if not charging_df.empty:

        charging_df.to_csv(
            os.path.join(
                results_folder,
                "charging_data.csv"
            ),
            index=False
        )

    if not discharging_df.empty:

        discharging_df.to_csv(
            os.path.join(
                results_folder,
                "discharging_data.csv"
            ),
            index=False
        )

    if not capacity_df.empty:

        capacity_df.to_csv(
            os.path.join(
                results_folder,
                "capacity_soh.csv"
            ),
            index=False
        )

    if not energy_df.empty:

        energy_df.to_csv(
            os.path.join(
                results_folder,
                "discharge_energy.csv"
            ),
            index=False
        )

    if not summary_df.empty:

        summary_df.to_csv(
            os.path.join(
                results_folder,
                "battery_summary.csv"
            ),
            index=False
        )