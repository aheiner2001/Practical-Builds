import streamlit as st
import time
from datetime import datetime, timedelta
import collections

# --- PAGE CONFIG ---
st.set_page_config(page_title="FlowFast Tracker", page_icon="💧", layout="wide")

# Initialize Session State
if 'start_time_obj' not in st.session_state:
    st.session_state.start_time_obj = None

# --- CUSTOM THEME (Applying Palette based on image style) ---
# Image primary: #0081ff (Steel Azure/Sky Reflection blend) | Gray: #e1e7ec (Beige/Gray)
# Accent: #b56576 (Rosewood)
st.markdown("""
    <style>
    .stApp {
        background-color: #f7fbff;
    }
    .main-header {
        color: #044389;
        text-align: center;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: 300;
        margin-bottom: 30px;
    }
    
    /* Overall Layout Containment */
    .dashboard-container {
        display: grid;
        grid-template-areas: 
            "progress progress"
            "stages steps"
            "timeline timeline";
        grid-template-columns: 1fr 2fr;
        grid-gap: 30px;
        margin-top: 20px;
    }

    /* -- 1. Main Progress Bar (TOP) -- */
    .p-bar-container {
        grid-area: progress;
        background: transparent;
        height: 60px;
        position: relative;
    }
    .p-bar-bg {
        position: absolute;
        top: 20px;
        left: 0;
        height: 20px;
        width: 100%;
        background-color: #e1e7ec; /* Beige/Light Gray */
        border-radius: 10px;
    }
    .p-bar-fill {
        position: absolute;
        top: 20px;
        left: 0;
        height: 20px;
        border-radius: 10px;
        transition: width 0.5s ease-in-out;
    }

    /* -- 2. Fasting Stages Circle (LEFT) -- */
    .stage-card {
        grid-area: stages;
        padding: 10px;
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    .progress-circle {
        position: relative;
        width: 160px;
        height: 160px;
        border-radius: 50%;
        background-color: #e1e7ec; /* Beige/Gray */
        display: flex;
        justify-content: center;
        align-items: center;
        overflow: hidden;
    }
    .progress-circle::after {
        content: "";
        position: absolute;
        width: 130px;
        height: 130px;
        background-color: #f7fbff;
        border-radius: 50%;
    }
    .progress-content {
        position: relative;
        z-index: 10;
        color: #044389; /* Steel Azure */
    }
    .progress-pct {
        font-size: 2.8rem;
        font-weight: 700;
        font-family: sans-serif;
    }
    .stage-name {
        margin-top: 5px;
        font-weight: bold;
        color: #676f54; /* Dusty Olive */
    }

    /* -- 3. Fast Selector Steps (RIGHT) -- */
    .stepper-card {
        grid-area: steps;
        padding: 20px;
        display: flex;
        flex-direction: column;
        justify-content: space-around;
        align-items: center;
    }
    .stepper {
        display: flex;
        align-items: center;
        justify-content: space-between;
        width: 100%;
        max-width: 400px;
        position: relative;
    }
    .step-line {
        position: absolute;
        height: 4px;
        background: #e1e7ec;
        top: 18px;
        left: 0;
        right: 0;
        z-index: -1;
    }
    .step {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        background-color: #e1e7ec; /* Base gray */
        color: white;
        font-weight: bold;
        position: relative;
        cursor: pointer;
        font-size: 1.2rem;
    }
    .step-tick {
        position: absolute;
        width: 20px;
        height: 10px;
        border-bottom: 4px solid white;
        border-left: 4px solid white;
        transform: rotate(-45deg);
        top: 10px;
    }
    .active-step {
        background-color: #0081ff; /* Image Blue */
        box-shadow: 0 0 10px rgba(0,129,255,0.4);
    }
    .finished-step {
        background-color: #0081ff;
    }
    .stepper-label {
        font-size: 0.85rem;
        color: #676f54;
        font-weight: normal;
        margin-top: 5px;
    }

    /* -- 4. Timeline View (BOTTOM) -- */
    .timeline-card {
        grid-area: timeline;
        padding: 20px;
        border-radius: 10px;
        border-top: 2px solid #e1e7ec;
    }
    .tl-header {
        font-weight: bold;
        color: #044389;
        margin-bottom: 15px;
    }
    .tl-container {
        position: relative;
        height: 120px;
        display: flex;
        justify-content: flex-start;
        align-items: center;
        padding-top: 20px;
    }
    .tl-line {
        position: absolute;
        left: 0;
        top: 20px;
        height: 100px;
        width: 2px;
        background: #0081ff;
        opacity: 0.15;
        z-index: 1;
    }
    .tick-marks {
        display: flex;
        justify-content: flex-start;
        position: absolute;
        top: 20px;
        left: 0;
        width: 100%;
        height: 100px;
    }
    .tick {
        flex: 1;
        border-left: 2px solid rgba(0,129,255, 0.15);
    }
    .tl-milestones {
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        z-index: 2;
        width: 100%;
        padding-left: 20px;
    }
    .tl-item {
        margin-bottom: 10px;
        font-size: 0.95rem;
        position: relative;
    }
    .tl-item-indicator {
        position: absolute;
        left: -20px;
        top: 4px;
        width: 12px;
        height: 12px;
        border-radius: 50%;
    }
    
    </style>
    """, unsafe_allow_html=True)

