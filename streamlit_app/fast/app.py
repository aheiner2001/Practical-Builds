import streamlit as st
import time
from datetime import datetime, timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="FlowFast Tracker", page_icon="💧", layout="centered")

# --- CUSTOM THEME (Applying your Palette) ---
# Steel Azure: #044389 | Dusty Olive: #676f54 | Pearl Beige: #e8dab2 
# Sky Reflection: #7cafc4 | Rosewood: #b56576
st.markdown(f"""
    <style>
    .stApp {{
        background-color: white;
    }}
    .main-header {{
        color: #044389;
        text-align: center;
        font-family: 'Helvetica';
    }}
    .stage-card {{
        background-color: #e8dab2;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #676f54;
        margin-bottom: 10px;
    }}
    .recommendation-box {{
        background-color: #7cafc4;
        color: white;
        padding: 15px;
        border-radius: 8px;
    }}
    .stProgress > div > div > div > div {{
        background-color: #b56576;
    }}
    </style>
    """, unsafe_allow_all_html=True)

# --- APP HEADER ---
st.markdown("<h1 class='main-header'>FlowFast Tracker</h1>", unsafe_allow_all_html=True)
st.write("---")

# --- SIDEBAR SETTINGS ---
st.sidebar.header("Fast Settings")
fast_type = st.sidebar.selectbox("Select Fast Duration", [48, 72], format_func=lambda x: f"{x} Hour Fast")
start_date = st.sidebar.date_input("Start Date", datetime.now())
start_time = st.sidebar.time_input("Start Time", datetime.now().time())

# Combine date and time
start_datetime = datetime.combine(start_date, start_time)
end_datetime = start_datetime + timedelta(hours=fast_type)

# --- CALCULATIONS ---
now = datetime.now()
total_seconds = fast_type * 3600
elapsed_seconds = (now - start_datetime).total_seconds()
remaining_seconds = max(0, (end_datetime - now).total_seconds())

# Progress calculation
progress_pct = min(1.0, max(0.0, elapsed_seconds / total_seconds))
hours_passed = elapsed_seconds / 3600

# --- PROGRESS & TIMER ---
col1, col2 = st.columns(2)
with col1:
    st.metric("Time Elapsed", f"{hours_passed:.1f} hrs")
with col2:
    remaining_hrs = remaining_seconds / 3600
    st.metric("Time Remaining", f"{remaining_hrs:.1f} hrs")

st.progress(progress_pct)

# --- DYNAMIC RECOMMENDATIONS (Based on your log) ---
st.subheader("💡 Recommendations & Milestones")

if hours_passed < 12:
    st.info("Drink plenty of plain water. Your body is still processing your last meal.")
elif 12 <= hours_passed < 24:
    st.warning("⚡ **Electrolyte Alert:** Take 1/2 packet of electrolytes with water now. Take the other 1/2 later today.")
elif 24 <= hours_passed < 48:
    st.warning("⚡ **Electrolyte Alert:** Deep Fasting. Take 1 full packet this morning and 1 full packet this afternoon.")
elif hours_passed >= 48:
    if fast_type == 48:
        st.success("🎉 Fast Complete! You can reintroduce solid foods normally.")
    else:
        st.warning("⚡ **Electrolyte Alert:** Maintain high mineral intake for the final 72-hour stretch.")

# --- BREAKING THE FAST TIPS ---
if remaining_hrs < 3:
    with st.expander("🥣 How to Break Your Fast", expanded=True):
        if fast_type == 48:
            st.write("You're likely okay to eat a regular meal, but start with something moderate.")
        else:
            st.markdown("""
            **Gentle Reintroduction Advised:**
            * **First:** Bone broth or light fermented foods (Kimchi/Kefir) for gut health.
            * **Next:** Lean protein (eggs/chicken).
            * **Avoid:** Heavy carbs or sugars immediately to prevent insulin spikes.
            """)

# --- FASTING STAGES (The Cycle) ---
st.write("---")
st.subheader("🔄 Current Biological Stage")

def get_stage(h):
    if h < 4: return "Feeding / Post-absorptive", "Insulin is managing blood sugar from your last meal.", "#7cafc4"
    if h < 16: return "Early Fasting", "Blood sugar drops, liver begins breaking down glycogen.", "#676f54"
    if h < 24: return "Ketosis Begins", "Glycogen stores low; body begins switching to fat-burning (ketones).", "#044389"
    if h < 72: return "Autophagy & Deep Ketosis", "Cellular cleanup (autophagy) and growth hormone increase.", "#b56576"
    return "Immune Regeneration", "Old immune cells are being recycled and regenerated.", "#044389"

stage_name, stage_desc, stage_color = get_stage(hours_passed)

st.markdown(f"""
    <div style="background-color:{stage_color}; color:white; padding:20px; border-radius:10px;">
        <h3>{stage_name}</h3>
        <p>{stage_desc}</p>
    </div>
    """, unsafe_allow_all_html=True)

# --- REFRESH BUTTON ---
if st.button("Refresh Timer"):
    st.rerun()
