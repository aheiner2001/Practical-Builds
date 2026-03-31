import streamlit as st
from st_supabase_connection import SupabaseConnection
import qrcode
from io import BytesIO

# 1. Page Configuration
st.set_page_config(page_title="Glide Upsell", layout="centered")

# 2. Custom CSS (Mobile-First)
st.markdown("""
    <style>
    .stButton button { 
        width: 100%; border-radius: 12px; height: 3.5em; 
        background-color: #007bff; color: white; font-weight: bold;
    }
    .main { background-color: #f9f9f9; }
    div[data-testid="stMetricValue"] { color: #2e7d32; font-size: 2.2rem; }
    .stCheckbox { 
        padding: 12px; background: white; border-radius: 10px; 
        margin-bottom: 8px; border: 1px solid #ddd;
    }
    /* Remove the +/- spinners from number inputs for a cleaner look */
    input[type=number]::-webkit-inner-spin-button, 
    input[type=number]::-webkit-outer-spin-button { 
        -webkit-appearance: none; margin: 0; 
    }
    input[type=number] { -moz-appearance: textfield; }
    </style>
    """, unsafe_allow_html=True)

# 3. Supabase Connection
conn = st.connection("supabase", type=SupabaseConnection)

# 4. Routing
query_params = st.query_params
upsell_id = query_params.get("id")

# --- CUSTOMER FLOW ---
if upsell_id:
    if st.session_state.get("finished", False):
        st.success("### Thanks! \n\nYou may now close this browser.")
        st.balloons()
        st.stop()

    res = conn.table("upsell_sessions").select("*").eq("id", upsell_id).execute()
    
    if not res.data:
        st.error("Invalid Link.")
    else:
        data = res.data[0]
        if data.get('is_submitted'):
            st.info("Request already processed. Thank you!")
            st.stop()

        st.title(f"Hello, {data['customer_name']}!")
        
        none_op = st.checkbox("❌ None (Keep original price)", key="none_box")
        running_total = float(data['base_price'])
        applied_items = []

        if not none_op:
            st.divider()
            # Only show if price is NOT 0 (which means admin excluded it)
            if data['interior_price'] > 0:
                if st.checkbox(f"🏠 Interior Windows (${data['interior_price']:.0f})"):
                    running_total += float(data['interior_price']); applied_items.append("Interior")
            
            if data['screens_price'] > 0:
                if st.checkbox(f"🖼️ Screen Deep Clean (${data['screens_price']:.0f})"):
                    running_total += float(data['screens_price']); applied_items.append("Screens")

            if data['fan_price'] > 0:
                if st.checkbox(f"🌀 Ceiling Fans (${data['fan_price']:.0f} ea)"):
                    fan_count = st.number_input("How many?", min_value=1, value=1, step=1, label_visibility="collapsed")
                    running_total += (float(data['fan_price']) * fan_count); applied_items.append(f"Fans ({fan_count})")

            if data['gutters_price'] > 0:
                if st.checkbox(f"🍂 Gutter Cleaning (${data['gutters_price']:.0f})"):
                    running_total += float(data['gutters_price']); applied_items.append("Gutters")
            
            if data['well_covers_price'] > 0:
                if st.checkbox(f"🛡️ Well Covers (${data['well_covers_price']:.0f})"):
                    running_total += float(data['well_covers_price']); applied_items.append("Well Covers")

            if data['mirrors_price'] > 0:
                if st.checkbox(f"🪞 Mirror Cleaning (${data['mirrors_price']:.0f})"):
                    running_total += float(data['mirrors_price']); applied_items.append("Mirrors")

            if data['perm_lighting_info'] and data['perm_lighting_info'].strip() != "":
                if st.checkbox("💡 Permanent Holiday Lighting?"):
                    st.info(data['perm_lighting_info']); applied_items.append("Lighting Interest")

        st.divider()
        st.metric("Total", f"${running_total:,.2f}")

        if st.button("Submit"):
            conn.table("upsell_sessions").update({
                "selected_items": applied_items, "final_total": running_total, "is_submitted": True
            }).eq("id", upsell_id).execute()
            st.session_state.finished = True
            st.rerun()

# --- ADMIN FLOW ---
else:
    st.title("Glide Admin")
    
    with st.form("creator"):
        c_name = st.text_input("Customer Name")
        c_base = st.number_input("Base Price", min_value=0.0)
        
        st.write("### Include these Add-ons?")
        # Interior
        col_a, col_b = st.columns([1, 4])
        inc_int = col_a.checkbox("Int", value=True)
        auto_int = (c_base * 0.6) // 5 * 5
        val_int = col_b.number_input("Interior Price", value=float(auto_int)) if inc_int else 0
        
        # Screens
        col_a, col_b = st.columns([1, 4])
        inc_scr = col_a.checkbox("Scr", value=True)
        val_scr = col_b.number_input("Screen Price", value=25.0) if inc_scr else 0

        # Gutters
        col_a, col_b = st.columns([1, 4])
        inc_gut = col_a.checkbox("Gut", value=False)
        val_gut = col_b.number_input("Gutter Price", value=50.0) if inc_gut else 0

        # Fans
        col_a, col_b = st.columns([1, 4])
        inc_fan = col_a.checkbox("Fan", value=True)
        val_fan = col_b.number_input("Fan Price (ea)", value=10.0) if inc_fan else 0
        
        # Wells
        col_a, col_b = st.columns([1, 4])
        inc_well = col_a.checkbox("Well", value=False)
        val_well = col_b.number_input("Well Cover Price", value=25.0) if inc_well else 0

        # Mirrors
        col_a, col_b = st.columns([1, 4])
        inc_mir = col_a.checkbox("Mir", value=False)
        val_mir = col_b.number_input("Mirror Price", value=25.0) if inc_mir else 0

        inc_light = st.checkbox("Include Lighting Info?", value=True)
        light_txt = st.text_area("Lighting Pitch", "Interested in permanent year-round lighting? Check for info!") if inc_light else ""
        
        create_btn = st.form_submit_button("Generate QR Code")

    if create_btn:
        new = conn.table("upsell_sessions").insert({
            "customer_name": c_name, "base_price": c_base,
            "interior_price": float(val_int), "screens_price": float(val_scr),
            "gutters_price": float(val_gut), "fan_price": float(val_fan),
            "well_covers_price": float(val_well), "mirrors_price": float(val_mir),
            "perm_lighting_info": light_txt
        }).execute()
        
        full_url = f"https://dgyzpaimv4zy73xfhfjrgv.streamlit.app/?id={new.data[0]['id']}"
        qr_img = qrcode.make(full_url)
        buf = BytesIO(); qr_img.save(buf)
        st.image(buf); st.code(full_url)

    st.divider()
    if st.button("🔄 Refresh Submissions"):
        st.rerun()

    st.subheader("Submissions")
    recent = conn.table("upsell_sessions").select("*").eq("is_submitted", True).order("created_at", desc=True).limit(10).execute()
    for r in recent.data:
        with st.expander(f"✅ {r['customer_name']} - ${r['final_total']}"):
            st.write(f"**Items:** {', '.join(r['selected_items']) if r['selected_items'] else 'None'}")
