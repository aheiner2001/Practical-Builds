import streamlit as st
import time
from datetime import datetime, timedelta

# --- 1. INITIALIZE SESSION STATE ---
if 'start_time_obj' not in st.session_state:
    st.session_state.start_time_obj = None
if 'fast_target_h' not in st.session_state:
    st.session_state.fast_target_h = 48 

# --- PAGE CONFIG ---
st.set_page_config(page_title="FlowFast Tracker", page_icon="💧", layout="wide")

# --- 2. CUSTOM THEME ---
st.markdown("""
    <style>
    .stApp { background-color: white; }
    .main-header { color: #044389; text-align: center; font-family: sans-serif; margin-bottom: 20px; }
    
    .dashboard-container {
        display: grid;
        grid-template-areas: "progress progress" "stages steps" "timeline timeline";
        grid-template-columns: 1fr 2fr;
        grid-gap: 30px;
    }

    /* Progress Bar */
    .p-bar-bg { height: 18px; width: 100%; background-color: #e8dab2; border-radius: 10px; position: relative; overflow: hidden; }
    .p-bar-fill { height: 100%; border-radius: 10px; transition: width 0.3s ease-in-out; }

    /* Circle & Stopwatch */
    .progress-circle { 
        width: 200px; height: 200px; border-radius: 50%; display: flex; 
        justify-content: center; align-items: center; position: relative;
    }
    .progress-circle::after {
        content: ""; position: absolute; width: 170px; height: 170px; 
        background-color: white; border-radius: 50%;
    }
    .stopwatch-display { 
        z-index: 10; text-align: center; font-family: 'Courier New', Courier, monospace; 
    }
    .time-digits { font-size: 2.2rem; font-weight: bold; color: #044389; display: block; }
    .time-label { font-size: 0.8rem; color: #b56576; letter-spacing: 2px; text-transform: uppercase; }

    /* Stepper */
    .stepper { display: flex; justify-content: space-between; align-items: center; width: 100%; position: relative; padding: 20px 0; }
    .step-line { position: absolute; height: 4px; background: #e8dab2; width: 100%; top: 50%; z-index: 1; }
    .step { 
        width: 45px; height: 45px; border-radius: 50%; display: flex; 
        justify-content: center; align-items: center; background: #e8dab2; 
        color: white; z-index: 2; font-weight: bold;
    }
    .active-step { background: #0081ff; box-shadow: 0 0 15px rgba(0,129,255,0.5); transform: scale(1.1); }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR CONTROLS ---
st.sidebar.header("Fast Setup")
selected_h = st.sidebar.select_slider("Select Target (Hours)", options=[48, 72, 120])

if st.sidebar.button("▶ Start Fast"):
    st.session_state.start_time_obj = datetime.now()
    st.session_state.fast_target_h = selected_h
    st.rerun()

if st.sidebar.button("⏹ Reset"):
    st.session_state.start_time_obj = None
    st.rerun()

# --- 4. STOPWATCH CALCULATIONS ---
is_active = st.session_state.start_time_obj is not None
hours_passed = 0
progress_pct = 0
target_h = st.session_state.fast_target_h
stopwatch_str = "00:00:00"

if is_active:
    diff = datetime.now() - st.session_state.start_time_obj
    total_seconds = int(diff.total_seconds())
    
    # Format as HH:MM:SS
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    stopwatch_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    hours_passed = total_seconds / 3600
    progress_pct = min(100.0, (hours_passed / target_h) * 100)

# --- 5. RENDER UI ---
st.markdown("<h1 class='main-header'>FlowFast Tracker</h1>", unsafe_allow_html=True)
st.markdown("<div class='dashboard-container'>", unsafe_allow_html=True)

# TOP PROGRESS BAR
st.markdown(f"""
    <div style='grid-area: progress;'>
        <div class='p-bar-bg'>
            <div class='p-bar-fill' style='width:{progress_pct}%; background:#0081ff;'></div>
        </div>
    </div>
""", unsafe_allow_html=True)

# LEFT CIRCLE & STOPWATCH
conic = f"conic-gradient(#0081ff {progress_pct}%, #e8dab2 {progress_pct}%)"
st.markdown(f"""
    <div style='grid-area: stages; display:flex; flex-direction:column; align-items:center;'>
        <div class='progress-circle' style='background:{conic};'>
            <div class='stopwatch-display'>
                <span class='time-digits'>{stopwatch_str}</span>
                <span class='time-label'>Elapsed</span>
            </div>
        </div>
        <div style='margin-top:15px; font-weight:bold; color:#676f54;'>{progress_pct:.1f}% Toward {target_h}H Goal</div>
    </div>
""", unsafe_allow_html=True)

# RIGHT STEPPER & TARGET
steps_html = ""
for h in [48, 72, 120]:
    status_class = "active-step" if h == target_h else ""
    steps_html += f"<div class='step {status_class}'>{h}</div>"

st.markdown(f"""
    <div style='grid-area: steps;'>
        <div style='font-weight:bold; margin-bottom:10px; color:#044389;'>TARGET MILESTONE</div>
        <div class='stepper'>
            <div class='step-line'></div>
            {steps_html}
        </div>
        <div style='background:#7cafc4; color:white; padding:15px; border-radius:10px; margin-top:20px;'>
            <strong>Fasting Stage:</strong><br>
            { "Autophagy" if hours_passed > 16 else "Ketosis" if hours_passed > 12 else "Sugar Burning" }
        </div>
    </div>
""", unsafe_allow_html=True)

# BOTTOM RECOMMENDATIONS
st.markdown("<div style='grid-area: timeline;'>", unsafe_allow_html=True)
st.write("---")
if is_active:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("⚡ Electrolytes")
        if hours_passed < 12: st.info("Drink plain water for now.")
        elif 12 <= hours_passed < 36: st.warning("Take 1/2 pack now, 1/2 later.")
        else: st.error("Take 1 FULL pack now, 1 FULL pack later.")
    with col2:
        st.subheader("🥣 Refeeding")
        if (target_h - hours_passed) < 3: st.success("Prepare bone broth and easy proteins!")
        else: st.info("Stay focused. Too early for food prep.")
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# --- 6. TICK THE CLOCK ---
if is_active and progress_pct < 100:
    time.sleep(1) # Refresh every second for the stopwatch effect
    st.rerun()
