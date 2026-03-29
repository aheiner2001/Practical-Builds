import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import time
import math

# --- 1. SUPABASE CONNECTION ---
try:
    supabase: Client = create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )
except Exception:
    st.error("Connect Supabase in .streamlit/secrets.toml first!")
    st.stop()

if 'user_data' not in st.session_state:
    st.session_state.user_data = None

# --- 2. PAGE CONFIG ---
st.set_page_config(page_title="Fasting Tracker", page_icon="💧", layout="wide")

# --- 3. STYLING ---
st.markdown("""
<style>
.stApp { background: #f6f8fb; }

/* Header */
.main-header {
    text-align: center;
    font-size: 2.4rem;
    font-weight: 800;
    color: #1f3c88;
}

/* Cards */
.card {
    background: white;
    padding: 22px;
    border-radius: 14px;
    border: 1px solid #e6e9ef;
    box-shadow: 0 4px 12px rgba(0,0,0,0.04);
}

/* Group Card */
.group-card {
    background: linear-gradient(135deg, #1f3c88, #3a86ff);
    color: white;
    padding: 24px;
    border-radius: 14px;
    text-align: center;
    margin-bottom: 20px;
}

/* Timer */
.progress-circle {
    width: 210px;
    height: 210px;
    border-radius: 50%;
    display: flex;
    justify-content: center;
    align-items: center;
    margin: auto;
    position: relative;
}

.progress-circle::after {
    content: "";
    position: absolute;
    width: 175px;
    height: 175px;
    background: #f6f8fb;
    border-radius: 50%;
}

.time {
    font-size: 2.4rem;
    font-weight: bold;
    font-family: monospace;
    color: #1f3c88;
}

.label {
    font-size: 0.85rem;
    color: #7a8599;
}

/* Timeline */
.bar-bg {
    height: 8px;
    background: #e6e9ef;
    border-radius: 4px;
    margin: 40px 0 20px 0;
    position: relative;
}

.bar-fill {
    height: 100%;
    background: #3a86ff;
    border-radius: 4px;
}

.dot {
    position: absolute;
    top: -6px;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    border: 3px solid white;
}

.dot-label {
    position: absolute;
    top: 24px;
    font-size: 0.7rem;
    color: #5c677d;
    transform: translateX(-50%);
}

/* Chat */
.chat-bubble {
    background: #f1f3f7;
    padding: 10px 14px;
    border-radius: 12px;
    margin-bottom: 8px;
}

.chat-user {
    font-size: 0.7rem;
    font-weight: bold;
    color: #3a86ff;
}

.chat-text {
    font-size: 0.9rem;
}
</style>
""", unsafe_allow_html=True)

# --- 4. LOGIN ---
if not st.session_state.user_data:
    st.markdown("<div class='main-header'>Fasting Tracker</div>", unsafe_allow_html=True)

    with st.form("login"):
        name = st.text_input("First Name").strip().upper()
        code = st.text_input("Family Code").strip().upper()

        # ✅ ONLY THESE OPTIONS (no 24)
        goal = st.selectbox("Fast Goal (Hours)", [48, 72, 120])

        if st.form_submit_button("Enter"):
            if name and code:
                res = supabase.table("fasting_groups") \
                    .select("*") \
                    .eq("user_name", name) \
                    .eq("group_code", code) \
                    .execute()

                if res.data:
                    st.session_state.user_data = res.data[0]
                else:
                    new_user = {
                        "user_name": name,
                        "group_code": code,
                        "start_time": datetime.now().isoformat(),
                        "target_hours": goal
                    }
                    ins = supabase.table("fasting_groups").insert(new_user).execute()
                    st.session_state.user_data = ins.data[0]

                st.rerun()

    st.stop()

# --- 5. DATA ---
user = st.session_state.user_data

members = supabase.table("fasting_groups") \
    .select("*") \
    .eq("group_code", user['group_code']) \
    .execute().data

