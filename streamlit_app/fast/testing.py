import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import time
import math

# --- 1. SUPABASE ---
try:
    supabase: Client = create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )
except Exception:
    st.error("Add Supabase credentials in secrets.toml")
    st.stop()

# --- STATE ---
if "user_data" not in st.session_state:
    st.session_state.user_data = None

if "restart_mode" not in st.session_state:
    st.session_state.restart_mode = False

# --- CONFIG ---
st.set_page_config(page_title="Fasting Tracker", layout="wide")

# --- STYLE ---
st.markdown("""
<style>
.stApp { background: #f7f9fc; }

.card {
    background: white;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #e6e9ef;
}

.group {
    background: linear-gradient(135deg,#1f3c88,#3a86ff);
    color:white;
    padding:20px;
    border-radius:12px;
    text-align:center;
    margin-bottom:15px;
}

.big {
    font-size:2.2rem;
    font-weight:bold;
    font-family:monospace;
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
        code = st.text_input("Group Code").upper()
        goal = st.selectbox("Goal (hrs)", [48,72,120])

        if st.form_submit_button("Enter"):
            if name and code:
                res = supabase.table("fasting_groups")\
                    .select("*")\
                    .eq("user_name", name)\
                    .eq("group_code", code)\
                    .execute()

                if res.data:
                    st.session_state.user_data = res.data[0]
                else:
                    new = {
                        "user_name": name,
                        "group_code": code,
                        "start_time": datetime.now().isoformat(),
                        "target_hours": goal
                    }
                    ins = supabase.table("fasting_groups").insert(new).execute()
                    st.session_state.user_data = ins.data[0]

                st.rerun()
    st.stop()

# --- DATA ---
user = st.session_state.user_data

members = supabase.table("fasting_groups")\
    .select("*")\
    .eq("group_code", user["group_code"])\
    .execute().data

now = datetime.now().astimezone()

def get_hours(start):
    start = datetime.fromisoformat(start.replace("Z","+00:00"))
    return max(0,(now-start).total_seconds()/3600)

my_hours = get_hours(user["start_time"])
progress = min(1.0, my_hours/user["target_hours"])
group_total = sum(get_hours(m["start_time"]) for m in members)

# --- HUNGER ---
hunger = 50 + 35 * math.sin((my_hours - 4) * (math.pi / 6))

# --- RECOMMENDATIONS ENGINE ---
def get_recommendation(hours):
    if hours < 12:
        return "Hydrate well. Stay busy. Hunger will rise soon."
    elif hours < 18:
        return "Hunger wave incoming. Drink water + electrolytes."
    elif hours < 24:
        return "Fat burning starting. Stay hydrated."
    elif hours < 36:
        return "Ketosis active. Add electrolytes if feeling weak."
    elif hours < 48:
        return "Autophagy increasing. Rest if needed."
    else:
        return "Deep fast. Prioritize electrolytes + avoid overexertion."

def electrolyte_tip(hours):
    if hours < 16:
        return "Optional"
    elif hours < 24:
        return "Recommended now"
    else:
        return "Strongly recommended (sodium, potassium)"

# --- UI ---
st.markdown(f"""
<div class='group'>
    <div>GROUP TOTAL</div>
    <div class='big'>{group_total:.1f} hrs</div>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1.4,1])

# --- LEFT ---
with col1:
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    h,m,s = int(my_hours), int((my_hours*60)%60), int((my_hours*3600)%60)

    st.markdown(f"<div class='big'>{h:02d}:{m:02d}:{s:02d}</div>", unsafe_allow_html=True)
    st.caption(user["user_name"])

    # --- PROGRESS ---
    st.progress(progress)

    # --- CHECKPOINTS ---
    st.write("**Progress Milestones**")

    checkpoints = [
        (12,"Sugar Burn"),
        (18,"Fat Burn"),
        (24,"Ketosis"),
        (48,"Autophagy"),
        (72,"Repair")
    ]

    cols = st.columns(len(checkpoints))

    for i,(hrs,label) in enumerate(checkpoints):
        with cols[i]:
            if my_hours >= hrs:
                st.success(f"{label}\n{hrs}h")
            else:
                st.caption(f"{label}\n{hrs}h")

    st.markdown("</div>", unsafe_allow_html=True)

    # --- FAMILY ---
    st.subheader("👥 Family")
    for m in members:
        h = get_hours(m["start_time"])
        p = min(1.0, h/m["target_hours"])
        st.caption(f"{m['user_name']} • {h:.1f}/{m['target_hours']} hrs")
        st.progress(p)

# --- RIGHT ---
with col2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    # --- HUNGER ---
    st.subheader("📉 Hunger")
    st.progress(min(1.0,hunger/100))

    # --- RECOMMENDATION ---
    st.subheader("🧠 Guidance")
    st.info(get_recommendation(my_hours))

    # --- ELECTROLYTES ---
    st.subheader("💧 Electrolytes")
    st.warning(electrolyte_tip(my_hours))

    st.divider()

    # --- CHAT ---
    st.subheader("💬 Chat")

    msgs = supabase.table("fasting_messages")\
        .select("*")\
        .eq("group_code", user["group_code"])\
        .order("created_at", desc=True)\
        .limit(5).execute().data

    for msg in reversed(msgs):
        st.markdown(f"<div class='chat'><b>{msg['user_name']}</b><br>{msg['message_text']}</div>", unsafe_allow_html=True)

    with st.form("chat", clear_on_submit=True):
        text = st.text_input("Message")
        if st.form_submit_button("Send") and text:
            supabase.table("fasting_messages").insert({
                "user_name": user["user_name"],
                "group_code": user["group_code"],
                "message_text": text
            }).execute()
            st.rerun()

    st.divider()

    # --- RESTART (FIXED) ---
    if not st.session_state.restart_mode:
        if st.button("Restart Fast"):
            st.session_state.restart_mode = True
    else:
        st.warning("Start new fast?")
        if st.button("Confirm Start"):
            supabase.table("fasting_groups").update({
                "start_time": datetime.now().isoformat()
            }).eq("id", user["id"]).execute()

            # IMPORTANT FIX
            st.session_state.user_data["start_time"] = datetime.now().isoformat()
            st.session_state.restart_mode = False
            st.rerun()

        if st.button("Cancel"):
            st.session_state.restart_mode = False

    # --- LOGOUT ---
    if st.button("Logout"):
        st.session_state.user_data = None
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# --- LOOP ---
time.sleep(1)
st.rerun()
