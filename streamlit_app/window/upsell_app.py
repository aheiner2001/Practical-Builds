import streamlit as st
from st_supabase_connection import SupabaseConnection
import qrcode
from io import BytesIO
import math

# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(page_title="Glide Upsell", layout="centered")

# -----------------------------
# Custom CSS
# -----------------------------
st.markdown("""
<style>
.stButton button {
    width: 100%;
    border-radius: 12px;
    height: 3.5em;
    background-color: #007bff;
    color: white;
    font-weight: bold;
}
.main {
    background-color: #f9f9f9;
}
div[data-testid="stMetricValue"] {
    color: #2e7d32;
    font-size: 2.2rem;
}
.stCheckbox {
    padding: 12px;
    background: white;
    border-radius: 10px;
    margin-bottom: 8px;
    border: 1px solid #ddd;
}
input[type=number]::-webkit-inner-spin-button,
input[type=number]::-webkit-outer-spin-button {
    -webkit-appearance: none;
    margin: 0;
}
input[type=number] {
    -moz-appearance: textfield;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Supabase Connection
# -----------------------------
conn = st.connection("supabase", type=SupabaseConnection)

# -----------------------------
# Helpers
# -----------------------------
def fallback_price(base_price: float) -> float:
    """Compute fallback = 60% of base rounded down to nearest 5."""
    val = base_price * 0.6
    return math.floor(val / 5) * 5

def get_service_price(admin_price: float, base_price: float) -> float:
    """
    Use admin price if > 0, otherwise fallback to derived price.
    """
    if admin_price and admin_price > 0:
        return float(admin_price)
    return float(fallback_price(base_price))

def admin_service_row(label, default_val, key_prefix):
    col_check, col_price = st.columns([1, 2])
    is_active = col_check.checkbox(label, value=True, key=f"active_{key_prefix}")

    price_input = col_price.number_input(
        f"{label} Price",
        value=float(default_val),
        step=5.0,
        key=f"val_{key_prefix}",
        label_visibility="collapsed"
    )

    return price_input if is_active else 0.0

# -----------------------------
# Routing
# -----------------------------
query_params = st.query_params
upsell_id = query_params.get("id")

# -----------------------------
# CUSTOMER FLOW
# -----------------------------
if upsell_id:

    if st.session_state.get("finished", False):
        st.success("Thanks! You may now close this browser.")
        st.balloons()
        st.stop()

    res = conn.table("upsell_sessions").select("*").eq("id", upsell_id).execute()

    if not res.data:
        st.error("Invalid Link.")
        st.stop()

    data = res.data[0]

    if data.get("is_submitted"):
        st.info("Request already processed. Thank you!")
        st.stop()

    st.title(f"Hello, {data['customer_name']}!")

    none_op = st.checkbox("❌ None (Keep original price)", key="none_box")

    running_total = float(data["base_price"])
    applied_items = []

    # Precompute fallback base
    base_price = float(data["base_price"])

    if not none_op:
        st.divider()

        # Interior
        interior_price = get_service_price(data.get("interior_price", 0), base_price)
        if interior_price > 0:
            if st.checkbox(f"🏠 Interior Windows (${interior_price:.0f})"):
                running_total += interior_price
                applied_items.append("Interior")

        # Screens
        screens_price = get_service_price(data.get("screens_price", 0), base_price)
        if screens_price > 0:
            if st.checkbox(f"🖼️ Screen Deep Clean (${screens_price:.0f})"):
                running_total += screens_price
                applied_items.append("Screens")

        # Fans
        fan_price = get_service_price(data.get("fan_price", 0), base_price)
        if fan_price > 0:
            if st.checkbox(f"🌀 Ceiling Fans (${fan_price:.0f} ea)"):
                fan_count = st.number_input(
                    "How many?",
                    min_value=1,
                    value=1,
                    step=1,
                    label_visibility="collapsed"
                )
                running_total += fan_price * fan_count
                applied_items.append(f"Fans ({fan_count})")

        # Gutters
        gutters_price = get_service_price(data.get("gutters_price", 0), base_price)
        if gutters_price > 0:
            if st.checkbox(f"🍂 Gutter Cleaning (${gutters_price:.0f})"):
                running_total += gutters_price
                applied_items.append("Gutters")

        # Well Covers
        well_price = get_service_price(data.get("well_covers_price", 0), base_price)
        if well_price > 0:
            if st.checkbox(f"🛡️ Well Covers (${well_price:.0f})"):
                running_total += well_price
                applied_items.append("Well Covers")

        # Mirrors
        mirror_price = get_service_price(data.get("mirrors_price", 0), base_price)
        if mirror_price > 0:
            if st.checkbox(f"🪞 Mirror Cleaning (${mirror_price:.0f})"):
                running_total += mirror_price
                applied_items.append("Mirrors")

        # Lighting
        if data.get("perm_lighting_info") and data["perm_lighting_info"].strip():
            if st.checkbox("💡 Permanent Holiday Lighting?"):
                st.info(data["perm_lighting_info"])
                applied_items.append("Lighting Interest")

    st.divider()
    st.metric("Total Appointment Price", f"${running_total:,.2f}")

    if st.button("Confirm & Submit"):
        conn.table("upsell_sessions").update({
            "selected_items": applied_items,
            "final_total": running_total,
            "is_submitted": True
        }).eq("id", upsell_id).execute()

        st.session_state.finished = True
        st.rerun()

# -----------------------------
# ADMIN FLOW
# -----------------------------
else:
    st.title("Glide Admin")

    with st.form("creator"):
        c_name = st.text_input("Customer Name")

        c_base = st.number_input(
            "Base Price",
            min_value=0.0,
            value=0.0,
            step=5.0
        )

        st.write("### Services to Include")

        # Interior auto suggestion (60% of base)
        auto_int = fallback_price(c_base)

        val_int = admin_service_row("Interior", auto_int, "int")
        val_scr = admin_service_row("Screens", 25.0, "scr")
        val_gut = admin_service_row("Gutters", 50.0, "gut")
        val_fan = admin_service_row("Fans", 10.0, "fan")
        val_well = admin_service_row("Wells", 25.0, "well")
        val_mir = admin_service_row("Mirrors", 25.0, "mir")

        st.divider()

        inc_light = st.checkbox("Show Permanent Lighting Info?", value=False)
        light_txt = st.text_area(
            "Lighting Pitch Text",
            "Interested in permanent year-round lighting? Check for info!"
        ) if inc_light else ""

        create_btn = st.form_submit_button("Generate QR Code")

        if create_btn:
            if not c_name:
                st.error("Please enter a name!")
            else:
                new = conn.table("upsell_sessions").insert({
                    "customer_name": c_name,
                    "base_price": c_base,
                    "interior_price": float(val_int),
                    "screens_price": float(val_scr),
                    "gutters_price": float(val_gut),
                    "fan_price": float(val_fan),
                    "well_covers_price": float(val_well),
                    "mirrors_price": float(val_mir),
                    "perm_lighting_info": light_txt
                }).execute()

                base_url = "https://dgyzpaimv4zy73xfhfjrgv.streamlit.app/"
                full_url = f"{base_url}?id={new.data[0]['id']}"

                st.success(f"Upsell Created for {c_name}!")

                qr_img = qrcode.make(full_url)
                buf = BytesIO()
                qr_img.save(buf)

                st.image(buf, caption="Customer scans this code")
                st.code(full_url)

    st.divider()

    if st.button("🔄 Check for New Submissions"):
        st.rerun()

    st.subheader("Recent Submissions")

    recent = conn.table("upsell_sessions") \
        .select("*") \
        .eq("is_submitted", True) \
        .order("created_at", desc=True) \
        .limit(10) \
        .execute()

    if recent.data:
        for r in recent.data:
            with st.expander(f"✅ {r['customer_name']} - ${r['final_total']}"):
                st.write(f"Selected: {', '.join(r['selected_items']) if r['selected_items'] else 'None'}")
                st.write(f"Base Price: ${r['base_price']}")
    else:
        st.info("No customer submissions found yet.")
