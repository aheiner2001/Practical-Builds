import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import time
import math

# --- SUPABASE ---
supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# --- SESSION STATE ---
if "user_data" not in st.session_state:
    st.session_state.user_data = None

# --- PAGE CONFIG ---
st.set_page_config(layout="wide", page_title="Fasting Tracker")

# --- STYLING ---
st.markdown("""
<style>
.stApp { background:#f7f9fc; font-family:sans-serif; }

/* Card */
.card {
    background:white;
    padding:18px;
    border-radius:12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

/* Group header */
.group {
    background:linear-gradient(135deg,#1f3c88,#3a86ff);
    color:white;
    padding:18px;
    border-radius:12px;
    text-align:center;
    margin-bottom:15px;
    font-weight:bold;
}

/* Circle timer */
.circle {
    width:200px;
    height:200px;
    border-radius:50%;
    display:flex;
    align-items:center;
    justify-content:center;
    margin:auto;
}

.inner {
    width:160px;
    height:160px;
    background:white;
    border-radius:50%;
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
}

.big {
    font-size:2rem;
    font-family:monospace;
    font-weight:bold;
}

/* Progress bar milestones */
.progress-container {
    position: relative;
    height: 12px;
    background:#e6e9ef;
    border-radius:6px;
    margin:20px 0;
}

.progress-fill {
    height:100%;
    background:#3a86ff;
    border-radius:6px;
    transition: width 0.5s;
}

.dot {
    position:absolute;
    top:-6px;
    width:16px;
    height:16px;
    border-radius:50%;
    border:3px solid white;
    background:#dfe3eb;
    transform:translateX(-50%);
    box-shadow: 0 2px 4px rgba(0,0,0,0.15);
}

.dot.active {
    background:#3a86ff;
}

.dot-label {
    position:absolute;
    top:20px;
    font-size:0.75rem;
    font-weight:600;
    transform:translateX(-50%);
    color:#495057;
    white-space:nowrap;
}

/* Chat */
.chat-container {
    max-height:250px;
    overflow-y:auto;
    padding-right:5px;
}

.chat-message {
    background:#eef2f7;
    padding:8px;
    border-radius:8px;
    margin-bottom:6px;
}

.chat-user {
    font-weight:bold;
    color:#3a86ff;
    margin-bottom:2px;
}
</style>
""", unsafe_allow_html=True)

# --- LOGIN ---
if not st.session_state.user_data:
    st.title("Fasting Tracker")

    with st.form("login"):
        name = st.text_input("Name").upper()
        code = st.text_input("Group Code").upper()
        goal = st.selectbox("Goal (hours)", [48,72,120])

        if st.form_submit_button("Enter"):
            res = supabase.table("fasting_groups")\
                .select("*")\
                .eq("user_name",name)\
                .eq("group_code",code)\
                .execute()

            if res.data:
                st.session_state.user_data = res.data[0]
            else:
                ins = supabase.table("fasting_groups").insert({
                    "user_name":name,
                    "group_code":code,
                    "start_time":None,  # Fast not started yet
                    "target_hours":goal
                }).execute()
                st.session_state.user_data = ins.data[0]

            st.rerun()
    st.stop()

# --- DATA ---
user = st.session_state.user_data

members = supabase.table("fasting_groups")\
    .select("*")\
    .eq("group_code",user["group_code"])\
    .execute().data

def get_hours(start):
    if not start:
        return 0
    start_dt = datetime.fromisoformat(start.replace("Z","+00:00"))
    now_dt = datetime.utcnow()
    if start_dt.tzinfo:
        start_dt = start_dt.replace(tzinfo=None)
    return max(0,(now_dt-start_dt).total_seconds()/3600)

my_hours = get_hours(user["start_time"])
progress = min(100, my_hours/user["target_hours"]*100) if user["start_time"] else 0
group_total = sum(get_hours(m.get("start_time")) for m in members)

# --- RECOMMENDATIONS ---
def get_recommendation(h):
    if h < 16:
        return "Hydrate well. No supplements needed."
    elif h < 24:
        return "Moderate fast. Electrolytes recommended if active or fatigued."
    elif h < 48:
        return "Extended fast. Take 1 pack of electrolytes in the morning and 1 in the evening."
    else:
        return "Long fast. Take 2 packs electrolytes per day, more if active. Monitor sodium/potassium closely."

