import streamlit as st
import pandas as pd
import numpy as np
import datetime
from io import BytesIO

# Set page configuration
st.set_page_config(
    page_title="ProFit: Ultimate Nutrition & Fitness Tracker",
    page_icon="💪",
    layout="wide"
)

# Initialize Session State for data persistence
if 'meals' not in st.session_state:
    st.session_state.meals = pd.DataFrame(columns=['Meal Type', 'Food Item', 'Calories (kcal)', 'Protein (g)', 'Carbs (g)', 'Fats (g)'])

if 'workouts' not in st.session_state:
    st.session_state.workouts = pd.DataFrame(columns=['Activity', 'Duration (min)', 'Intensity', 'Calories Burned (kcal)'])

if 'water' not in st.session_state:
    st.session_state.water = 0.0

# ----------------------------------------------------------------------------------
# APP HEADER
# ----------------------------------------------------------------------------------
st.title("💪 ProFit: Personal Nutrition & Fitness Analytics")
st.markdown("Track macros, log workouts, monitor your hydration, and export your performance metrics instantly.")

# ----------------------------------------------------------------------------------
# SIDEBAR: METABOLIC CALCULATOR (BMR / TDEE)
# ----------------------------------------------------------------------------------
st.sidebar.header("👤 Profile & Metabolic Calculator")
gender = st.sidebar.radio("Gender", ["Male", "Female"])
age = st.sidebar.number_input("Age (years)", min_value=10, max_value=100, value=25)
weight = st.sidebar.number_input("Weight (kg)", min_value=30.0, max_value=200.0, value=70.0)
height = st.sidebar.number_input("Height (cm)", min_value=100.0, max_value=250.0, value=175.0)

activity_level = st.sidebar.selectbox(
    "Activity Level",
    [
        "Sedentary (little or no exercise)",
        "Lightly active (light exercise 1-3 days/week)",
        "Moderately active (moderate exercise 3-5 days/week)",
        "Very active (hard exercise 6-7 days/week)"
    ]
)

# Calculate BMR using the Mifflin-St Jeor Equation
if gender == "Male":
    bmr = 10 * weight + 6.25 * height - 5 * age + 5
else:
    bmr = 10 * weight + 6.25 * height - 5 * age - 161

# Map activity multipliers using numpy arrays for processing efficiency
multipliers = np.array([1.2, 1.375, 1.55, 1.725])
activity_idx = ["Sedentary", "Lightly", "Moderately", "Very"].index(activity_level.split()[0])
tdee = int(bmr * multipliers[activity_idx])

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Daily Target Goals")
target_calories = st.sidebar.number_input("Target Calorie Intake (kcal)", value=tdee, step=50)
target_water = st.sidebar.number_input("Target Water Intake (Liters)", value=3.0, step=0.5)

# ----------------------------------------------------------------------------------
# MAIN DASHBOARD: 3-COLUMN LAYOUT FOR ENTRY
# ----------------------------------------------------------------------------------
col1, col2, col3 = st.columns(3)

# Column 1: Nutrition Logging
with col1:
    st.header("🍳 Log Nutrition")
    with st.form("nutrition_form", clear_on_submit=True):
        meal_type = st.selectbox("Meal Category", ["Breakfast", "Lunch", "Dinner", "Snack"])
        food_item = st.text_input("Food Item Name", placeholder="e.g., Grilled Chicken Rice Bowl")
        calories = st.number_input("Calories (kcal)", min_value=0, value=0)
        protein = st.number_input("Protein (g)", min_value=0.0, value=0.0, step=1.0)
        carbs = st.number_input("Carbs (g)", min_value=0.0, value=0.0, step=1.0)
        fats = st.number_input("Fats (g)", min_value=0.0, value=0.0, step=1.0)
        
        submitted_meal = st.form_submit_submit = st.form_submit_button("Add Food Item")
        if submitted_meal and food_item != "":
            new_meal = pd.DataFrame([[meal_type, food_item, calories, protein, carbs, fats]], columns=st.session_state.meals.columns)
            st.session_state.meals = pd.concat([st.session_state.meals, new_meal], ignore_index=True)
            st.success(f"Added {food_item} successfully!")

# Column 2: Workout Logging
with col2:
    st.header("🏃‍♂️ Log Exercise")
    with st.form("workout_form", clear_on_submit=True):
        activity = st.text_input("Activity / Exercise", placeholder="e.g., Running, Weightlifting")
        duration = st.number_input("Duration (minutes)", min_value=1, value=30)
        intensity = st.selectbox("Intensity Level", ["Low", "Moderate", "High"])
        
        # Estimate calorie burn using an analytical MET estimate array
        met_multiplier = {"Low": 3.5, "Moderate": 7.0, "High": 10.5}[intensity]
        calc_burned = int((met_multiplier * 3.5 * weight / 200) * duration)
        
        custom_burn = st.number_input("Estimated Calories Burned (Leave 0 to auto-calculate)", min_value=0, value=0)
        final_burn = custom_burn if custom_burn > 0 else calc_burned
        
        submitted_workout = st.form_submit_button("Add Activity Log")
        if submitted_workout and activity != "":
            new_workout = pd.DataFrame([[activity, duration, intensity, final_burn]], columns=st.session_state.workouts.columns)
            st.session_state.workouts = pd.concat([st.session_state.workouts, new_workout], ignore_index=True)
            st.success(f"Log updated: {activity} saved!")

