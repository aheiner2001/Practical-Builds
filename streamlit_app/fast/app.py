import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta
import time
import collections

# --- 1. INITIALIZE SUPABASE ---
# Make sure these are in your .streamlit/secrets.toml
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception:
    st.error("Please configure Supabase secrets to use the family features.")
    st.stop()

# --- 2. SESSION STATE ---
if 'user_data' not in st.session_state:
    st.session_state.user_data = None

# --- 3. PAGE CONFIG & STYLING ---
st.set_page_config(page_title="Family FlowFast", page_icon="💧", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: white; }
    .main-header { color: #044389; text-align: center; font-family: sans-serif; margin-bottom: 20px; }
    
    .dashboard-container {
        display: grid;
        grid-template-areas: "progress progress" "stages steps" "family family";
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
    .stopwatch-display { z-index: 10; text-align: center; }
    .time-digits { font-size: 2.2rem; font-weight: bold; color: #044389; display: block; font-family: monospace; }
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
    
    /* Family Section */
    .family-card { background: #f7fbff; padding: 20px; border-radius: 15px; border: 1px solid #e1e7ec; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. LOGIN / JOIN LOGIC ---
if st.session_state.user_data is None:
    st.markdown("<h1 class='main-header'>FlowFast Family</h1>", unsafe_allow_html=True)
    with st.container():
        col_l, col_r = st.columns(2)
        with col_l:
            st.subheader("Join a Fast")
            with st.form("login_form"):
                u_name = st.text_input("Your Name")
                u_group = st.text_input("Group/Family Code")
                u_target = st.selectbox("Goal (Hours)", [48, 72, 120])
                if st.form_submit_button("Start Fasting"):
                    # Upsert to Supabase
                    data = {
                        "user_name": u_name, 
                        "group_code": u_group.upper(), 
                        "start_time": datetime.now().isoformat(),
                        "target_hours": u_target
                    }
                    res = supabase.table("fasting_groups").upsert(data, on_conflict="user_name, group_code").execute()
                    st.session_state.user_data = res.data[0]
                    st.rerun()
        with col_r:
            st.info("👋 **How it works:** Enter a name and a shared family code. You'll see everyone else using the same code below your timer!")
    st.stop()

# --- 5. DASHBOARD CALCULATIONS ---
user = st.session_state.user_data
start_time = datetime.fromisoformat(user['start_time'])
now = datetime.now().astimezone() # Ensure timezone awareness
diff = now - start_time
total_seconds = int(diff.total_seconds())

# HH:MM:SS for Stopwatch
hours = total_seconds // 3600
minutes = (total_seconds % 3600) // 60
seconds = total_seconds % 60
stopwatch_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

hours_passed = total_seconds / 3600
target_h = user['target_hours']
progress_pct = min(100.0, (hours_passed / target_h) * 100)

# --- 6. RENDER DASHBOARD ---
st.markdown(f"<h1 class='main-header'>{user['group_code']} DASHBOARD</h1>", unsafe_allow_html=True)
st.markdown("<div class='dashboard-container'>", unsafe_allow_html=True)

# TOP PROGRESS
st.markdown(f"""
    <div style='grid-area: progress;'>
        <div class='p-bar-bg'><div class='p-bar-fill' style='width:{progress_pct}%; background:#0081ff;'></div></div>
    </div>
""", unsafe_allow_html=True)

# LEFT CIRCLE
conic = f"conic-gradient(#0081ff {progress_pct}%, #e8dab2 {progress_pct}%)"
st.markdown(f"""
    <div style='grid-area: stages; display:flex; flex-direction:column; align-items:center;'>
        <div class='progress-circle' style='background:{conic};'>
            <div class='stopwatch-display'>
                <span class='time-digits'>{stopwatch_str}</span>
                <span class='time-label'>Your Fast</span>
            </div>
        </div>
        <div style='margin-top:10px; font-weight:bold; color:#676f54;'>{user['user_name']}</div>
    </div>
""", unsafe_allow_html=True)

# RIGHT STEPPER
steps_html = ""
for h in [48, 72, 120]:
    active = "active-step" if h == target_h else ""
    steps_html += f"<div class='step {active}'>{h}</div>"

st.markdown(f"""
    <div style='grid-area: steps;'>
        <div style='font-weight:bold; color:#044389;'>MY TARGET</div>
        <div class='stepper'><div class='step-line'></div>{steps_html}</div>
        <div style='background:#7cafc4; color:white; padding:15px; border-radius:10px;'>
            <strong>Recommendation:</strong><br>
            { "Take 1 full electrolyte pack" if hours_passed > 36 else "Take 1/2 electrolyte pack" if hours_passed > 12 else "Drink water" }
        </div>
    </div>
""", unsafe_allow_html=True)

# --- 7. FAMILY SECTION (BOTTOM) ---
st.markdown("<div style='grid-area: family;' class='family-card'>", unsafe_allow_html=True)
st.subheader("👥 Current Group Members")

# Fetch all in same group
members = supabase.table("fasting_groups").select("*").eq("group_code", user['group_code']).execute()

for m in members.data:
    m_start = datetime.fromisoformat(m['start_time'])
    m_diff = now - m_start
    m_hours = m_diff.total_seconds() / 3600
    m_prog = min(1.0, m_hours / m['target_hours'])
    
    col_n, col_p = st.columns([1, 4])
    with col_n:
        st.write(f"**{m['user_name']}**")
    with col_p:
        st.progress(m_prog)
        st.caption(f"{m_hours:.1f} hrs / {m['target_hours']} hrs")

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# --- 8. HEARTBEAT ---
if st.sidebar.button("Log Out"):
    st.session_state.user_data = None
    st.rerun()

time.sleep(1)
st.rerun()
