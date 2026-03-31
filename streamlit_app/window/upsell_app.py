
import streamlit as st
from st_supabase_connection import SupabaseConnection
import qrcode
from io import BytesIO

# Page Config for Mobile
st.set_page_config(page_title="Glide Upsell", layout="centered")

# CSS for Mobile Styling
st.markdown("""
    <style>
    .stButton button { width: 100%; border-radius: 10px; height: 3em; background-color: #007bff; color: white; }
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; }
    </style>
    """, unsafe_all_white_space=True)

# Initialize Supabase
conn = st.connection("supabase", type=SupabaseConnection)

# --- ROUTING LOGIC ---
query_params = st.query_params
upsell_id = query_params.get("id")

if upsell_id:
    # --- CUSTOMER VIEW ---
    res = conn.table("upsell_sessions").select("*").eq("id", upsell_id).execute()
    
    if not res.data:
        st.error("Upsell link expired or invalid.")
    else:
        data = res.data[0]
        st.header(f"Special Offers for {data['customer_name']}")
        
        # Calculation Logic
        if 'selections' not in st.session_state:
            st.session_state.selections = []
            st.session_state.fan_count = 1

        # "None" Logic
        none_op = st.checkbox("No additions today", key="none_box")
        
        running_total = float(data['base_price'])
        applied_items = []

        if not none_op:
            st.divider()
            # Interior
            if st.checkbox(f"Interior Cleaning (+${data['interior_price']:.0f})"):
                running_total += float(data['interior_price'])
                applied_items.append("Interior")
            
            # Screens
            if st.checkbox(f"Screen Deep Clean (+${data['screens_price']:.0f})"):
                running_total += float(data['screens_price'])
                applied_items.append("Screens")

            # Fans
            if st.checkbox(f"Ceiling Fans (+${data['fan_price']:.0f} ea)"):
                count = st.number_input("How many fans?", min_value=1, value=1)
                running_total += (float(data['fan_price']) * count)
                applied_items.append(f"Fans ({count})")

            # Others
            if st.checkbox(f"Gutter Debris Removal (+${data['gutters_price']:.0f})"):
                running_total += float(data['gutters_price'])
                applied_items.append("Gutters")
            
            if st.checkbox(f"Mirror Cleaning (+${data['mirrors_price']:.0f})"):
                running_total += float(data['mirrors_price'])
                applied_items.append("Mirrors")

            if st.checkbox("Interested in Permanent Lighting?"):
                st.info(f"Note: {data['perm_lighting_info']}")
                applied_items.append("Perm Lighting Interest")

        st.metric("Total Price", f"${running_total:,.2f}")

        if st.button("Confirm & Submit"):
            conn.table("upsell_sessions").update({
                "selected_items": applied_items,
                "final_total": running_total,
                "is_submitted": True
            }).eq("id", upsell_id).execute()
            st.success("Thank you! I've been notified.")

else:
    # --- ADMIN VIEW (YOU) ---
    st.title("Create New Upsell")
    name = st.text_input("Customer Name")
    base = st.number_input("Current Job Price", min_value=0.0, step=5.0)
    
    with st.expander("Customize Upsell Prices"):
        # Interior: .6 of original rounded down to nearest 5
        calc_int = (base * 0.6) // 5 * 5
        int_p = st.number_input("Interior Price", value=float(calc_int))
        scr_p = st.number_input("Screens Price", value=25.0)
        gut_p = st.number_input("Gutters Price", value=50.0)
        fan_p = st.number_input("Fan Price (Per)", value=10.0)
        mir_p = st.number_input("Mirrors Price", value=25.0)
        perm_info = st.text_area("Permanent Lighting Details", "We use high-quality LED trim.")

    if st.button("Create Upsell Page"):
        new_row = conn.table("upsell_sessions").insert({
            "customer_name": name,
            "base_price": base,
            "interior_price": int_p,
            "screens_price": scr_p,
            "gutters_price": gut_p,
            "fan_price": fan_p,
            "mirrors_price": mir_p,
            "perm_lighting_info": perm_info
        }).execute()
        
        new_id = new_row.data[0]['id']
        # Generate URL (Replace with your actual streamlit URL)
        url = f"https://your-app-url.streamlit.app/?id={new_id}"
        
        st.write("### Customer QR Code")
        qr = qrcode.make(url)
        buf = BytesIO()
        qr.save(buf)
        st.image(buf)
        st.code(url)

    st.divider()
    st.subheader("Recent Submissions")
    subs = conn.table("upsell_sessions").select("*").eq("is_submitted", True).order("created_at", desc=True).limit(5).execute()
    for s in subs.data:
        st.write(f"**{s['customer_name']}** added: {', '.join(s['selected_items'])} | Total: ${s['final_total']}")
