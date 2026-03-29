import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta
import time

# --- 1. INITIALIZE SUPABASE ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception:
    st.error("Missing Supabase Secrets! Add them to .streamlit/secrets.toml")
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

    .p-bar-bg { height: 18px; width: 100%; background-color: #e8dab2; border-radius: 10px; position: relative; overflow: hidden; }
    .p-bar-fill { height: 100%; border-radius: 10px; transition: width 0.3s ease-in-out; }

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

    .stepper { display: flex; justify-content: space-between; align-items: center; width: 100%; position: relative; padding: 20px 0; }
    .step-line { position: absolute; height: 4px; background: #e8dab2; width: 100%; top: 50%; z-index: 1; }
    .step { width: 45px; height: 45px; border-radius: 50%; display: flex; justify-content: center; align-items: center; background: #e8dab2; color: white; z-index: 2; font-weight: bold; }
    .active-step { background: #0081ff; box-shadow: 0 0 15px rgba(0,129,255,0.5); transform: scale(1.1); }
    
    .family-card { background: #f7fbff; padding: 20px; border-radius: 15px; border: 1px solid #e1e7ec; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. LOGIN / JOIN LOGIC ---
if st.session_state.user_data is None:
    st.markdown("<h1 class='main-header'>FlowFast Family</h1>", unsafe_allow_html=True)
    col_l, col_r = st.columns([2, 1])
    
    with col_l:
        st.subheader("Join or Resume a Fast")
        with st.form("login_form"):
            u_name = st.text_input("Your Name").strip().upper()
            u_group = st.text_input("Group/Family Code").strip().upper()
            u_target = st.selectbox("Goal (Hours)", [48, 72, 120])
            
            if st.form_submit_button("Start / Resume Fasting"):
                if u_name and u_group:
                    query = supabase.table("fasting_groups").select("*").eq("user_name", u_name).eq("group_code", u_group).execute()
                    
                    if query.data and len(query.data) > 0:
                        st.session_state.user_data = query.data[0]
                    else:
                        new_entry = {
                            "user_name": u_name, 
                            "group_code": u_group, 
                            "start_time": datetime.now().isoformat(),
                            "target_hours": u_target
                        }
                        insert_res = supabase.table("fasting_groups").insert(new_entry).execute()
                        st.session_state.user_data = insert_res.data[0]
                    st.rerun()
    with col_r:
        st.info("💡 **Welcome!** Enter your group code to see your family's progress live.")
    st.stop()

# --- 5. DASHBOARD CALCULATIONS ---
user = st.session_state.user_data
# Fix for ISO format variations
start_str = user['start_time'].replace('Z', '+00:00')
start_time = datetime.fromisoformat(start_str)
now = datetime.now().astimezone()

diff = now - start_time
total_seconds = max(0, int(diff.total_seconds()))

hours = total_seconds // 3600
minutes = (total_seconds % 3600) // 60
seconds = total_seconds % 60
stopwatch_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

hours_passed = total_seconds / 3600
target_h = user['target_hours']
progress_pct = min(100.0, (hours_passed / target_h) * 100)

# --- 6. SIDEBAR: ACTION BUTTONS ---
st.sidebar.header("Fast Controls")

if st.sidebar.button("🔄 Restart My Fast", help="Resets your start time to right now."):
    new_time = datetime.now().isoformat()
    # Update Supabase
    res = supabase.table("fasting_groups").update({"start_time": new_time}).eq("id", user['id']).execute()
    st.session_state.user_data = res.data[0]
    st.toast("Fast restarted! Good luck.")
    time.sleep(1)
    st.rerun()

if st.sidebar.button("⏹ Stop & Logout", help="Ends this session and logs you out."):
    st.session_state.user_data = None
    st.rerun()

# --- 7. RENDER DASHBOARD ---
st.markdown(f"<h1 class='main-header'>{user['group_code']} GROUP</h1>", unsafe_allow_html=True)
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
                <span class='time-label'>{user['user_name']}</span>
            </div>
        </div>
        <div style='margin-top:10px; font-weight:bold; color:#676f54;'>{progress_pct:.1f}% COMPLETE</div>
    </div>
""", unsafe_allow_html=True)

# RIGHT STEPPER
steps_html = "".join([f"<div class='step {'active-step' if h == target_h else ''}'>{h}</div>" for h in [48, 72, 120]])

st.markdown(f"""
    <div style='grid-area: steps;'>
        <div style='font-weight:bold; color:#044389;'>MY TARGET</div>
        <div class='stepper'><div class='step-line'></div>{steps_html}</div>
        <div style='background:#7cafc4; color:white; padding:15px; border-radius:10px;'>
            <strong>Quick Guidance:</strong><br>
            { "Autophagy peak. Deep cellular repair." if hours_passed > 36 else "Ketosis active. Fat oxidation high." if hours_passed > 16 else "Transitioning to fat burning." }
        </div>
    </div>
""", unsafe_allow_html=True)

# --- 8. FAMILY LEADERBOARD ---
st.markdown("<div style='grid-area: family;' class='family-card'>", unsafe_allow_html=True)
st.subheader("👥 Live Group Members")

members = supabase.table("fasting_groups").select("*").eq("group_code", user['group_code']).execute()

for m in members.data:
    m_start = datetime.fromisoformat(m['start_time'].replace('Z', '+00:00'))
    m_hours = max(0, (now - m_start).total_seconds() / 3600)
    m_prog = min(1.0, m_hours / m['target_hours'])
    
    col_n, col_p = st.columns([1, 4])
    with col_n:
        st.write(f"**{m['user_name']}** {'(You)' if m['user_name'] == user['user_name'] else ''}")
    with col_p:
        st.progress(m_prog)
        st.caption(f"{m_hours:.1f} / {m['target_hours']} hrs")

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# Update clock every second
time.sleep(1)
st.rerun()
