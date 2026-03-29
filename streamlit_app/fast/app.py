import streamlit as st
import time
from datetime import datetime, timedelta

# --- 1. INITIALIZE SESSION STATE (The Fix) ---
# This must happen before any other logic to prevent AttributeErrors
if 'start_time_obj' not in st.session_state:
    st.session_state.start_time_obj = None
if 'fast_target_h' not in st.session_state:
    st.session_state.fast_target_h = 48  # Default starting target

# --- PAGE CONFIG ---
st.set_page_config(page_title="FlowFast Tracker", page_icon="💧", layout="wide")

# --- 2. CUSTOM THEME (Applying your Palette) ---
# Steel Azure: #044389 | Dusty Olive: #676f54 | Pearl Beige: #e8dab2 
# Sky Reflection: #7cafc4 | Rosewood: #b56576 | Image Blue: #0081ff
st.markdown("""
    <style>
    .stApp { background-color: white; }
    .main-header { color: #044389; text-align: center; font-family: sans-serif; margin-bottom: 30px; }
    
    /* Main Dashboard Layout */
    .dashboard-container {
        display: grid;
        grid-template-areas: 
            "progress progress"
            "stages steps"
            "timeline timeline";
        grid-template-columns: 1fr 2fr;
        grid-gap: 30px;
    }

    /* Progress Bar (Top) */
    .p-bar-bg { height: 20px; width: 100%; background-color: #e8dab2; border-radius: 10px; position: relative; overflow: hidden; }
    .p-bar-fill { height: 100%; border-radius: 10px; transition: width 0.8s ease-in-out; }

    /* Circular Stage (Left) */
    .progress-circle { 
        width: 180px; height: 180px; border-radius: 50%; display: flex; 
        justify-content: center; align-items: center; position: relative;
    }
    .progress-circle::after {
        content: ""; position: absolute; width: 150px; height: 150px; 
        background-color: white; border-radius: 50%;
    }
    .progress-pct { z-index: 10; font-size: 3rem; font-weight: bold; color: #044389; font-family: sans-serif; }
    .stage-label { font-weight: bold; color: #676f54; margin-top: 15px; font-size: 1.2rem; }

    /* Stepper (Right) */
    .stepper { display: flex; justify-content: space-between; align-items: center; width: 100%; position: relative; padding: 20px 0; }
    .step-line { position: absolute; height: 4px; background: #e8dab2; width: 100%; top: 50%; z-index: 1; }
    .step { 
        width: 45px; height: 45px; border-radius: 50%; display: flex; 
        justify-content: center; align-items: center; background: #e8dab2; 
        color: white; z-index: 2; font-weight: bold; font-size: 0.9rem;
    }
    .active-step { background: #0081ff; box-shadow: 0 0 15px rgba(0,129,255,0.5); transform: scale(1.1); }
    .finished-step { background: #044389; }

    /* Recommendation Cards */
    .rec-card { background: #7cafc4; color: white; padding: 15px; border-radius: 10px; margin-top: 10px; border-left: 5px solid #044389; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CONFIG DATA ---
FAST_CHOICES = [48, 72, 120]
PALETTE_BLUE = "#0081ff"
PALETTE_ROSEWOOD = "#b56576"

# --- 4. SIDEBAR CONTROLS ---
st.sidebar.header("Fast Setup")
selected_h = st.sidebar.select_slider("Select Target (Hours)", options=FAST_CHOICES)

if st.sidebar.button("▶ Start Fast"):
    st.session_state.start_time_obj = datetime.now()
    st.session_state.fast_target_h = selected_h
    st.rerun()

if st.sidebar.button("⏹ Reset"):
    st.session_state.start_time_obj = None
    st.rerun()

# --- 5. CALCULATIONS ---
is_active = st.session_state.start_time_obj is not None
hours_passed = 0
progress_pct = 0
target_h = st.session_state.fast_target_h

if is_active:
    elapsed = (datetime.now() - st.session_state.start_time_obj).total_seconds()
    hours_passed = elapsed / 3600
    progress_pct = min(100.0, (hours_passed / target_h) * 100)

# --- 6. RENDER UI ---
st.markdown("<h1 class='main-header'>FlowFast Tracker</h1>", unsafe_allow_html=True)
st.markdown("<div class='dashboard-container'>", unsafe_allow_html=True)

# TOP PROGRESS BAR
st.markdown(f"""
    <div style='grid-area: progress;'>
        <div class='p-bar-bg'>
            <div class='p-bar-fill' style='width:{progress_pct}%; background:{PALETTE_ROSEWOOD if progress_pct > 80 else PALETTE_BLUE};'></div>
        </div>
    </div>
""", unsafe_allow_html=True)

# LEFT CIRCLE STAGE
conic = f"conic-gradient({PALETTE_BLUE} {progress_pct}%, #e8dab2 {progress_pct}%)"
st.markdown(f"""
    <div style='grid-area: stages; display:flex; flex-direction:column; align-items:center;'>
        <div class='progress-circle' style='background:{conic};'>
            <div class='progress-pct'>{progress_pct:.0f}%</div>
        </div>
        <div class='stage-label'>Current Progress</div>
        <div style='color:#aab0c4;'>{hours_passed:.1f} / {target_h} Hours</div>
    </div>
""", unsafe_allow_html=True)

# RIGHT STEPPER
steps_html = ""
for h in FAST_CHOICES:
    if h < target_h:
        status_class = "finished-step"
    elif h == target_h:
        status_class = "active-step"
    else:
        status_class = ""
    steps_html += f"<div class='step {status_class}'>{h}H</div>"

st.markdown(f"""
    <div style='grid-area: steps;'>
        <div style='font-weight:bold; margin-bottom:10px; color:#044389;'>TARGET MILESTONE</div>
        <div class='stepper'>
            <div class='step-line'></div>
            {steps_html}
        </div>
        <div class='rec-card'>
            <strong>Current Goal:</strong> {target_h} Hour Fast<br>
            <strong>Status:</strong> {'Active' if is_active else 'Paused'}
        </div>
    </div>
""", unsafe_allow_html=True)

# BOTTOM TIMELINE (Electrolytes & Biological Stages)
st.markdown("<div style='grid-area: timeline;'>", unsafe_allow_html=True)
st.write("---")
st.subheader("📋 Recommendations & Biological Cycle")

# Electrolyte Logic
if is_active:
    if 12 <= hours_passed < 24:
        st.warning("⚡ **Electrolytes:** Take 1/2 packet now. Take the second 1/2 later today.")
    elif 36 <= hours_passed < 48:
        st.error("⚡ **Electrolytes:** Take 1 FULL packet this morning and 1 FULL packet this afternoon.")
    
    # Biological Stage Logic
    if hours_passed < 4:
        st.info("🔄 **Post-absorptive:** Body is processing your last meal.")
    elif hours_passed < 16:
        st.info("🔄 **Early Fasting:** Liver is breaking down glycogen for energy.")
    elif hours_passed < 24:
        st.info("🔄 **Ketosis:** Body is switching to fat-burning mode.")
    elif hours_passed < 72:
        st.info("🔄 **Autophagy:** Cellular repair and deep fat-burning is occurring.")
    
    # Refeeding Logic (If near end)
    if (target_h - hours_passed) < 3 and (target_h - hours_passed) > 0:
        if target_h == 72:
            st.success("🥣 **Refeeding Tip:** Start with bone broth or fermented foods. Eat protein slowly.")
        else:
            st.success("🥣 **Refeeding Tip:** You're clear to eat, but keep it whole-food based.")

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# Automatic Rerun for the timer
if is_active and progress_pct < 100:
    time.sleep(10) # Update every 10 seconds to save resources
    st.rerun()
