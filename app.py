import streamlit as st
import pandas as pd
import numpy as np
import datetime

# --- APP CONFIGURATION ---
st.set_page_config(
    page_title="Pulse & Plate | Fitness Tracker",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM STYLING ---
st.markdown("""
    <style>
    .main-title { font-size: 42px; font-weight: 700; color: #FF4B4B; margin-bottom: 20px; }
    .metric-card { background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
# Using Pandas dataframes inside session state to persistently log data during the session
if 'food_log' not in st.session_state:
    st.session_state.food_log = pd.DataFrame(columns=['Time', 'Item', 'Calories (kcal)', 'Protein (g)', 'Carbs (g)', 'Fats (g)'])

if 'workout_log' not in st.session_state:
    st.session_state.workout_log = pd.DataFrame(columns=['Time', 'Activity', 'Duration (min)', 'Intensity', 'Calories Burned (kcal)'])

# --- SIDEBAR: USER PROFILE & BIOMETRICS ---
st.sidebar.header("👤 User Profile & Goals")

name = st.sidebar.text_input("Name", value="Athlete")
age = st.sidebar.number_input("Age", min_value=1, max_value=120, value=25)
gender = st.sidebar.radio("Gender", ["Male", "Female"])
weight = st.sidebar.number_input("Weight (kg)", min_value=10.0, max_value=300.0, value=70.0, step=0.1)
height = st.sidebar.number_input("Height (cm)", min_value=50.0, max_value=250.0, value=175.0, step=0.1)

activity_level = st.sidebar.selectbox(
    "Activity Level",
    ["Sedentary (Little to no exercise)", 
     "Lightly Active (1-3 days/week)", 
     "Moderately Active (3-5 days/week)", 
     "Very Active (6-7 days/week)"]
)

# --- ALGORITHMIC CALCULATIONS (Numpy & Math) ---
# BMI Calculation: weight (kg) / height (m)^2
bmi = np.round(weight / ((height / 100) ** 2), 1)

# BMR Calculation via Harris-Benedict Equation
if gender == "Male":
    bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
else:
    bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)

# Activity multipliers using Numpy conditional arrays
multipliers = [1.2, 1.375, 1.55, 1.725]
levels = ["Sedentary (Little to no exercise)", "Lightly Active (1-3 days/week)", "Moderately Active (3-5 days/week)", "Very Active (6-7 days/week)"]
chosen_multiplier = np.select([activity_level == lvl for lvl in levels], multipliers, default=1.2)
tdee = np.round(bmr * chosen_multiplier, 0)

# --- MAIN INTERFACE ---
st.markdown(f"<div class='main-title'>⚡ Pulse & Plate</div>", unsafe_allow_html=True)
st.subheader(f"Welcome back, {name}! tracking your journey to peak health.")

# --- ROW 1: BIOMETRIC DASHBOARD ---
st.markdown("### 📊 Today's Baseline Biometrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="BMI Score", value=bmi, delta="Healthy" if 18.5 <= bmi <= 24.9 else "Out of Range", delta_color="normal" if 18.5 <= bmi <= 24.9 else "inverse")
with col2:
    st.metric(label="Basal Metabolic Rate (BMR)", value=f"{int(bmr)} kcal")
with col3:
    st.metric(label="Daily Energy Expenditure (TDEE)", value=f"{int(tdee)} kcal")
with col4:
    # Calculate balance dynamically using Pandas columns
    total_consumed = st.session_state.food_log['Calories (kcal)'].sum()
    total_burned = st.session_state.workout_log['Calories Burned (kcal)'].sum()
    net_calories = total_consumed - total_burned
    st.metric(label="Net Calories Today", value=f"{int(net_calories)} kcal", delta=f"{int(net_calories - tdee)} vs Budget")

st.markdown("---")

# --- ROW 2: INTERACTIVE LOGGING ENGINES ---
tab1, tab2, tab3 = st.tabs(["🍏 Nutrition Tracker", "🏋️ Fitness & Workouts", "📈 Summary Analytics"])

with tab1:
    st.subheader("Log Meal & Macronutrients")
    c1, c2, c3 = st.columns([2, 1, 1])
    
    with c1:
        food_item = st.text_input("What did you eat?", placeholder="e.g., Grilled Chicken Salad")
    with c2:
        meal_time = st.time_input("Time of Meal", datetime.time(12, 0))
    with c3:
        cal_input = st.number_input("Calories (kcal)", min_value=0, value=350, step=10)
        
    p_col, c_col, f_col = st.columns(3)
    with p_col:
        protein = st.number_input("Protein (g)", min_value=0.0, value=25.0, step=1.0)
    with c_col:
        carbs = st.number_input("Carbs (g)", min_value=0.0, value=30.0, step=1.0)
    with f_col:
        fats = st.number_input("Fats (g)", min_value=0.0, value=10.0, step=1.0)
        
    if st.button("➕ Add Food Entry", type="primary"):
        new_food = pd.DataFrame([{
            'Time': meal_time.strftime("%H:%M"),
            'Item': food_item if food_item else "Unspecified Meal",
            'Calories (kcal)': cal_input,
            'Protein (g)': protein,
            'Carbs (g)': carbs,
            'Fats (g)': fats
        }])
        # Append data to the stateful DataFrame
        st.session_state.food_log = pd.concat([st.session_state.food_log, new_food], ignore_index=True)
        st.success(f"Logged {food_item} successfully!")
        st.rerun()

    # Dynamic Data Display
    st.markdown("#### Today's Intake History")
    if not st.session_state.food_log.empty:
        st.dataframe(st.session_state.food_log, use_container_width=True)
        if st.button("🗑️ Clear Food Log"):
            st.session_state.food_log = pd.DataFrame(columns=['Time', 'Item', 'Calories (kcal)', 'Protein (g)', 'Carbs (g)', 'Fats (g)'])
            st.rerun()
    else:
        st.info("No food logged yet today. Feed your body!")

with tab2:
    st.subheader("Log Physical Activity")
    wc1, wc2, wc3 = st.columns([2, 1, 1])
    
    with wc1:
        activity = st.selectbox("Workout Type", ["Running", "Weightlifting", "Cycling", "Swimming", "Yoga", "Walking", "Other HIIT"])
    with wc2:
        duration = st.number_input("Duration (minutes)", min_value=1, value=30, step=5)
    with wc3:
        intensity = st.select_slider("Intensity Level", options=["Low", "Medium", "High"])
        
    # Algorithmic calorie estimation per minute based on intensity using Numpy maps
    intensity_multiplier = np.select([intensity == "Low", intensity == "Medium", intensity == "High"], [5, 8, 12.5])
    estimated_burn = np.round(duration * intensity_multiplier, 0)
    
    st.info(f"🔥 Estimated energy burn for this session: **{int(estimated_burn)} kcal**")
    
    if st.button("🏋️ Record Session", type="primary"):
        new_workout = pd.DataFrame([{
            'Time': datetime.datetime.now().strftime("%H:%M"),
            'Activity': activity,
            'Duration (min)': duration,
            'Intensity': intensity,
            'Calories Burned (kcal)': estimated_burn
        }])
        st.session_state.workout_log = pd.concat([st.session_state.workout_log, new_workout], ignore_index=True)
        st.success(f"Recorded your {activity} session!")
        st.rerun()
        
    st.markdown("#### Today's Workout History")
    if not st.session_state.workout_log.empty:
        st.dataframe(st.session_state.workout_log, use_container_width=True)
        if st.button("🗑️ Clear Workout Log"):
            st.session_state.workout_log = pd.DataFrame(columns=['Time', 'Activity', 'Duration (min)', 'Intensity', 'Calories Burned (kcal)'])
            st.rerun()
    else:
        st.info("No workouts recorded yet. Let's get moving!")

with tab3:
    st.subheader("📊 Performance Analytics")
    
    if not st.session_state.food_log.empty or not st.session_state.workout_log.empty:
        col_metrics_1, col_metrics_2 = st.columns(2)
        
        with col_metrics_1:
            st.markdown("#### Macronutrient Distribution Breakdown")
            total_p = st.session_state.food_log['Protein (g)'].sum()
            total_c = st.session_state.food_log['Carbs (g)'].sum()
            total_f = st.session_state.food_log['Fats (g)'].sum()
            
            # Formulate macro metrics chart via Pandas
            macro_df = pd.DataFrame({
                'Macronutrient': ['Protein', 'Carbs', 'Fats'],
                'Grams Consumed': [total_p, total_c, total_f]
            })
            st.bar_chart(data=macro_df, x='Macronutrient', y='Grams Consumed', color="#FF4B4B")
            
        with col_metrics_2:
            st.markdown("#### Calorie Budget Tracking")
            cal_summary = pd.DataFrame({
                'Metric': ['Target TDEE', 'Consumed', 'Burned'],
                'Calories (kcal)': [tdee, total_consumed, total_burned]
            })
            st.bar_chart(data=cal_summary, x='Metric', y='Calories (kcal)', color="#29B5E8")
            
        # Target suggestions engine
        st.markdown("#### 💡 AI Architecture Recommendations")
        if total_consumed > tdee:
            st.warning("⚠️ You are currently in a caloric surplus. Ideal for muscle building, but reduce intake slightly if your goal is fat loss.")
        elif total_consumed < bmr and total_consumed > 0:
            st.error("🚨 Warning: Your caloric intake is below your basic BMR. Ensure you consume enough energy to power vital organ functions safely.")
        else:
            st.success("💪 Exceptional work! Your caloric balance is tracking within optimized ranges for sustainable metabolic health.")
    else:
        st.info("Log your meals and movements in the previous tabs to activate deep analytics reporting.")

