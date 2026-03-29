import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import time
import math

# --- SUPABASE ---
supabase: Client = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# --- STATE ---
if "user_data" not in st.session_state:
    st.session_state.user_data = None

# --- PAGE ---
st.set_page_config(layout="wide", page_title="Fasting")

# --- STYLE ---
st.markdown("""
<style>
.stApp { background:#f7f9fc; }

.card {
    background:white;
    padding:18px;
    border-radius:12px;
}

.group {
    background:linear-gradient(135deg,#1f3c88,#3a86ff);
    color:white;
    padding:18px;
    border-radius:12px;
    text-align:center;
    margin-bottom:15px;
}

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

.chat {
    background:#eef2f7;
    padding:8px;
    border-radius:8px;
    margin-bottom:6px;
}
</style>
""", unsafe_allow_html=True)

# --- LOGIN ---
if not st.session_state.user_data:
    st.title("Fasting Tracker")

    with st.form("login"):
        name = st.text_input("Name").upper()
        code = st.text_input("Code").upper()
        goal = st.selectbox("Goal", [48,72,120])

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
                    "start_time":None,   # ✅ NOT STARTED
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

# --- TIME ---
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
group_total = sum(get_hours(m["start_time"]) for m in members)

# --- UI ---
st.markdown(f"<div class='group'><h3>{group_total:.1f} hrs group</h3></div>", unsafe_allow_html=True)

col1,col2 = st.columns([1.4,1])

# --- LEFT ---
with col1:
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    if user["start_time"]:
        # TIMER
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

        st.progress(progress/100)

        # CHECKPOINTS
        st.write("**Milestones**")
        checkpoints = [(12,"Sugar"),(18,"Fat Burn"),(24,"Ketosis"),(48,"Autophagy"),(72,"Repair")]
        cols = st.columns(len(checkpoints))

        for i,(hrs,label) in enumerate(checkpoints):
            with cols[i]:
                if my_hours >= hrs:
                    st.success(label)
                else:
                    st.caption(label)

    else:
        st.info("Fast not started yet")

    st.markdown("</div>", unsafe_allow_html=True)

# --- RIGHT ---
with col2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    # START BUTTON
    if not user["start_time"]:
        if st.button("▶️ Start Fast"):
            now_iso = datetime.utcnow().isoformat()

            supabase.table("fasting_groups").update({
                "start_time":now_iso
            }).eq("id",user["id"]).execute()

            st.session_state.user_data["start_time"] = now_iso
            st.rerun()

    else:
        if st.button("Restart Fast"):
            supabase.table("fasting_groups").update({
                "start_time":None
            }).eq("id",user["id"]).execute()

            st.session_state.user_data["start_time"] = None
            st.rerun()

    st.divider()

    # CHAT
    st.subheader("💬 Chat")

    msgs = supabase.table("fasting_messages")\
        .select("*")\
        .eq("group_code",user["group_code"])\
        .order("created_at",desc=True)\
        .limit(5)\
        .execute().data

    for msg in reversed(msgs):
        st.markdown(f"<div class='chat'><b>{msg['user_name']}</b><br>{msg['message_text']}</div>", unsafe_allow_html=True)

    with st.form("chat", clear_on_submit=True):
        text = st.text_input("Message")
        if st.form_submit_button("Send") and text:
            supabase.table("fasting_messages").insert({
                "user_name":user["user_name"],
                "group_code":user["group_code"],
                "message_text":text
            }).execute()
            st.rerun()

    if st.button("Logout"):
        st.session_state.user_data = None
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# LOOP
time.sleep(1)
st.rerun()