# --- CONFIG DATA ---
FAST_CHOICES = collections.OrderedDict([(48, "48H"), (72, "72H"), (120, "EF"), (168, "7D")])
PALETTE_BLUE = "#0081ff"
PALETTE_ROSEWOOD = "#b56576" # Accent

# Biological Stages (based on user info)
STAGES = [
    {"name": "Feeding", "max_h": 4, "desc": "Processing last meal.", "color": "#7cafc4"},
    {"name": "Early Fasting", "max_h": 16, "desc": "Liver breaks down glycogen.", "color": "#676f54"},
    {"name": "Ketosis Begins", "max_h": 24, "desc": "Switching to fat-burning.", "color": PALETTE_BLUE},
    {"name": "Autophagy / Deep Ketosis", "max_h": 72, "desc": "Cellular cleanup/Muscle preservation.", "color": PALETTE_ROSEWOOD},
    {"name": "Immune Refresh", "max_h": 1000, "desc": "White blood cells regenerating.", "color": PALETTE_BLUE}
]

# Electrolyte Recommendations
RECOMMENDATIONS = [
    {"h_trigger": 12, "h_end": 24, "color": PALETTE_BLUE, "rec": "Take 1/2 pack electrolytes with water. (1st half of day)"},
    {"h_trigger": 16, "h_end": 24, "color": PALETTE_ROSEWOOD, "rec": "Take 1/2 pack electrolytes. (2nd half of day)"},
    {"h_trigger": 36, "h_end": 48, "color": PALETTE_BLUE, "rec": "Take 1 FULL packet of electrolytes. (Morning)"},
    {"h_trigger": 42, "h_end": 48, "color": PALETTE_ROSEWOOD, "rec": "Take 1 FULL packet of electrolytes. (Afternoon)"},
    {"h_trigger": 72, "h_end": 73, "color": PALETTE_ROSEWOOD, "rec": "**72H:** Reintroduce gut food and lean protein slowly."}
]

# --- APP HEADER ---
st.markdown("<h1 class='main-header'>FlowFast Tracker</h1>", unsafe_allow_html=True)

# --- SIDEBAR: Controls ---
st.sidebar.header("Fast Setup")
fast_target_h = st.sidebar.select_slider(
    "Set Fast Duration (Hours)",
    options=list(FAST_CHOICES.keys()),
    format_func=lambda x: FAST_CHOICES[x]
)

# Start/Reset Controls
col_btn1, col_btn2 = st.sidebar.columns(2)
with col_btn1:
    if st.button("▶ Start Fast"):
        # Set start time immediately
        st.session_state.start_time_obj = datetime.now()
        st.session_state.fast_target_h = fast_target_h
        st.rerun()
with col_btn2:
    if st.button("⏹ Reset"):
        st.session_state.start_time_obj = None
        st.session_state.fast_target_h = None
        st.rerun()

# Define variables based on state
is_active = st.session_state.start_time_obj is not None

# Placeholder/Null Calculations
hours_passed = 0
progress_pct = 0
total_hours_target = fast_target_h if st.session_state.start_time_obj is not None else 48 # default for rendering

