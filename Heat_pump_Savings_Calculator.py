import streamlit as st

st.set_page_config(page_title="Heat Pump Savings Calculator", page_icon="🔥", layout="centered")

st.title("♨️ Heat Pump Savings & Payback Calculator")

st.header("Input Parameters")

# ---- Inputs ----
col1, col2 = st.columns(2)

with col1:
    heating_capacity = st.number_input("Required Heating Capacity (kW)", value=462.0)
    fuel_cost = st.number_input("Fuel Cost (Rs/kg)", value=9.5)
    calorific_value = st.number_input("Calorific Value of Biomass (kcal/kg)", value=2800)
    boiler_efficiency = st.number_input("Boiler Efficiency (%)", value=70.0)
    electricity_cost = st.number_input("Electricity Cost (Rs/unit)", value=5.5)

with col2:
    hours_per_day = st.number_input("Operating Hours per Day", value=24.0)
    days_per_year = st.number_input("Operating Days per Year", value=330)
    boiler_operator_cost = st.number_input("Boiler Operator Cost (Rs/day)", value=7500.0)
    connected_load_cost = st.number_input("Boiler Electrical Load Cost per Day (Rs)", value=1980.0)

# ---- Calculations ----
biomass_consumption=(heating_capacity*3600)/(calorific_value*4.184)
boiler_daily_cost = (biomass_consumption * fuel_cost * hours_per_day) + boiler_operator_cost + connected_load_cost
boiler_annual_cost = boiler_daily_cost * days_per_year

# Heat pump parameters
st.header("Heat Pump Details")
hp_capacity = st.number_input("Heat Pump Capacity (kW)", value=462.0)
hp_power = st.number_input("Heat Pump Power Consumption (kW)", value=271.8)
hp_cooling_cap = st.number_input("Heat Pump Cooling Capacity (kW)", value=190.2)

hp_annual_cost = hp_power * 24 * days_per_year * electricity_cost
heating_savings = boiler_annual_cost - hp_annual_cost

# Cooling benefit
cooling_benefit = hp_cooling_cap * 24 * days_per_year * electricity_cost * 0.8 / 10  # simplified assumption

annual_savings = heating_savings + cooling_benefit
daily_savings = annual_savings / days_per_year

# ---- Results ----
st.header("💰 Results")

st.write(f"**Boiler Annual Cost:** ₹{boiler_annual_cost:,.2f}")
st.write(f"**Heat Pump Annual Cost:** ₹{hp_annual_cost:,.2f}")
st.write(f"**Heating Savings:** ₹{heating_savings:,.2f}")
st.write(f"**Cooling Benefit:** ₹{cooling_benefit:,.2f}")
st.success(f"**Total Annual Savings:** ₹{annual_savings:,.2f}")
st.info(f"**Savings per Day:** ₹{daily_savings:,.2f}")
