import streamlit as st
from st_supabase_connection import SupabaseConnection
import qrcode
from io import BytesIO

# 1. Page Configuration for Mobile
st.set_page_config(page_title="Glide Upsell", layout="centered")

# Custom CSS for a clean mobile "App" look
st.markdown("""
    <style>
    .stButton button { 
        width: 100%; 
        border-radius: 12px; 
        height: 3.5em; 
        background-color: #007bff; 
        color: white; 
        font-weight: bold;
        font-size: 1.1rem;
    }
    .main { background-color: #f9f9f9; }
    div[data-testid="stMetricValue"] { color: #2e7d32; font-size: 2.2rem; }
    .stCheckbox { padding: 10px; background: white; border-radius: 8px; margin-bottom: 5px; border: 1px solid #eee; }
    </style>
    """, unsafe_all_white_space=True)

# 2. Connect to Supabase
conn = st.connection("supabase", type=SupabaseConnection)

# 3. Routing Logic (Checking URL Parameters)
query_params = st.query_params
upsell_id = query_params.get("id")

# --- CUSTOMER FLOW ---
if upsell_id:
    # Check if they just finished in this session
    if st.session_state.get("finished", False):
        st.success("### Success!\n\nYour request has been sent. You may now close this browser window.")
        st.balloons()
        st.stop()

    # Fetch data for this specific ID
    res = conn.table("upsell_sessions").select("*").eq("id", upsell_id).execute()
    
    if not res.data:
        st.error("This link is no longer active.")
    else:
        data = res.data[0]
        
        # Check if already submitted in the database
        if data.get('is_submitted'):
            st.info("This request has already been processed. Thank you!")
            st.stop()

        st.title(f"Hello, {data['customer_name']}!")
        st.write("Review your estimate below and add any additional services you'd like performed today.")

        # Pricing Logic
        none_op = st.checkbox("❌ None (Keep original price only)", key="none_box")
        
        running_total = float(data['base_price'])
        applied_items = []

        if not none_op:
            st.divider()
            
            # Interior (.6 of base, rounded down to nearest 5)
            if st.checkbox(f"🏠 Interior Windows (+${data['interior_price']:.0f})"):
                running_total += float(data['interior_price'])
                applied_items.append("Interior")
            
            # Screens
            if st.checkbox(f"🖼️ Screen Deep Clean (+${data['screens_price']:.0f})"):
                running_total += float(data['screens_price'])
                applied_items.append("Screens")

            # Fans
            if st.checkbox(f"🌀 Ceiling Fans (+${data['fan_price']:.0f} ea)"):
                fan_count = st.number_input("How many fans?", min_value=1, value=1, step=1)
                running_total += (float(data['fan_price']) * fan_count)
                applied_items.append(f"Fans ({fan_count})")

            # Gutters
            if st.checkbox(f"🍂 Gutter Debris Removal (+${data['gutters_price']:.0f})"):
                running_total += float(data['gutters_price'])
                applied_items.append("Gutters")
            
            # Window Well Covers
            if st.checkbox(f"🛡️ Window Well Covers (+${data['well_covers_price']:.0f})"):
                running_total += float(data['well_covers_price'])
                applied_items.append("Well Covers")

            # Mirrors
            if st.checkbox(f"🪞 Mirror Cleaning (+${data['mirrors_price']:.0f})"):
                running_total += float(data['mirrors_price'])
                applied_items.append("Mirrors")

            # Permanent Lighting
            if st.checkbox("💡 Interested in Permanent Holiday Lighting?"):
                st.info(f"**Details:** {data['perm_lighting_info']}")
                applied_items.append("Perm Lighting Info Requested")

        st.divider()
        st.metric("Total Estimate", f"${running_total:,.2f}")

        if st.button("Confirm Add-Ons"):
            conn.table("upsell_sessions").update({
                "selected_items": applied_items,
                "final_total": running_total,
                "is_submitted": True
            }).eq("id", upsell_id).execute()
            
            st.session_state.finished = True
            st.rerun()

# --- ADMIN FLOW (Your Phone) ---
else:
    st.title("Glide Upsell Creator")
    
    with st.form("creator_form"):
        cust_name = st.text_input("Customer Name")
        current_price = st.number_input("Base Price", min_value=0.0, step=10.0)
        
        st.write("### Adjust Add-on Pricing")
        col1, col2 = st.columns(2)
        
        with col1:
            # Auto-calc interior (60% of base rounded down to nearest 5)
            auto_int = (current_price * 0.6) // 5 * 5
            p_interior = st.number_input("Interior", value=float(auto_int))
            p_screens = st.number_input("Screens", value=25.0)
            p_wells = st.number_input("Well Covers", value=25.0)
            
        with col2:
            p_gutters = st.number_input("Gutters", value=50.0)
            p_fans = st.number_input("Fans (per)", value=10.0)
            p_mirrors = st.number_input("Mirrors", value=25.0)
            
        p_light_info = st.text_area("Perm Lighting Text", "Check for more information on our permanent year-round lighting solutions!")
        
        submitted = st.form_submit_button("Generate Upsell QR")

    if submitted:
        if not cust_name:
            st.error("Please enter a customer name.")
        else:
            # Insert into Supabase
            new_row = conn.table("upsell_sessions").insert({
                "customer_name": cust_name,
                "base_price": current_price,
                "interior_price": p_interior,
                "screens_price": p_screens,
                "well_covers_price": p_wells,
                "gutters_price": p_gutters,
                "fan_price": p_fans,
                "mirrors_price": p_mirrors,
                "perm_lighting_info": p_light_info
            }).execute()
            
            # Create Link
            new_id = new_row.data[0]['id']
            # IMPORTANT: Change this URL to your actual Streamlit Cloud URL once deployed
            base_url = "https://your-app-name.streamlit.app/" 
            full_url = f"{base_url}?id={new_id}"
            
            st.success("Upsell Created!")
            
            # QR Code Generation
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(full_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            buf = BytesIO()
            img.save(buf)
            st.image(buf, caption="Customer scans this")
            st.code(full_url)

    st.divider()
    st.subheader("Recent Customer Submissions")
    recent = conn.table("upsell_sessions").select("*").eq("is_submitted", True).order("created_at", desc=True).limit(10).execute()
    
    if recent.data:
        for r in recent.data:
            with st.expander(f"{r['customer_name']} - ${r['final_total']}"):
                st.write(f"**Add-ons Selected:** {', '.join(r['selected_items']) if r['selected_items'] else 'None'}")
                st.write(f"**Final Price:** ${r['final_total']}")
    else:
        st.info("No submissions yet today.")
