# app.py (enhanced UI with separate tables & cost comparison graph)
import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from datetime import datetime
import matplotlib.pyplot as plt

# App config
st.set_page_config(page_title="HEAT PUMP SAVINGS CALCULATOR", page_icon="🔥", layout="wide")
st.title("♨️ HEAT PUMP SAVINGS CALCULATOR")

# Show branding image (optional)
try:
    st.image("/mnt/data/4900a0ed-a960-440a-a771-64bcd2d0724b.png", width=260)
except:
    pass

# ------------------------------------
# Default Fuel Database
# ------------------------------------
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

# ------------------------------------
# HEATING INPUT
# ------------------------------------
st.header("1) Heating Capacity Input")

method = st.selectbox("Select method", ["Steam Flow Rate", "Direct Heating (kW)", "Electric Heater (kW)", "Boiler Capacity (kcal/hr)"])
heating_capacity_kW = 0

if method == "Steam Flow Rate":
    steam_flow = st.number_input("Steam flow (kg/hr)", value=1000.0)
    steam_latent_kJkg = 2840  # fixed (simplified)
    condensate_temp = st.number_input("Condensate temp (°C)", value=95.0)
    heating_capacity_kW = (steam_flow * (steam_latent_kJkg - (4.186 * condensate_temp))) / 3600

elif method == "Direct Heating (kW)":
    heating_capacity_kW = st.number_input("Heating capacity (kW)", value=462.0)

elif method == "Electric Heater (kW)":
    heating_capacity_kW = st.number_input("Electric heater rating (kW)", value=462.0)

elif method == "Boiler Capacity (kcal/hr)":
    boiler_input = st.number_input("Boiler capacity (kcal/hr)", value=100000.0)
    heating_capacity_kW = boiler_input / 860

st.markdown("---")

# ------------------------------------
# TEMPERATURES & COP
# ------------------------------------
st.header("2) Temperature & COP")
ambient = st.number_input("Ambient (°C)", value=30.0)
hot_water = st.number_input("Hot Water (°C)", value=90.0)
cop = st.number_input("Heat Pump COP", value=3.5)

st.markdown("---")

# ------------------------------------
# OPERATING PROFILE & FUEL
# ------------------------------------
st.header("3) Operation & Fuel Selection")
hours = st.number_input("Hours/day", value=24.0)
days = st.number_input("Days/year", value=330)
elec_cost = st.number_input("Electricity Cost (Rs/kWh)", value=5.5)

fuel = st.selectbox("Fuel Type", fuel_df["Fuel"])
row = fuel_df[fuel_df["Fuel"] == fuel].iloc[0]

cv = st.number_input("Calorific Value (kcal/kg)", value=float(row["CV_default"]))
eff = st.number_input("Boiler Efficiency (%)", value=float(row["Eff_default"]))
fuel_cost = st.number_input("Fuel Cost (Rs/kg)", value=float(row["Fuel_Cost"]))
co2_factor_fuel = float(row["CO2_Emn/kg"])
co2_factor_grid = 0.82

st.markdown("---")

# ------------------------------------
# CALCULATIONS
# ------------------------------------
req_kJ_hr = heating_capacity_kW * 3600
fuel_kg_hr = req_kJ_hr / ((cv * 4.184) * (eff/100))
fuel_yr = fuel_kg_hr * hours * days

fuel_cost_year = fuel_yr * fuel_cost

hp_input_kW = heating_capacity_kW / cop
hp_cost_year = hp_input_kW * hours * days * elec_cost

# CO₂
co2_fuel_year = fuel_yr * co2_factor_fuel
co2_hp_year = (hp_input_kW * hours * days) * co2_factor_grid
co2_reduction = co2_fuel_year - co2_hp_year

roi_years = fuel_cost_year / (fuel_cost_year - hp_cost_year) if (fuel_cost_year - hp_cost_year) > 0 else None

# ------------------------------------
# DATA TABLES
# ------------------------------------
inputs_df = pd.DataFrame({
    "Parameter": ["Heating method", "Heating capacity (kW)", "Operating Hours/day", "Operating Days/year", "Fuel Type Selected"],
    "Value": [method, heating_capacity_kW, hours, days, fuel]
})

assumptions_df = pd.DataFrame({
    "Parameter": ["Calorific Value (kcal/kg)", "Boiler Efficiency (%)", "Electricity Cost (Rs/kWh)", "Heat Pump COP"],
    "Value": [cv, eff, elec_cost, cop]
})

results_df = pd.DataFrame({
    "Parameter": [
        "Fuel Required (kg/year)", "Fuel Cost (Rs/year)", 
        "HP Electricity (kW)", "HP Operating Cost (Rs/year)",
        "Annual Savings 💰 (Rs/year)", "CO₂ (Fuel - ton/year)",
        "CO₂ (Heat pump - ton/year)", "CO₂ Reduction (ton/year)",
        "ROI (Years)"
    ],
    "Value": [
        round(fuel_yr,2), round(fuel_cost_year,2),
        round(hp_input_kW,2), round(hp_cost_year,2),
        round(fuel_cost_year - hp_cost_year,2),
        round(co2_fuel_year/1000,2), round(co2_hp_year/1000,2),
        round(co2_reduction/1000,2),
        round(roi_years,2) if roi_years else "Not Applicable"
    ]
})

# Display tables
st.subheader("📌 User Inputs")
st.table(inputs_df)

st.subheader("📌 Assumptions & Derived Values")
st.table(assumptions_df)

st.subheader("📌 Final Results")
st.table(results_df)

# ------------------------------------
# COST COMPARISON GRAPH
# ------------------------------------
st.subheader("Operating Cost Comparison 💰 (Rs/year)")
fig2, ax2 = plt.subplots()
ax2.bar(["Fuel Boiler", "Heat Pump"], [fuel_cost_year, hp_cost_year])
ax2.set_ylabel("Rs/year")
st.pyplot(fig2)
# CO2 COMPARISON GRAPH
# ------------------------------------
st.subheader("CO2 Comparison (kgs/year)")
fig2, ax2 = plt.subplots()
ax2.bar(["Fuel Boiler", "Heat Pump"], [co2_fuel_year, co2_hp_year])
ax2.set_ylabel("kgs/year")
st.pyplot(fig2)


# ------------------------------------
# EXPORT OPTIONS
# ------------------------------------
st.subheader("Download Output")

csv = results_df.to_csv(index=False).encode()
st.download_button("📄 Download CSV", csv, "heatpump_summary.csv")

buffer = BytesIO()
with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
    inputs_df.to_excel(writer, sheet_name="Inputs", index=False)
    assumptions_df.to_excel(writer, sheet_name="Assumptions", index=False)
    results_df.to_excel(writer, sheet_name="Results", index=False)
buffer.seek(0)

st.download_button("📘 Download Excel", buffer, "heatpump_summary.xlsx")

