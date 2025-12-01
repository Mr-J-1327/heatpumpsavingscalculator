# app.py (Updated: CSV only + Editable CV)
import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import matplotlib.pyplot as plt
import math

# --------------------------
# App config
# --------------------------
st.set_page_config(page_title="HEAT PUMP SAVINGS CALCULATOR", page_icon="🔥", layout="wide")
st.title("♨️ HEAT PUMP SAVINGS CALCULATOR")

# Branding image (optional)
try:
    st.image("/mnt/data/4900a0ed-a960-440a-a771-64bcd2d0724b.png", width=260)
except:
    pass

# --------------------------
# Default Fuel Database
# --------------------------
default_fuel_df = pd.DataFrame([
    {"Fuel": "Biomass", "CV_default": 3000, "Eff_default": 70, "Fuel_Cost":10,"CO2_Emn/kg":1.8},
    {"Fuel": "LPG", "CV_default": 11500, "Eff_default": 90, "Fuel_Cost":60,"CO2_Emn/kg":3},
    {"Fuel": "PNG", "CV_default": 11500, "Eff_default": 90, "Fuel_Cost":60,"CO2_Emn/kg":2.8},
    {"Fuel": "Diesel", "CV_default": 10500, "Eff_default": 85, "Fuel_Cost":100,"CO2_Emn/kg":3.2},
    {"Fuel": "Coal", "CV_default": 5000, "Eff_default": 65, "Fuel_Cost":10,"CO2_Emn/kg":2.5},
    {"Fuel": "Electric (resistive)", "CV_default": 860, "Eff_default": 100, "Fuel_Cost":8,"CO2_Emn/kg":0.82},
])

st.sidebar.header("Optional: Upload Fuel Database")
upload = st.sidebar.file_uploader("Upload fuel DB", type=["xlsx","xls","csv"])
fuel_df = default_fuel_df.copy()

# --------------------------
# Tabs
# --------------------------
tab1, tab2, tab3 = st.tabs(["Inputs", "Cooling Benefit", "Results & Export"])

# --------------------------
# Tab 1: Inputs
# --------------------------
with tab1:
    st.header("1) Heating Capacity Input")
    method = st.selectbox("Select method", ["Steam Flow Rate", "Heating Capacity (kW)", "Electric Heater (kW)", "Boiler Capacity (kcal/hr)"])
    heating_capacity_kW = 0

    if method == "Steam Flow Rate":
        steam_flow = st.number_input("Steam flow (kg/hr)", value=1000.0)
        steam_pressure = st.number_input("Steam Inlet Pressure (bar abs)", value=1.0, min_value=0.1)
        condensate_temp = st.number_input("Condensate temp (°C)", value=95.0)

        steam_table = pd.DataFrame({
            "pressure_bar": [1,1.5,2,2.5,3,3.5,4,4.5,5,5.5,6,6.5,7,7.5,8,8.5,9,9.5,10,10.5,11],
            "vapor_enthalpy": [2674.9,2693.1,2706.2,2716.5,2724.9,2732,2738.1,2743.4,2748.1,2752.3,
                               2756.1,2759.6,2762.8,2765.6,2768.3,2770.8,2773,2775.1,2777.1,2778.9,2780.6]
        })

        h_vapor = np.interp(steam_pressure, steam_table["pressure_bar"], steam_table["vapor_enthalpy"])
        h_liquid = 4.186 * condensate_temp
        heating_capacity_kW = steam_flow * (h_vapor - h_liquid) / 3600

    elif method == "Heating Capacity (kW)":
        heating_capacity_kW = st.number_input("Heating capacity (kW)", value=462.0)

    elif method == "Electric Heater (kW)":
        heating_capacity_kW = st.number_input("Electric heater rating (kW)", value=462.0)

    elif method == "Boiler Capacity (kcal/hr)":
        boiler_input = st.number_input("Boiler capacity (kcal/hr)", value=100000.0)
        heating_capacity_kW = boiler_input / 860

    st.markdown("---")
    st.header("2) Temperature & COP")

    source_temp = st.number_input("Source Temperature (°C)", value=35.0)
    hot_water_temp = st.number_input("Required Hot Water Temperature (°C)", value=65.0)

    evap_temp = source_temp - 10
    cond_temp = hot_water_temp + 5

    cop_ideal = round((cond_temp + 273) / ((cond_temp + 273) - (evap_temp + 273)), 2)
    cop = st.number_input("Actual COP (editable)", value=cop_ideal*0.52)

    st.markdown("---")
    st.header("3) Operation & Fuel Selection")

    hours = st.number_input("Hours/day", value=24.0)
    days = st.number_input("Days/year", value=330)
    elec_cost = st.number_input("Electricity Cost (Rs/kWh)", value=5.5)

    fuel = st.selectbox("Fuel Type", fuel_df["Fuel"])
    row = fuel_df[fuel_df["Fuel"] == fuel].iloc[0]

    # ---- Editable CV ----
    cv = st.number_input("Calorific Value (kcal/kg)", value=float(row["CV_default"]))

    eff = float(row["Eff_default"]) / 100
    fuel_cost = float(row["Fuel_Cost"])
    co2_factor_fuel = float(row["CO2_Emn/kg"])
    co2_factor_grid = 0.82

    if fuel.lower() == "electric (resistive)":
        fuel_cost = elec_cost

    labour_cost_per_day = st.number_input("Boiler Labour Cost (Rs/day)", value=0.0)
    boiler_connected_load = st.number_input("Boiler Connected Load (kW)", value=0.0)

