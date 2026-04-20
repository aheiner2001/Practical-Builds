import streamlit as st
import os
import requests
from datetime import datetime, date, time, timedelta
import calendar
import streamlit as st
from st_supabase_connection import SupabaseConnection
import qrcode
from io import BytesIO
import math
from datetime import datetime
from dotenv import load_dotenv
import os
from pathlib import Path
import pandas as pd

st.set_page_config(
    page_title="FreshPane Solutions LLC",
    page_icon="🪟",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BUSINESS_NAME = "FreshPane Solutions LLC"
BUSINESS_SUB  = "Window Cleaning"
BOOKING_NOTE  = "60-min appointment · We bring all equipment"
# add business logo
script_path = Path(__file__).resolve().parent
logo_path = script_path / "logofreshpoane.png"
    
#     # 3. Add the logo (check if exists first to avoid crashes)
# if logo_path.exists():
#     st.image(str(logo_path), width=120)
# else:
#     st.warning("Logo image not found at 'logofreshpoane.png'. Please add your logo to the project directory.")



SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("⚠️ Missing Supabase credentials. Add SUPABASE_URL and SUPABASE_KEY to your Streamlit secrets.")
    st.stop()

def sb_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

def sb_get(table, params=None):
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{table}", headers=sb_headers(), params=params or {})
    r.raise_for_status()
    return r.json()

def sb_post(table, payload):
    r = requests.post(f"{SUPABASE_URL}/rest/v1/{table}", headers=sb_headers(), json=payload)
    r.raise_for_status()
    return r.json()

def sb_delete(table, params):
    r = requests.delete(f"{SUPABASE_URL}/rest/v1/{table}", headers=sb_headers(), params=params)
    r.raise_for_status()

def sb_patch(table, params, payload):
    r = requests.patch(f"{SUPABASE_URL}/rest/v1/{table}", headers=sb_headers(), params=params, json=payload)
    r.raise_for_status()

@st.cache_data(ttl=30)
def get_settings():
    rows = sb_get("settings")
    return {r["key"]: r["value"] for r in rows}

@st.cache_data(ttl=30)
def get_recurring():
    rows = sb_get("recurring_slots", {"order": "day_of_week,start_time"})
    result = {d: [] for d in ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]}
    for r in rows:
        result[r["day_of_week"]].append(r["start_time"])
    return result

@st.cache_data(ttl=15)
def get_extra_availability():
    rows = sb_get("extra_availability", {"order": "slot_date,start_time"})
    result = {}
    for r in rows:
        result.setdefault(r["slot_date"], []).append(r["start_time"])
    return result

@st.cache_data(ttl=15)
def get_blocked():
    rows = sb_get("blocked_slots", {"order": "slot_date,start_time"})
    result = {}
    for r in rows:
        result.setdefault(r["slot_date"], []).append(r["start_time"])
    return result

@st.cache_data(ttl=15)
def get_bookings():
    rows = sb_get("bookings", {"order": "slot_date,start_time"})
    result = {}
    for r in rows:
        result.setdefault(r["slot_date"], []).append(r["start_time"])
    return result

def clear_cache():
    get_settings.clear()
    get_recurring.clear()
    get_extra_availability.clear()
    get_blocked.clear()
    get_bookings.clear()

def slots_for_date(d):
    day_name = d.strftime("%A")
    date_str = d.isoformat()
    base    = set(get_recurring().get(day_name, []))
    extra_a = set(get_extra_availability().get(date_str, []))
    extra_u = get_blocked().get(date_str, [])
    bkd     = set(get_bookings().get(date_str, []))
    slots   = base | extra_a
    if "ALL" in extra_u:
        slots = set()
    else:
        slots -= set(extra_u)
    slots -= bkd
    return sorted(slots)

def fmt_time(t):
    h, m = map(int, t.split(":"))
    suf  = "AM" if h < 12 else "PM"
    return f"{h % 12 or 12}:{m:02d} {suf}"

def all_possible_slots(dur):
    slots, t = [], datetime.combine(date.today(), time(6, 0))
    end = datetime.combine(date.today(), time(19, 0))
    while t <= end:
        slots.append(t.strftime("%H:%M"))
        t += timedelta(minutes=dur)
    return slots