if is_active:
    now = datetime.now()
    start_time_obj = st.session_state.start_time_obj
    target_hours = st.session_state.fast_target_h
    
    elapsed_seconds = (now - start_time_obj).total_seconds()
    hours_passed = elapsed_seconds / 3600
    
    total_seconds_target = target_hours * 3600
    progress_pct = min(100.0, (elapsed_seconds / total_seconds_target) * 100) if total_seconds_target > 0 else 0


# --- BUILD DASHBOARD UI ---
st.markdown("<div class='dashboard-container'>", unsafe_allow_html=True)

# -- 1. Main Progress Bar (TOP) --
main_pbar_color = PALETTE_ROSEWOOD if progress_pct > 90 else PALETTE_BLUE
st.markdown(f"""
    <div class='p-bar-container'>
        <div class='p-bar-bg'></div>
        <div class='p-bar-fill' style='width: {progress_pct}%; background-color: {main_pbar_color};'></div>
    </div>
""", unsafe_allow_html=True)

# -- 2. Fasting Stages Circle (LEFT) --
active_stage_info = next(stage for stage in STAGES if hours_passed < stage["max_h"])
conic_gradient_str = f"conic-gradient({active_stage_info['color']} {progress_pct}%, #e1e7ec {progress_pct}%)"

# Dynamic 70% style from image
progress_circle_display = f"{progress_pct:.0f}%" if is_active else "0%"
circle_line = "<div style='width: 30px; height: 3px; background-color: #044389; margin: 2px auto;'></div>" if is_active else ""

st.markdown(f"""
    <div class='stage-card'>
        <div class='progress-circle' style='background: {conic_gradient_str};'>
            <div class='progress-content'>
                <div class='progress-pct'>{progress_circle_display}</div>
                {circle_line}
            </div>
        </div>
        <div class='stage-name'>{active_stage_info['name']}</div>
        <div style='color: #aab0c4; font-size: 0.9rem;'>{active_stage_info['desc']}</div>
    </div>
""", unsafe_allow_html=True)

# -- 3. Fast Selector Steps (RIGHT) --
# Build steps visually like the image (Finished, Active, Next)
steps_html = []
target_h_list = list(FAST_CHOICES.keys())
active_target_h = st.session_state.fast_target_h if st.session_state.fast_target_h else 48
is_fixed = target_h_list.index(active_target_h)

for i, hour_target in enumerate(target_h_list):
    label = FAST_CHOICES[hour_target]
    step_num = i + 1
    
    if i < is_fixed: # Completed steps
        steps_html.append(f"""
            <div class='step finished-step'>
                <div class='step-tick'></div>
                <div class='stepper-label' style='margin-top: 45px; position: absolute;'>{label}</div>
            </div>
        """)
    elif i == is_fixed and is_active: # Currently selected step (active)
        steps_html.append(f"""
            <div class='step active-step' style='border: 3px solid #0081ff; transform: scale(1.15); box-shadow: 0 0 10px rgba(0,129,255,0.4);'>
                <div class='step-tick' style='opacity:0;'></div>
                <div class='stepper-label' style='margin-top: 48px; position: absolute;'>{label}</div>
            </div>
        """)
    else: # Future steps
        steps_html.append(f"""
            <div class='step' style='background-color: transparent; border: 3px solid #e1e7ec; color: #aab0c4;'>
                {step_num}
                <div class='stepper-label' style='margin-top: 42px; position: absolute;'>{label}</div>
            </div>
        """)

st.markdown(f"""
    <div class='stepper-card'>
        <div class='tl-header'>FAST TARGET</div>
        <div class='stepper'>
            <div class='step-line'></div>
            {" ".join(steps_html)}
        </div>
        <div style='color: {PALETTE_BLUE}; font-size: 1.1rem; font-weight: bold; margin-top: 35px;'>{target_hours if is_active else 48} Hour Target</div>
    </div>
""", unsafe_allow_html=True)

# -- 4. Timeline View (BOTTOM) --
st.markdown("<div class='timeline-card'>", unsafe_allow_html=True)
st.markdown("<div class='tl-header'>TIMELINE & MILESTONES</div>", unsafe_allow_html=True)