def electrolyte_plan(h):
    if h < 16:
        return "💧 Water only"
    elif h < 24:
        return "⚡ Optional electrolytes (if needed)"
    elif h < 30:
        return "⚡ 1 pack morning + 1 pack evening"
    elif h < 48:
        return "⚡ 2 packs per day (1 morning + 1 evening)"
    else:
        return "⚡ 2–3 packs per day, depending on activity level"

# --- UI ---
st.markdown(f"<div class='group'>{group_total:.1f} hrs group total</div>", unsafe_allow_html=True)

col1, col2 = st.columns([1.4,1])

# --- LEFT ---
with col1:
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    if user["start_time"]:
        # Circle timer
        conic = f"conic-gradient(#3a86ff {progress}%, #e6e9ef {progress}%)"
        h,m,s = int(my_hours), int((my_hours*60)%60), int((my_hours*3600)%60)
        st.markdown(f"""
        <div class='circle' style='background:{conic};'>
            <div class='inner'>
                <div class='big'>{h:02d}:{m:02d}:{s:02d}</div>
                <div>{user['user_name']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Progress bar with milestones
        st.markdown("<div class='progress-container'>", unsafe_allow_html=True)
        st.markdown(f"<div class='progress-fill' style='width:{progress}%;'></div>", unsafe_allow_html=True)

        # Checkpoints
        checkpoints = [(12,"Sugar"),(18,"Fat Burn"),(24,"Ketosis"),(48,"Autophagy"),(72,"Cellular Repair")]
        for hrs,label in checkpoints:
            left_pct = min(100, hrs/user['target_hours']*100)
            active_class = "active" if my_hours >= hrs else ""
            st.markdown(f"""
            <div class='dot {active_class}' style='left:{left_pct}%;'></div>
            <div class='dot-label' style='left:{left_pct}%;'>{label}</div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.info("Fast not started yet")

    st.markdown("</div>", unsafe_allow_html=True)

    # Family
    st.subheader("👥 Family Members")
    for m in members:
        h_m = get_hours(m.get("start_time"))
        st.caption(f"{m['user_name']} • {h_m:.1f}/{m['target_hours']} hrs")
        st.progress(min(1.0,h_m/m["target_hours"] if m.get("start_time") else 0))

# --- RIGHT ---
with col2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    # START / RESTART / LOGOUT
    if not user["start_time"]:
        if st.button("▶️ Start Fast"):
            now_iso = datetime.utcnow().isoformat()
            supabase.table("fasting_groups").update({"start_time":now_iso}).eq("id",user["id"]).execute()
            st.session_state.user_data["start_time"] = now_iso
            st.rerun()
    else:
        col_restart,col_logout = st.columns([1,1])
        with col_restart:
            if st.button("🔄 Restart Fast"):
                supabase.table("fasting_groups").update({"start_time":None}).eq("id",user["id"]).execute()
                st.session_state.user_data["start_time"] = None
                st.rerun()
        with col_logout:
            if st.button("Logout"):
                st.session_state.user_data = None
                st.rerun()

    st.divider()

    # Recommendations
    st.subheader("🧠 Recommendation")
    st.info(get_recommendation(my_hours))

    st.subheader("💧 Electrolytes")
    st.warning(electrolyte_plan(my_hours))

    st.divider()

    # Chat
    st.subheader("💬 Chat")
    chat_html = "<div class='chat-container'>"
    msgs = supabase.table("fasting_messages")\
        .select("*")\
        .eq("group_code",user["group_code"])\
        .order("created_at",desc=True)\
        .limit(20)\
        .execute().data

    for msg in reversed(msgs):
        chat_html += f"<div class='chat-message'><div class='chat-user'>{msg['user_name']}</div>{msg['message_text']}</div>"
    chat_html += "</div>"
    st.markdown(chat_html, unsafe_allow_html=True)

    with st.form("chat_form", clear_on_submit=True):
        text = st.text_input("Message")
        if st.form_submit_button("Send") and text:
            supabase.table("fasting_messages").insert({
                "user_name":user["user_name"],
                "group_code":user["group_code"],
                "message_text":text
            }).execute()
            st.rerun()

    if not user["start_time"]:
        if st.button("Logout"):
            st.session_state.user_data = None
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# LOOP
time.sleep(1)
st.rerun()