def get_slot_duration():
    return int(get_settings().get("slot_duration", 60))

def get_admin_password():
    return get_settings().get("admin_password", "admin123")

if "admin_auth"    not in st.session_state: st.session_state.admin_auth = False
if "selected_date" not in st.session_state: st.session_state.selected_date = None
if "cal_month"     not in st.session_state: st.session_state.cal_month = date.today().replace(day=1)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');
html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }
.stApp { background: linear-gradient(160deg, #e8f4fd 0%, #f0f8ff 40%, #e2eff9 100%); min-height: 100vh; color: #1a2a3a; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.5rem; max-width: 1080px; }
div[data-testid="stButton"] > button {
    background: white; color: #1e6fa8; border: 1.5px solid #b8d9f0; border-radius: 10px;
    padding: 0.45rem 0.8rem; font-family: 'Outfit', sans-serif; font-size: 0.82rem; font-weight: 600;
    letter-spacing: 0.03em; transition: all 0.18s ease; width: 100%; box-shadow: 0 1px 4px rgba(30,111,168,0.08);
}
div[data-testid="stButton"] > button:hover { background: #1e6fa8; color: white; border-color: #1e6fa8; transform: translateY(-2px); box-shadow: 0 6px 20px rgba(30,111,168,0.25); }
div[data-testid="stButton"] > button[kind="primary"] { background: #1e6fa8; color: white; border-color: #1e6fa8; }
div[data-testid="stButton"] > button[kind="primary"]:hover { background: #155d90; box-shadow: 0 6px 24px rgba(30,111,168,0.35); }
.cal-cell { background: white; border: 1.5px solid #d4e9f7; border-radius: 12px; padding: 10px 6px 8px; text-align: center; min-height: 72px; transition: all 0.18s ease; box-shadow: 0 1px 3px rgba(30,111,168,0.06); }
.cal-cell.has-slots { border-color: #7bbfe0; }
.cal-cell.has-slots:hover { background: #e8f4fd; border-color: #1e6fa8; transform: translateY(-2px); box-shadow: 0 6px 18px rgba(30,111,168,0.18); }
.cal-cell.selected { background: #1e6fa8 !important; border-color: #1e6fa8 !important; }
.cal-cell.selected .day-num { color: white !important; }
.cal-cell.selected .slot-count { color: rgba(255,255,255,0.8) !important; }
.cal-cell.today { border-color: #f0a500 !important; }
.cal-cell.past  { opacity: 0.38; }
.cal-cell.empty { background: transparent; border-color: transparent; box-shadow: none; }
.day-num { font-size: 1.05rem; font-weight: 700; color: #1a2a3a; line-height: 1; }
.today-dot { width:5px;height:5px;background:#f0a500;border-radius:50%;margin:3px auto 0; }
.slot-pip { width:6px;height:6px;background:#1e6fa8;border-radius:50%;display:inline-block;margin:5px 1px 0; }
.cal-cell.selected .slot-pip { background: rgba(255,255,255,0.7); }
.slot-count { font-size:0.6rem;color:#1e6fa8;font-weight:700;letter-spacing:0.05em;margin-top:3px; }
.dow-hdr { text-align:center;font-size:0.68rem;font-weight:700;letter-spacing:0.14em;color:#5a8aaa;text-transform:uppercase;padding-bottom:10px; }
.hero-card { background: linear-gradient(135deg, #1e6fa8 0%, #0d4f7c 100%); border-radius: 20px; padding: 2.2rem 2.5rem; margin-bottom: 1.8rem; position: relative; overflow: hidden; box-shadow: 0 8px 32px rgba(30,111,168,0.3); }
.hero-card::before { content: '🪟'; position: absolute; right: 2rem; top: 50%; transform: translateY(-50%); font-size: 5rem; opacity: 0.15; }
.hero-label { font-size:0.7rem;letter-spacing:0.2em;color:rgba(255,255,255,0.6);text-transform:uppercase;font-weight:600;margin-bottom:0.3rem; }
.hero-title { font-family:'Playfair Display',serif;font-size:2.4rem;color:white;line-height:1.1;margin:0; }
.hero-sub   { color:rgba(255,255,255,0.7);font-size:0.88rem;margin-top:0.5rem; }
.confirm-card { background:white;border:2px solid #1e6fa8;border-radius:16px;padding:1.5rem 1.8rem;margin-top:1.2rem;box-shadow:0 4px 20px rgba(30,111,168,0.12); }
.footer-lnk { color:#7bbfe0 !important;text-decoration:none;font-weight:600; }
hr { border-color: #c8dff0; }
</style>
""", unsafe_allow_html=True)

admin_mode = st.query_params.get("admin", "false").lower() == "true"

# ══════════════════════════════════════════════════════════════════════════════
# ADMIN
# ══════════════════════════════════════════════════════════════════════════════
if admin_mode:
    if not st.session_state.admin_auth:
        st.markdown("<br><br>", unsafe_allow_html=True)
        cols = st.columns([1,2,1])
        with cols[1]:
            st.markdown("""<div style='text-align:center;margin-bottom:1.5rem'><div style='font-size:2.5rem'>🪟</div><h2 style='font-family:"Playfair Display",serif;margin:0.3rem 0 0'>Admin Login</h2><p style='color:#5a8aaa;font-size:0.85rem'>Crystal Clear Scheduling</p></div>""", unsafe_allow_html=True)
            pw = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Enter admin password")
            if st.button("Sign In →", use_container_width=True, type="primary"):
                if pw == get_admin_password():
                    st.session_state.admin_auth = True; st.rerun()
                else:
                    st.error("Incorrect password.")
        st.stop()

    st.markdown("""<div style='display:flex;align-items:center;gap:0.8rem;margin-bottom:1.2rem'><span style='font-size:1.6rem'>🪟</span><div><div style='font-family:"Playfair Display",serif;font-size:1.5rem;color:#1a2a3a;line-height:1'>Crystal Clear</div><div style='font-size:0.72rem;letter-spacing:0.15em;color:#5a8aaa;text-transform:uppercase'>Schedule Admin</div></div></div>""", unsafe_allow_html=True)

    tabs = st.tabs(["📅 Recurring", "➕ Add Availability", "🚫 Block Time", "📋 Bookings", "⚙️ Settings"])

    with tabs[0]:
        st.markdown("### Weekly Recurring Schedule")
        st.caption("These slots repeat every week by default.")
        dur = get_slot_duration()
        ap  = all_possible_slots(dur)
        rec = get_recurring()
        for day in ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]:
            with st.expander(day):
                cur_slots = rec.get(day, [])
                sel = st.multiselect(f"Open slots — {day}", ap, default=cur_slots, format_func=fmt_time, key=f"rec_{day}")
                if st.button(f"💾 Save {day}", key=f"save_{day}"):
                    try:
                        sb_delete("recurring_slots", {"day_of_week": f"eq.{day}"})
                        if sel:
                            sb_post("recurring_slots", [{"day_of_week": day, "start_time": s} for s in sel])
                        clear_cache(); st.success(f"{day} saved!"); st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    with tabs[1]:
        st.markdown("### Add One-Off Availability")
        st.caption("Open extra slots on a specific date.")
        c1, c2 = st.columns(2)
        with c1: ea_date = st.date_input("Date", min_value=date.today(), key="ea_d")
        with c2: ea_slots = st.multiselect("Slots to open", all_possible_slots(get_slot_duration()), format_func=fmt_time, key="ea_s")
        if st.button("➕ Add These Slots", type="primary"):
            for s in ea_slots:
                try:
                    sb_post("extra_availability", {"slot_date": ea_date.isoformat(), "start_time": s})
                except Exception:
                    pass
            clear_cache(); st.success(f"Added {len(ea_slots)} slot(s) on {ea_date.strftime('%b %d')}"); st.rerun()
        st.divider()
        st.markdown("**Upcoming extra availability:**")
        ea = get_extra_availability(); shown = False
        for ds, slots in sorted(ea.items()):
            if date.fromisoformat(ds) >= date.today():
                shown = True
                c1, c2 = st.columns([4,1])
                with c1: st.write(f"**{date.fromisoformat(ds).strftime('%A, %b %d')}** — {', '.join(fmt_time(s) for s in slots)}")
                with c2:
                    if st.button("Remove", key=f"rmea_{ds}"):
                        sb_delete("extra_availability", {"slot_date": f"eq.{ds}"}); clear_cache(); st.rerun()
        if not shown: st.caption("None added.")

    with tabs[2]:
        st.markdown("### Block Time Off")
        st.caption("Block specific slots or an entire day.")
        bl_type = st.radio("Block type", ["Specific slots","Entire day"], horizontal=True)
        bl_date = st.date_input("Date to block", min_value=date.today(), key="bl_d")
        if bl_type == "Entire day":
            if st.button("🚫 Block Entire Day", type="primary"):
                try:
                    sb_delete("blocked_slots", {"slot_date": f"eq.{bl_date.isoformat()}"})
                    sb_post("blocked_slots", {"slot_date": bl_date.isoformat(), "start_time": "ALL"})
                    clear_cache(); st.success(f"Blocked {bl_date.strftime('%b %d, %Y')}"); st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            avail = sorted(set(get_recurring().get(bl_date.strftime("%A"), [])) | set(get_extra_availability().get(bl_date.isoformat(), [])))
            bl_slots = st.multiselect("Slots to block", avail, format_func=fmt_time, key="bl_s")
            if st.button("🚫 Block Selected", type="primary"):
                for s in bl_slots:
                    try:
                        sb_post("blocked_slots", {"slot_date": bl_date.isoformat(), "start_time": s})
                    except Exception:
                        pass
                clear_cache(); st.success(f"Blocked {len(bl_slots)} slot(s)."); st.rerun()
        st.divider()
        st.markdown("**Active blocks:**")
        bl = get_blocked(); shown = False
        for ds, slots in sorted(bl.items()):
            if date.fromisoformat(ds) >= date.today():
                shown = True
                c1, c2 = st.columns([4,1])
                with c1:
                    label = "ENTIRE DAY" if "ALL" in slots else ", ".join(fmt_time(s) for s in slots)
                    st.write(f"**{date.fromisoformat(ds).strftime('%A, %b %d')}** — {label}")
                with c2:
                    if st.button("Unblock", key=f"rmbl_{ds}"):
                        sb_delete("blocked_slots", {"slot_date": f"eq.{ds}"}); clear_cache(); st.rerun()
        if not shown: st.caption("No blocks set.")

    with tabs[3]:
        st.markdown("### Upcoming Bookings")
        try:
            rows = sb_get("bookings", {"slot_date": f"gte.{date.today().isoformat()}", "order": "slot_date,start_time"})
        except Exception as e:
            st.error(f"Could not load bookings: {e}"); rows = []
        if rows:
            by_date = {}
            for r in rows:
                by_date.setdefault(r["slot_date"], []).append(r)
            for ds, appts in sorted(by_date.items()):
                st.markdown(f"**{date.fromisoformat(ds).strftime('%A, %B %d, %Y')}**")
                for appt in appts:
                    c1, c2, c3, c4 = st.columns([2,2,3,1])
                    with c1: st.write(f"🕐 {fmt_time(appt['start_time'])}")
                    with c2: st.write(appt["client_name"])
                    with c3: st.caption(appt.get("service_address","") or appt.get("client_email",""))
                    with c4:
                        if st.button("Cancel", key=f"can_{appt['id']}"):
                            sb_delete("bookings", {"id": f"eq.{appt['id']}"}); clear_cache(); st.rerun()
                st.divider()
        else:
            st.info("No upcoming bookings yet.")

    with tabs[4]:
        st.markdown("### Settings")
        cur_dur = get_slot_duration()
        new_dur = st.selectbox("Slot duration (minutes)", [30,45,60,90,120], index=[30,45,60,90,120].index(cur_dur))
        new_pw  = st.text_input("Admin password", value=get_admin_password())
        if st.button("💾 Save Settings", type="primary"):
            try:
                sb_patch("settings", {"key": "eq.slot_duration"}, {"value": str(new_dur)})
                sb_patch("settings", {"key": "eq.admin_password"}, {"value": new_pw})
                clear_cache(); st.success("Settings saved!")
            except Exception as e:
                st.error(f"Error: {e}")
        st.divider()
        st.caption("Credentials: SUPABASE_URL and SUPABASE_KEY in Streamlit secrets")
        st.divider()
        if st.button("🔓 Log Out"):
            st.session_state.admin_auth = False; st.rerun()
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# CLIENT VIEW
# ══════════════════════════════════════════════════════════════════════════════
today = date.today()

# ══════════════════════════════════════════════════════════════════════════════
# CLIENT VIEW
# ══════════════════════════════════════════════════════════════════════════════
today = date.today()

# Create two columns for the Logo and the Business Title
col_logo, col_text = st.columns([1, 4])

with col_logo:
    if logo_path.exists():
        st.image(str(logo_path), width=150)
    else:
        # Fallback if image isn't found
        st.markdown("<h1 style='font-size: 80px; margin: 0;'>🪟</h1>", unsafe_allow_html=True)

with col_text:
    st.markdown(f"""
        <div style="padding-top: 10px;">
            <div style="font-size: 0.75rem; letter-spacing: 0.2em; color: #5a8aaa; text-transform: uppercase; font-weight: 600; margin-bottom: 0.2rem;">
                Professional Window Cleaning
            </div>
            <h1 style="font-family: 'Playfair Display', serif; font-size: 2.8rem; color: #1a2a3a; margin: 0; line-height: 1.1;">
                {BUSINESS_NAME}
            </h1>
            <div style="color: #1e6fa8; font-size: 1.1rem; font-weight: 500; margin-top: 0.2rem;">
                {BUSINESS_SUB}
            </div>
            <div style="color: #5a8aaa; font-size: 0.85rem; margin-top: 0.5rem;">
                📍 Schedule your appointment below &nbsp;·&nbsp; {BOOKING_NOTE}
            </div>
        </div>
    """, unsafe_allow_html=True)

st.divider()
cur = st.session_state.cal_month
c_prev, c_title, c_next = st.columns([1,4,1])
with c_prev:
    if cur > today.replace(day=1):
        if st.button("← Back"):
            prev = (cur.replace(day=1) - timedelta(days=1)).replace(day=1)
            st.session_state.cal_month = prev; st.rerun()
with c_next:
    if cur < today.replace(day=1) + timedelta(days=90):
        if st.button("Next →"):
            last = calendar.monthrange(cur.year, cur.month)[1]
            st.session_state.cal_month = (cur.replace(day=last) + timedelta(days=1)).replace(day=1); st.rerun()
with c_title:
    st.markdown(f"<div style='text-align:center;font-family:\"Playfair Display\",serif;font-size:1.7rem;color:#1a2a3a;font-weight:700'>{cur.strftime('%B %Y')}</div>", unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
hdr_cols = st.columns(7)
for i, dn in enumerate(["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]):
    with hdr_cols[i]:
        st.markdown(f"<div class='dow-hdr'>{dn}</div>", unsafe_allow_html=True)

sel_date = st.session_state.selected_date
for week in calendar.monthcalendar(cur.year, cur.month):
    wcols = st.columns(7)
    for i, day_num in enumerate(week):
        with wcols[i]:
            if day_num == 0:
                st.markdown("<div class='cal-cell empty'></div>", unsafe_allow_html=True); continue
            d        = date(cur.year, cur.month, day_num)
            n_slots  = len(slots_for_date(d))
            is_today = d == today; is_past = d < today; is_sel = d == sel_date
            cls = "cal-cell" + (" past" if is_past else " has-slots" if n_slots else "") + (" today" if is_today else "") + (" selected" if is_sel else "")
            pips   = "".join("<span class='slot-pip'></span>" for _ in range(min(n_slots, 5)))
            tdot   = "<div class='today-dot'></div>" if is_today else ""
            scount = f"<div class='slot-count'>{n_slots} open</div>" if n_slots and not is_past else ""
            st.markdown(f"<div class='{cls}'><div class='day-num'>{day_num}</div>{tdot}{pips}{scount}</div>", unsafe_allow_html=True)
            if not is_past and n_slots > 0:
                if st.button(f"{day_num}: Click Here", key=f"c_{d.isoformat()}", help=f"{n_slots} slot(s)", use_container_width=True):
                    st.session_state.selected_date = d
                    st.session_state.pop("confirm_slot", None); st.session_state.pop("confirm_date", None); st.rerun()

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
st.divider()

if st.session_state.selected_date:
    sel     = st.session_state.selected_date
    o_slots = slots_for_date(sel)
    dur     = get_slot_duration()
    st.markdown(f"<div style='font-family:\"Playfair Display\",serif;font-size:1.4rem;color:#1a2a3a;margin-bottom:0.2rem'>{sel.strftime('%A, %B %d')}<span style='font-size:0.85rem;font-weight:400;color:#5a8aaa;font-family:Outfit,sans-serif;margin-left:0.6rem'>{len(o_slots)} slot{'s' if len(o_slots)!=1 else ''} available</span></div>", unsafe_allow_html=True)
    if not o_slots:
        st.warning("No open slots on this day.")
    else:
        st.caption(f"Each appointment is {dur} minutes. Select your preferred time:")
        slot_cols = st.columns(min(len(o_slots), 5))
        for idx, slot in enumerate(o_slots):
            with slot_cols[idx % 5]:
                if st.button(fmt_time(slot), key=f"slot_{slot}"):
                    st.session_state["confirm_slot"] = slot; st.session_state["confirm_date"] = sel

        if st.session_state.get("confirm_slot") and st.session_state.get("confirm_date") == sel:
            cslot  = st.session_state["confirm_slot"]
            end_dt = datetime.combine(sel, datetime.strptime(cslot, "%H:%M").time()) + timedelta(minutes=dur)
            st.markdown(f"""<div class='confirm-card'><div style='font-size:0.68rem;letter-spacing:0.18em;color:#5a8aaa;text-transform:uppercase;font-weight:700;margin-bottom:0.4rem'>Confirm your appointment</div><div style='font-family:"Playfair Display",serif;font-size:1.5rem;color:#1a2a3a'>{sel.strftime('%B %d, %Y')}</div><div style='font-size:1.1rem;color:#1e6fa8;font-weight:600;margin-top:0.2rem'>🕐 {fmt_time(cslot)} – {end_dt.strftime("%-I:%M %p")}</div><div style='color:#5a8aaa;font-size:0.8rem;margin-top:0.3rem'>Window cleaning · {dur} min</div></div>""", unsafe_allow_html=True)
            name  = st.text_input("Your name",        placeholder="First & last name", key="bk_name")
            email = st.text_input("Email address",    placeholder="you@email.com",    key="bk_email")
            phone = st.text_input("Phone (optional)", placeholder="(555) 000-0000",   key="bk_phone")
            addr  = st.text_input("Service address",  placeholder="123 Main St",      key="bk_addr")
            bc1, bc2 = st.columns(2)
            with bc1:
                if st.button("✓ Confirm Booking", use_container_width=True, type="primary"):
                    if not name.strip(): st.error("Please enter your name.")
                    elif "@" not in email: st.error("Please enter a valid email.")
                    else:
                        try:
                            sb_post("bookings", {"slot_date": sel.isoformat(), "start_time": cslot, "client_name": name.strip(), "client_email": email.strip(), "client_phone": phone.strip() or None, "service_address": addr.strip() or None})
                            clear_cache()
                            st.session_state.pop("confirm_slot", None); st.session_state.pop("confirm_date", None)
                            st.session_state["success"] = (sel, cslot, name); st.rerun()
                        except Exception as e:
                            st.error(f"Booking failed (slot may already be taken): {e}")
            with bc2:
                if st.button("✕ Choose Different Time", use_container_width=True):
                    st.session_state.pop("confirm_slot", None); st.session_state.pop("confirm_date", None); st.rerun()
else:
    st.markdown("""<div style='text-align:center;padding:2.5rem 0 1rem;color:#9ab8cc'><div style='font-size:2.5rem'>📅</div><div style='margin-top:0.6rem;font-size:0.9rem;font-weight:500'>Pick a highlighted date above to view available times</div></div>""", unsafe_allow_html=True)

if "success" in st.session_state:
    sel, slot, name = st.session_state.pop("success")
    st.balloons()
    st.success(f"🎉 Booked! See you {sel.strftime('%B %d')} at {fmt_time(slot)}, {name.split()[0]}! We'll confirm your address shortly.")

st.markdown("""<div style='text-align:center;padding:2.5rem 0 0.5rem;font-size:0.72rem;letter-spacing:0.08em;color:#9ab8cc'>Questions? Call or text us &nbsp;·&nbsp; <a href='?admin=true' class='footer-lnk'>Admin →</a></div>""", unsafe_allow_html=True)
