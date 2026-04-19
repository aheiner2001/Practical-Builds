import streamlit as st
from supabase import create_client, Client
from streamlit_calendar import calendar
import urllib.parse

# 1. Initialize Supabase Client
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def get_bookings():
    # Pulling from public.bookings as defined in your SQL
    response = supabase.table("bookings").select("*").execute()
    return response.data

def make_maps_link(address):
    if not address: return None
    # Formats address for a clean Google Maps search
    return f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(address)}"

# 2. Page Config
st.set_page_config(page_title="Admin Bookings", layout="wide")
st.title("📅 Internal Bookings Calendar")

# Fetch Data
data = get_bookings()

# 3. Format data for the Calendar component
calendar_events = []
for entry in data:
    # Combining date and time for the calendar display
    start_dt = f"{entry['slot_date']}T{entry['start_time']}"
    
    calendar_events.append({
        "title": entry['client_name'],
        "start": start_dt,
        "id": entry['id'],
        "extendedProps": {
            "phone": entry.get('client_phone'),
            "email": entry.get('client_email'),
            "address": entry.get('service_address')
        }
    })

# 4. Calendar Settings
calendar_options = {
    "headerToolbar": {
        "left": "today prev,next",
        "center": "title",
        "right": "dayGridMonth,timeGridWeek,timeGridDay",
    },
    "initialView": "dayGridMonth",
    "slotMinTime": "06:00:00", # Adjust to your working hours
    "slotMaxTime": "22:00:00",
}

# Render
state = calendar(events=calendar_events, options=calendar_options)

# 5. The Sidebar "Contact Card"
st.sidebar.header("📋 Appointment Info")

if "eventClick" in state:
    event_data = state["eventClick"]["event"]
    props = event_data.get("extendedProps", {})
    
    st.sidebar.subheader(event_data['title'])
    st.sidebar.divider()
    
    st.sidebar.write(f"**📞 Phone:** {props.get('phone', 'N/A')}")
    st.sidebar.write(f"**✉️ Email:** {props.get('email', 'N/A')}")
    
    address = props.get('address')
    if address:
        st.sidebar.write(f"**📍 Address:**\n{address}")
        map_url = make_maps_link(address)
        st.sidebar.link_button("🚗 Open in Google Maps", map_url)
    else:
        st.sidebar.warning("No address provided for this booking.")
else:
    st.sidebar.info("Click an event on the calendar to see client contact details and address.")