if is_active:
    # Build timeline items based on user criteria
    timeline_items_html = []
    
    # 1. Start Milestone
    timeline_items_html.append(f"""
        <div class='tl-item'>
            <div class='tl-item-indicator' style='background-color: {active_stage_info['color']}; border: 2px solid white;'></div>
            <span style='color: #044389; font-weight: bold;'>FAST STARTED</span> • {start_time_obj.strftime("%H:%M")} ({start_time_obj.strftime("%d %b")})
        </div>
    """)

    # 2. Key Electrolyte Ticks (dynamic based on criteria)
    active_recs = [rec for rec in RECOMMENDATIONS if hours_passed >= rec["h_trigger"] and hours_passed < rec["h_end"]]
    
    # Process specifically: the electrolyte splits and full pack splits
    if hours_passed >= 12 and hours_passed < 16:
        active_recs = [RECOMMENDATIONS[0]] # 1/2 morning
    elif hours_passed >= 16 and hours_passed < 24:
        active_recs = [RECOMMENDATIONS[1]] # 1/2 afternoon
    elif hours_passed >= 36 and hours_passed < 42:
        active_recs = [RECOMMENDATIONS[2]] # Full morning
    elif hours_passed >= 42 and hours_passed < 48:
        active_recs = [RECOMMENDATIONS[3]] # Full afternoon
    else:
        # Check if the fast target is > than the current hour pass
        active_recs = [rec for rec in RECOMMENDATIONS if hours_passed >= rec["h_trigger"] and target_hours >= rec["h_end"]]

    for rec in active_recs:
        timeline_items_html.append(f"""
            <div class='tl-item'>
                <div class='tl-item-indicator' style='background-color: {rec['color']};'></div>
                <span style='color: #044389;'>{rec['h_trigger']}H:</span> <span style='font-weight:bold; color:{rec['color']}'>⚡ RECS:</span> {rec['rec']}
            </div>
        """)

    # 3. Dynamic Biological Stage Indicator
    current_bstage = f"""
        <div class='tl-item' style='margin-top: 20px; font-weight: bold;'>
            <div class='tl-item-indicator' style='background-color: {active_stage_info['color']}; border: 3px solid white; transform: scale(1.3);'></div>
            <span style='color: {active_stage_info['color']}; font-size: 1.1rem;'>STAGE: {active_stage_info['name']}</span>
        </div>
    """
    timeline_items_html.append(current_bstage)
    
    
    # 4. Target/End Milestone
    end_time_obj = start_time_obj + timedelta(hours=target_hours)
    finish_color = active_stage_info['color'] if progress_pct < 100 else PALETTE_ROSEWOOD
    
    timeline_items_html.append(f"""
        <div class='tl-item' style='margin-top: 15px;'>
            <div class='tl-item-indicator' style='background-color: #e1e7ec; border: 3px solid #aab0c4;'></div>
            <span style='color: #aab0c4;'>TARGET COMPLETE</span> • {end_time_obj.strftime("%H:%M")} ({end_time_obj.strftime("%d %b")})
        </div>
    """)

    st.markdown(f"""
        <div class='tl-container'>
            <div class='tl-line'></div>
            <div class='tick-marks'>{" ".join(["<div class='tick'></div>"] * target_hours)}</div>
            <div class='tl-milestones'>
                {" ".join(timeline_items_html)}
            </div>
        </div>
    """, unsafe_allow_html=True)

else:
    # No fast active state display
    st.markdown(f"""
        <div class='tl-container' style='display: flex; justify-content: center; align-items: center; color: #aab0c4;'>
            Set target duration and press "Start Fast" in the sidebar to begin tracking.
        </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True) # close timeline-card
st.markdown("</div>", unsafe_allow_html=True) # close dashboard-container

# -- METRICS: TIME PASSED (Bottom Right) --
# Show exact metrics if active
if is_active:
    st.write("---")
    remaining_secs = (end_time_obj - now).total_seconds()
    remaining_hrs = remaining_secs / 3600 if remaining_secs > 0 else 0

    col_m1, col_m2, col_m3 = st.columns([2, 1, 1])
    with col_m1:
        st.metric("Start Time", start_time_obj.strftime("%H:%M (%d %b)"))
    with col_m2:
        st.metric("Total Elapsed", f"{hours_passed:.1f} Hours", f"{hours_passed:.2f}")
    with col_m3:
        st.metric("Time Remaining", f"{remaining_hrs:.1f} Hours", f"-{remaining_hrs:.1f}")

    if progress_pct >= 100:
        if target_hours == 48:
            st.success("**Fast Complete!** (48H). Reintroduce food normally.")
        else:
            st.success("**Fast Complete!** (72H+). Gently break with gut food.")
