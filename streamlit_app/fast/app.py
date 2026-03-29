import streamlit as st
import time
from datetime import datetime, timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="FlowFast Tracker", page_icon="💧", layout="centered")

# --- CUSTOM THEME (Applying your Palette) ---
# Steel Azure: #044389 | Dusty Olive: #676f54 | Pearl Beige: #e8dab2 
# Sky Reflection: #7cafc4 | Rosewood: #b56576
st.markdown("""
    <style>
    .stApp {
        background-color: white;
    }
    .main-header {
        color: #044389;
        text-align: center;
        font-family: 'Helvetica', sans-serif;
        margin-bottom: 20px;
    }
    .stProgress > div > div > div > div {
        background-color: #b56576;
    }
    /* Metric styling */
    [data-testid="stMetricValue"] {
        color: #044389;
    }
    </style>
    """, unsafe_allow_html=True)

# --- APP HEADER ---
st.markdown("<h1 class='main-header'>FlowFast Tracker</h1>", unsafe_allow_html=True)

# --- SIDEBAR SETTINGS ---
st.sidebar.header("Fast Settings")
fast_type = st.sidebar.selectbox("Select Fast Duration", [48, 72], format_func=lambda x: f"{x} Hour Fast")

# Input for start time
start_date = st.sidebar.date_input("Start Date", datetime.now())
start_time = st.sidebar.time_input("Start Time", datetime.now().time())

# Combine date and time
start_datetime = datetime.combine(start_date, start_time)
end_datetime = start_datetime + timedelta(hours=fast_type)

# --- CALCULATIONS ---
now = datetime.now()
total_seconds = fast_type * 3600
elapsed_seconds = (now - start_datetime).total_seconds()

# Logic for progress and time remaining
if elapsed_seconds < 0:
    st.warning("Start time is in the future!")
    hours_passed = 0
    remaining_hrs = fast_type
    progress_pct = 0.0
else:
    hours_passed = elapsed_seconds / 3600
    remaining_seconds = max(0, (end_datetime - now).total_seconds())
    remaining_hrs = remaining_seconds / 3600
    progress_pct = min(1.0, elapsed_seconds / total_seconds)

# --- PROGRESS & TIMER DISPLAY ---
col1, col2 = st.columns(2)
with col1:
    st.metric("Time Elapsed", f"{hours_passed:.1f} hrs")
with col2:
    st.metric("Time Remaining", f"{remaining_hrs:.1f} hrs")

st.progress(progress_pct)
st.write("---")

# --- DYNAMIC RECOMMENDATIONS (Your specific schedule) ---
st.subheader("💡 Action & Recommendations")

if hours_passed < 12:
    st.info("💧 Focus on hydration. Your body is currently in the post-absorptive phase.")
elif 12 <= hours_passed < 24:
    st.warning("⚡ **Electrolytes:** Take 1/2 packet now with water, and the remaining 1/2 later today.")
elif 24 <= hours_passed < 36:
    st.info("🌊 Keep sipping water. You are entering deep ketosis.")
elif 36 <= hours_passed < 48:
    st.error("⚡ **Electrolytes:** Take 1 full packet this morning and 1 full packet this afternoon.")
elif hours_passed >= 48:
    if fast_type == 48:
        st.success("🎉 **Fast Complete!** You can reintroduce solid foods normally.")
    else:
        st.warning("⚡ **Electrolytes:** Maintain mineral intake for the final 24-hour stretch.")

# --- BREAKING THE FAST TIPS ---
if remaining_hrs < 5 and remaining_hrs > 0:
    with st.expander("🥣 Preparing to Break Your Fast", expanded=True):
        if fast_type == 48:
            st.write("A moderate meal is fine. Focus on whole foods.")
        else:
            st.markdown("""
            **Gentle Reintroduction (72h protocol):**
            1. **Dinner (Now):** Easy on the stomach—bone broth, fermented veg, or a light soup.
            2. **Tomorrow Morning:** Introduce lean proteins and healthy fats slowly.
            *Avoid high-carb or sugary meals immediately to prevent insulin spikes.*
            """)

# --- FASTING STAGES (The Cycle) ---
st.write("---")
st.subheader("🔄 Biological Stage")

def get_stage_info(h):
    if h < 4:
        return "Feeding / Post-absorptive", "Insulin is elevated to manage blood sugar from your last meal.", "#7cafc4"
    elif h < 16:
        return "Early Fasting", "Liver breaks down glycogen for energy. Fat oxidation increases.", "#676f54"
    elif h < 18:
        return "Ketosis Begins", "Body switches to fat-burning; ketone production starts.", "#044389"
    elif h < 24:
        return "Autophagy Start", "Cellular cleanup begins. Recycling old proteins and lowering inflammation.", "#b56576"
    elif h < 72:
        return "Deep Ketosis & Autophagy", "Intensive cellular repair and HGH rise to support muscle preservation.", "#b56576"
    else:
        return "Immune Cell Regeneration", "White blood cells are being recycled and immune system is refreshing.", "#044389"

stage_name, stage_desc, stage_color = get_stage_info(hours_passed)

st.markdown(f"""
    <div style="background-color:{stage_color}; color:white; padding:20px; border-radius:10px; border-left: 10px solid #e8dab2;">
        <h3 style="margin:0;">{stage_name}</h3>
        <p style="margin:10px 0 0 0; font-size:1.1rem;">{stage_desc}</p>
    </div>
    """, unsafe_allow_html=True)

# --- REFRESH ---
st.write("")
if st.button("Update Clock"):
    st.rerun()
