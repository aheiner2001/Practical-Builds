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

if "confirm_restart" not in st.session_state:
    st.session_state.confirm_restart = False

# --- 2. PAGE CONFIG ---
st.set_page_config(page_title="Fasting Tracker", page_icon="💧", layout="wide")

# --- 3. SIMPLE CLEAN STYLE ---
st.markdown("""
<style>
.stApp { background: #f6f8fb; }

.card {
    background: white;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #e6e9ef;
}

.group-card {
    background: linear-gradient(135deg, #1f3c88, #3a86ff);
    color: white;
    padding: 20px;
    border-radius: 12px;
    text-align: center;
    margin-bottom: 20px;
}

.time {
    font-size: 2.2rem;
    font-weight: bold;
    font-family: monospace;
}

.chat-bubble {
    background: #f1f3f7;
    padding: 8px 12px;
    border-radius: 10px;
    margin-bottom: 6px;
}
</style>
""", unsafe_allow_html=True)

# --- 4. LOGIN ---
if not st.session_state.user_data:
    st.title("Fasting Tracker")

    with st.form("login"):
        name = st.text_input("First Name").strip().upper()
        code = st.text_input("Family Code").strip().upper()
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
progress = min(1.0, my_hours / user['target_hours'])
group_total = sum(get_hours(m['start_time']) for m in members)

hunger = 50 + 35 * math.sin((my_hours - 4) * (math.pi / 6))

# --- 6. UI ---

# Group
st.markdown(f"""
<div class='group-card'>
    <div>GROUP STREAK</div>
    <div style='font-size:2rem;'>{group_total:.1f} hrs</div>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1.4, 1])

# --- LEFT ---
with col1:
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    h, m, s = int(my_hours), int((my_hours*60)%60), int((my_hours*3600)%60)

    st.markdown(f"<div class='time'>{h:02d}:{m:02d}:{s:02d}</div>", unsafe_allow_html=True)
    st.caption(user['user_name'])

    st.progress(progress)

    # ✅ CLEAN TIMELINE (NO HTML BUGS)
    st.write("**Milestones**")
    milestones = [
        (12, "Sugar"),
        (18, "Fat Burn"),
        (24, "Ketosis"),
        (48, "Autophagy"),
        (72, "Repair"),
    ]

    cols = st.columns(len(milestones))
    for i, (hrs, label) in enumerate(milestones):
        with cols[i]:
            if my_hours >= hrs:
                st.success(label)
            else:
                st.caption(label)

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

    st.divider()

    # Chat
    st.subheader("💬 Chat")

    msgs = supabase.table("fasting_messages") \
        .select("*") \
        .eq("group_code", user['group_code']) \
        .order("created_at", desc=True) \
        .limit(5).execute().data

    for msg in reversed(msgs):
        st.markdown(f"""
        <div class='chat-bubble'>
            <b>{msg['user_name']}</b><br>
            {msg['message_text']}
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

    # ✅ RESTART FLOW (CONFIRMATION)
    if not st.session_state.confirm_restart:
        if st.button("Restart Fast"):
            st.session_state.confirm_restart = True
            st.rerun()
    else:
        st.warning("Start a new fast now?")
        c1, c2 = st.columns(2)

        if c1.button("Yes, Start"):
            supabase.table("fasting_groups").update({
                "start_time": datetime.now().isoformat()
            }).eq("id", user['id']).execute()

            st.session_state.confirm_restart = False
            st.rerun()

        if c2.button("Cancel"):
            st.session_state.confirm_restart = False
            st.rerun()

    if st.button("Logout"):
        st.session_state.user_data = None
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# --- LOOP ---
time.sleep(1)
st.rerun()