# --------------------------
# Tab 2: Cooling Benefit
# --------------------------
with tab2:
    st.header("Optional Cooling Benefit")
    enable_cooling = st.checkbox("Enable Cooling Benefit?")
    ikW_TR = 0.8
    if enable_cooling:
        ikW_TR = st.number_input("Chiller Efficiency (ikW/TR)", value=0.8)

# --------------------------
# Tab 3: Results & Export
# --------------------------
with tab3:
    hp_input_kW = heating_capacity_kW / cop
    req_kJ_hr = heating_capacity_kW
    fuel_kg_hr = (req_kJ_hr * 3600) / (cv * eff * 4.184)
    fuel_yr = fuel_kg_hr * hours * days
    fuel_cost_year = fuel_yr * fuel_cost

    boiler_operating_cost = fuel_cost_year + labour_cost_per_day * days + boiler_connected_load * hours * days * elec_cost
    hp_cost_year = hp_input_kW * hours * days * elec_cost

    co2_fuel_year = fuel_yr * co2_factor_fuel
    co2_hp_year = hp_input_kW * hours * days * co2_factor_grid

    cooling_capacity_kW = 0
    cooling_capacity_TR = 0
    cooling_input_kW = 0
    cooling_cost_year = 0
    cooling_co2_year = 0

    if enable_cooling:
        cooling_capacity_kW = max(heating_capacity_kW - hp_input_kW, 0)
        cooling_capacity_TR = cooling_capacity_kW / 3.516
        cooling_input_kW = cooling_capacity_TR * ikW_TR
        cooling_cost_year = cooling_input_kW * hours * days * elec_cost
        cooling_co2_year = cooling_input_kW * hours * days * co2_factor_grid

    total_hp_cost = hp_cost_year + (cooling_cost_year if enable_cooling else 0)
    total_co2_hp = co2_hp_year + (cooling_co2_year if enable_cooling else 0)
    total_savings = boiler_operating_cost - total_hp_cost
    total_co2_reduction = co2_fuel_year - total_co2_hp

    summary_df = pd.DataFrame(
        columns=["Annual Boiler Operating Cost (Rs/year)",
                 "Heat Pump Operating Cost (Rs/year)",
                 "Annual Savings (Rs/year)",
                 "Annual CO₂ Reduction (ton/year)"],
        data=[[round(boiler_operating_cost,2),
               round(total_hp_cost,2),
               round(total_savings,2),
               round(total_co2_reduction/1000,2)]]
    )
    st.subheader("📌 Summary")
    st.table(summary_df)

    results_df = pd.DataFrame({
        "Parameter": [
            "Heating Capacity (kW)",
            "Fuel Required (kg/year)", "Fuel Cost (Rs/year)",
            "Boiler Labour Cost (Rs/year)",
            "Boiler Connected Load Electricity Cost (Rs/year)",
            "HP Electricity (kW)", "HP Operating Cost (Rs/year)",
            "Cooling Capacity (kW)" if enable_cooling else "Cooling (Disabled)",
            "Cooling Cost (Rs/year)" if enable_cooling else "",
            "Total Operating Cost (HP + Cooling)",
            "Annual Savings (Rs/year)",
            "Calorific Value Used (kcal/kg)",
            "CO₂ (Fuel - ton/year)",
            "CO₂ (HP + Cooling - ton/year)",
            "CO₂ Reduction (ton/year)"
        ],
        "Value": [
            round(heating_capacity_kW,2),
            round(fuel_yr,2), round(fuel_cost_year,2),
            round(labour_cost_per_day*days,2),
            round(boiler_connected_load * hours * days * elec_cost,2),
            round(hp_input_kW,2), round(hp_cost_year,2),
            round(cooling_capacity_kW,2) if enable_cooling else "N/A",
            round(cooling_cost_year,2) if enable_cooling else "",
            round(total_hp_cost,2),
            round(total_savings,2),
            cv,
            round(co2_fuel_year/1000,2),
            round(total_co2_hp/1000,2),
            round(total_co2_reduction/1000,2)
        ]
    })

    st.subheader("📌 Detailed Results")
    st.table(results_df)

    st.subheader("Operating Cost Comparison 💰 (Rs/year)")
    fig2, ax2 = plt.subplots()
    ax2.bar(["Fuel Boiler", "Heat Pump"], [boiler_operating_cost, total_hp_cost])
    ax2.set_ylabel("Rs/year")
    st.pyplot(fig2)

    st.subheader("CO₂ Comparison (kgs/year)")
    fig3, ax3 = plt.subplots()
    ax3.bar(["Fuel Boiler", "Heat Pump"], [co2_fuel_year, total_co2_hp])
    ax3.set_ylabel("kgs/year")
    st.pyplot(fig3)

    st.subheader("Download Output")
    csv = results_df.to_csv(index=False).encode()
    st.download_button("📄 Download CSV", csv, "heatpump_summary.csv")
