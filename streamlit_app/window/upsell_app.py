import streamlit as st
from st_supabase_connection import SupabaseConnection
import qrcode
from io import BytesIO

# 1. Page Configuration for Mobile
st.set_page_config(page_title="Glide Upsell", layout="centered")

# 2. Custom CSS for a clean mobile "App" look (Corrected Parameter)
st.markdown("""
    <style>
    /* Make buttons big and thumb-friendly */
    .stButton button { 
        width: 100%; 
        border-radius: 12px; 
        height: 3.5em; 
        background-color: #007bff; 
        color: white; 
        font-weight: bold;
        font-size: 1.1rem;
    }
    /* Background and Metric styling */
    .main { background-color: #f9f9f9; }
    div[data-testid="stMetricValue"] { color: #2e7d32; font-size: 2.2rem; }
    
    /* Style checkboxes to look like selectable cards */
    .stCheckbox { 
        padding: 15px; 
        background: white; 
        border-radius: 10px; 
        margin-bottom: 10px; 
        border: 1px solid #ddd;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Connect to Supabase
# Ensure your Secrets are set in Streamlit Cloud Settings
conn = st.connection("supabase", type=SupabaseConnection)

# 4. Routing Logic (Using URL Parameters)
query_params = st.query_params
upsell_id = query_params.get("id")

# --- CUSTOMER FLOW (The page the client sees) ---
if upsell_id:
    # Check if they just finished in this session
    if st.session_state.get("finished", False):
        st.success("### Success!\n\nYour request has been received. You may now close this browser window.")
        st.balloons()
        st.stop()

    # Fetch data for this specific ID from Supabase
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
        st.write("Review your service estimate below. Check any boxes to add these services to your appointment today.")

        # "None" Logic - if checked, it overrides others
        none_op = st.checkbox("❌ No additions today (Keep original price)", key="none_box")
        
        running_total = float(data['base_price'])
        applied_items = []

        if not none_op:
            st.divider()
            
            # Interior Price
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
            st.write("---")
            if st.checkbox("💡 Interested in Permanent Holiday Lighting?"):
                st.info(f"**Information:** {data['perm_lighting_info']}")
                applied_items.append("Perm Lighting Interest")

        st.divider()
        st.metric("Total Appointment Price", f"${running_total:,.2f}")

        if st.button("Confirm & Submit"):
            # Update Supabase with selections
            conn.table("upsell_sessions").update({
                "selected_items": applied_items,
                "final_total": running_total,
                "is_submitted": True
            }).eq("id", upsell_id).execute()
            
            # Show the thank you page
            st.session_state.finished = True
            st.rerun()

# --- ADMIN FLOW (The page you use on your phone) ---
else:
    st.title("Glide Upsell Creator")
    
    with st.form("creator_form", clear_on_submit=True):
        cust_name = st.text_input("Customer Name")
        current_price = st.number_input("Original Job Price", min_value=0.0, step=5.0)
        
        st.write("### Set Add-on Pricing")
        col1, col2 = st.columns(2)
        
        with col1:
            # Auto-calculation: 60% of base, rounded down to nearest 5
            auto_int = (current_price * 0.6) // 5 * 5
            p_interior = st.number_input("Interior Price", value=float(auto_int))
            p_screens = st.number_input("Screens Price", value=25.0)
            p_wells = st.number_input("Well Covers Price", value=25.0)
            
        with col2:
            p_gutters = st.number_input("Gutters Price", value=50.0)
            p_fans = st.number_input("Fan Price (Per)", value=10.0)
            p_mirrors = st.number_input("Mirrors Price", value=25.0)
            
        p_light_info = st.text_area("Permanent Lighting Pitch", "Interested in permanent lighting? Check for more information.")
        
        submitted = st.form_submit_button("Create & Generate QR")

    if submitted:
        if not cust_name:
            st.error("Please provide a name.")
        else:
            # Save to Database
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
            
            # Link Creation
            new_id = new_row.data[0]['id']
            # Change this to your actual deployed URL
            base_url = "https://your-app.streamlit.app/" 
            full_url = f"{base_url}?id={new_id}"
            
            st.success(f"Upsell Ready for {cust_name}!")
            
            # QR Code Generation
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(full_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            buf = BytesIO()
            img.save(buf)
            st.image(buf, caption="Let customer scan this")
            st.code(full_url)

    st.divider()
    st.subheader("Completed Upsells")
    recent = conn.table("upsell_sessions").select("*").eq("is_submitted", True).order("created_at", desc=True).limit(5).execute()
    
    if recent.data:
        for r in recent.data:
            with st.expander(f"{r['customer_name']} - Total: ${r['final_total']}"):
                st.write(f"**Added:** {', '.join(r['selected_items']) if r['selected_items'] else 'None'}")
                st.write(f"**Original Price:** ${r['base_price']}")
    else:
        st.info("No customer submissions found.")