# Column 3: Hydration Metrics
with col3:
    st.header("💧 Tracker Hydration")
    st.write(f"**Current Intake:** {st.session_state.water:.2f} L / {target_water:.2f} L")
    
    water_progress = min(st.session_state.water / max(target_water, 1.0), 1.0)
    st.progress(water_progress)
    
    h_col1, h_col2 = st.columns(2)
    with h_col1:
        if st.button("➕ Add 250ml (0.25L)"):
            st.session_state.water += 0.25
            st.rerun()
    with h_col2:
        if st.button("➕ Add 500ml (0.50L)"):
            st.session_state.water += 0.50
            st.rerun()
            
    if st.button("🔄 Reset Hydration Counter"):
        st.session_state.water = 0.0
        st.rerun()

# ----------------------------------------------------------------------------------
# VISUAL ANALYTICS ENGINE & MACRO BREAKDOWNS
# ----------------------------------------------------------------------------------
st.markdown("---")
st.header("📊 Today's Aggregated Analytics Summary")

# Data processing using pandas and numpy vectors
total_calories_consumed = int(st.session_state.meals['Calories (kcal)'].sum())
total_protein = np.round(st.session_state.meals['Protein (g)'].sum(), 1)
total_carbs = np.round(st.session_state.meals['Carbs (g)'].sum(), 1)
total_fats = np.round(st.session_state.meals['Fats (g)'].sum(), 1)
total_calories_burned = int(st.session_state.workouts['Calories Burned (kcal)'].sum())

net_calories = total_calories_consumed - total_calories_burned

# Dynamic KPI Cards
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Calories Consumed", f"{total_calories_consumed} kcal", f"Goal: {target_calories} kcal")
kpi2.metric("Calories Burned", f"{total_calories_burned} kcal")
kpi3.metric("Net Energy Balance", f"{net_calories} kcal", delta=f"{net_calories - target_calories} vs Goal", delta_color="inverse")
kpi4.metric("Hydration Total", f"{st.session_state.water:.2f} L", f"Goal: {target_water:.2f} L")

# Display Active Sub-Tables
view1, view2 = st.columns(2)
with view1:
    st.subheader("🍽️ Meal Logs")
    if not st.session_state.meals.empty:
        st.dataframe(st.session_state.meals, use_container_width=True)
    else:
        st.info("No meals logged yet today.")

with view2:
    st.subheader("🏋️ Workout History Log")
    if not st.session_state.workouts.empty:
        st.dataframe(st.session_state.workouts, use_container_width=True)
    else:
        st.info("No workouts registered yet today.")

# Macro Chart Representation (Bar chart layout calculated via pandas series transformations)
if total_protein > 0 or total_carbs > 0 or total_fats > 0:
    st.subheader("🍗 Macronutrient Gram Split Distribution")
    macro_df = pd.DataFrame({
        'Macro': ['Protein (g)', 'Carbohydrates (g)', 'Fats (g)'],
        'Grams': [total_protein, total_carbs, total_fats]
    }).set_index('Macro')
    st.bar_chart(macro_df)

# ----------------------------------------------------------------------------------
# REPORT COMPILATION & GENERATION FOR EXPORT
# ----------------------------------------------------------------------------------
st.markdown("---")
st.header("📋 Export Metric Report")

def generate_csv_report():
    # Construct unified plain-text summary and stack underlying DataFrames
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Sheet 1: High Level Summary Overview
        summary_df = pd.DataFrame([{
            "Report Date": datetime.date.today(),
            "Calculated BMR (kcal)": bmr,
            "TDEE Base Baseline": tdee,
            "Target Calories Set": target_calories,
            "Total Consumed": total_calories_consumed,
            "Total Burned": total_calories_burned,
            "Net Energy Balance": net_calories,
            "Water Intake (L)": st.session_state.water
        }])
        summary_df.to_excel(writer, sheet_name="Daily Summary", index=False)
        st.session_state.meals.to_excel(writer, sheet_name="Diet Log", index=False)
        st.session_state.workouts.to_excel(writer, sheet_name="Workout Log", index=False)
    return buffer.getvalue()

st.write("Generate and download your structural data log mapping out all current records.")
try:
    report_data = generate_csv_report()
    st.download_button(
        label="📥 Download Comprehensive Excel Report",
        data=report_data,
        file_name=f"Fitness_Nutrition_Report_{datetime.date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
except Exception as e:
    st.warning("Ensure all fields or structural elements are ready before clicking download.")