now = datetime.now().astimezone()

def get_hours(start):
    start = datetime.fromisoformat(start.replace('Z', '+00:00'))
    return max(0, (now - start).total_seconds() / 3600)

my_hours = get_hours(user['start_time'])
progress = min(100, (my_hours / user['target_hours']) * 100)
group_total = sum(get_hours(m['start_time']) for m in members)

# Hunger curve
hunger = 50 + 35 * math.sin((my_hours - 4) * (math.pi / 6))

# --- 6. UI ---

# Group Card
st.markdown(f"""
<div class='group-card'>
    <div style='font-size:0.8rem; opacity:0.8;'>GROUP STREAK</div>
    <div style='font-size:2.2rem; font-weight:bold;'>{group_total:.1f} hrs</div>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1.4, 1])

# --- LEFT ---
with col1:
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    # Timer
    conic = f"conic-gradient(#3a86ff {progress:.1f}%, #e6e9ef {progress:.1f}%)"
    h, m, s = int(my_hours), int((my_hours*60)%60), int((my_hours*3600)%60)

    st.markdown(f"""
    <div class='progress-circle' style='background:{conic};'>
        <div style='z-index:2; text-align:center;'>
            <div class='time'>{h:02d}:{m:02d}:{s:02d}</div>
            <div class='label'>{user['user_name']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- FIXED TIMELINE ---
    checkpoints = [12, 18, 24, 48, 72]
    labels = ["Sugar", "Fat Burn", "Ketosis", "Autophagy", "Repair"]

    dot_html = ""
    for hrs, label in zip(checkpoints, labels):
        percent = (hrs / user['target_hours']) * 100

        if percent <= 100:
            color = "#3a86ff" if my_hours >= hrs else "#dfe3eb"

            dot_html += f"""
            <div class="dot" style="left:{percent:.1f}%; background:{color};"></div>
            <div class="dot-label" style="left:{percent:.1f}%;">{label}</div>
            """

    st.markdown(f"""
    <div class="bar-bg">
        <div class="bar-fill" style="width:{progress:.1f}%;"></div>
        {dot_html}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Members
    st.subheader("👥 Family Progress")
    for m in members:
        h = get_hours(m['start_time'])
        p = min(1.0, h / m['target_hours'])
        st.caption(f"{m['user_name']} • {h:.1f}/{m['target_hours']} hrs")
        st.progress(p)

# --- RIGHT ---
with col2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    st.subheader("📉 Hunger")
    st.progress(min(1.0, hunger / 100))
    st.caption("Hunger comes in waves — it passes.")

    st.divider()

    # Chat
    st.subheader("💬 Chat")

    msgs = supabase.table("fasting_messages") \
        .select("*") \
        .eq("group_code", user['group_code']) \
        .order("created_at", desc=True) \
        .limit(5).execute().data

    chat_box = st.container(height=200)
    with chat_box:
        for msg in reversed(msgs):
            st.markdown(f"""
            <div class='chat-bubble'>
                <div class='chat-user'>{msg['user_name']}</div>
                <div class='chat-text'>{msg['message_text']}</div>
            </div>
            """, unsafe_allow_html=True)

    with st.form("chat", clear_on_submit=True):
        text = st.text_input("Message")
        if st.form_submit_button("Send") and text:
            supabase.table("fasting_messages").insert({
                "user_name": user['user_name'],
                "group_code": user['group_code'],
                "message_text": text
            }).execute()
            st.rerun()

    st.divider()

    c1, c2 = st.columns(2)

    if c1.button("Restart", use_container_width=True):
        supabase.table("fasting_groups").update({
            "start_time": datetime.now().isoformat()
        }).eq("id", user['id']).execute()
        st.rerun()

    if c2.button("Logout", use_container_width=True):
        st.session_state.user_data = None
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# --- LOOP ---
time.sleep(1)
st.rerun()
