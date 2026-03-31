import streamlit as st
from st_supabase_connection import SupabaseConnection
import qrcode
from io import BytesIO
import math

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(page_title="Glide Upsell", layout="centered")

# -----------------------------
# THEME / CSS
# -----------------------------
st.markdown("""
<style>
.main {
    background-color: #f6f0ed;
}

h1, h2, h3 {
    color: #28536b;
}

.stButton button {
    width: 100%;
    border-radius: 12px;
    height: 3.2em;
    background-color: #28536b;
    color: white;
    font-weight: 600;
    border: none;
}

.stButton button:hover {
    background-color: #1f3e50;
}

.stCheckbox {
    padding: 12px;
    background: white;
    border-radius: 12px;
    margin-bottom: 10px;
    border: 1px solid #ddd;
}

div[data-testid="stMetricValue"] {
    color: #688b58;
    font-size: 2.4rem;
}

.block-container {
    padding-top: 2rem;
}

.card {
    background: white;
    padding: 16px;
    border-radius: 14px;
    margin-bottom: 10px;
    border: 1px solid #eee;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Supabase
# -----------------------------
conn = st.connection("supabase", type=SupabaseConnection)

# -----------------------------
# Helpers
# -----------------------------
def fallback_price(base_price: float) -> float:
    val = base_price * 0.6
    return math.floor(val / 5) * 5

def get_service_price(admin_price: float, base_price: float) -> float:
    if admin_price and admin_price > 0:
        return float(admin_price)
    return float(fallback_price(base_price))

def render_service(label, price, icon, key, per_unit=False):
    """Reusable UI block for services"""
    selected = st.checkbox(f"{icon} {label} (${price:.0f})", key=f"chk_{key}")

    total = 0
    desc = None

    if selected:
        if per_unit:
            count = st.number_input(
                f"{label} count",
                min_value=1,
                value=1,
                step=1,
                key=f"cnt_{key}"
            )
            total = price * count
            desc = f"{label} ({count})"
        else:
            total = price
            desc = label

    return selected, total, desc

# -----------------------------
# Routing
# -----------------------------
query_params = st.query_params
upsell_id = query_params.get("id")

# =============================
# CUSTOMER FLOW
# =============================
if upsell_id:

    if st.session_state.get("finished"):
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

    st.title(f"Hello, {data['customer_name']} 👋")

    base_price = float(data["base_price"])
    running_total = base_price
    applied_items = []

    none_op = st.checkbox("❌ No Add-ons (Keep original price)")

    if not none_op:
        st.divider()

        # --- SERVICES ---

        services = [
            ("Interior Windows", "🏠", "interior_price", False, True),  # ALWAYS SHOW
            ("Screen Deep Clean", "🖼️", "screens_price", False, False),
            ("Ceiling Fans", "🌀", "fan_price", True, False),
            ("Gutter Cleaning", "🍂", "gutters_price", False, False),
            ("Well Covers", "🛡️", "well_covers_price", False, False),
            ("Mirror Cleaning", "🪞", "mirrors_price", False, False),
        ]

        for label, icon, field, per_unit, always_show in services:

            raw_price = data.get(field, 0)

            # 🔥 FIX: interior ALWAYS gets fallback if zero
            if always_show:
                price = get_service_price(raw_price, base_price)
            else:
                if raw_price <= 0:
                    continue
                price = get_service_price(raw_price, base_price)

            selected, total, desc = render_service(
                label, price, icon, field, per_unit
            )

            if selected:
                running_total += total
                applied_items.append(desc)

        # Lighting
        if data.get("perm_lighting_info"):
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

# =============================
# ADMIN FLOW
# =============================
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

        st.subheader("Services")

        auto_int = fallback_price(c_base)

        def admin_row(label, default, key):
            col1, col2 = st.columns([1, 2])
            active = col1.checkbox(label, value=True, key=f"a_{key}")
            val = col2.number_input(
                label,
                value=float(default),
                step=5.0,
                label_visibility="collapsed",
                key=f"v_{key}"
            )
            return val if active else 0.0

        val_int = admin_row("Interior", auto_int, "int")
        val_scr = admin_row("Screens", 25.0, "scr")
        val_gut = admin_row("Gutters", 50.0, "gut")
        val_fan = admin_row("Fans", 10.0, "fan")
        val_well = admin_row("Wells", 25.0, "well")
        val_mir = admin_row("Mirrors", 25.0, "mir")

        st.divider()

        inc_light = st.checkbox("Include Lighting Pitch?")
        light_txt = st.text_area(
            "Lighting Text",
            "Ask us about permanent lighting!"
        ) if inc_light else ""

        submitted = st.form_submit_button("Generate QR Code")

        if submitted:
            if not c_name:
                st.error("Enter a name")
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

                url = f"https://dgyzpaimv4zy73xfhfjrgv.streamlit.app/?id={new.data[0]['id']}"

                st.success(f"Created for {c_name}")

                img = qrcode.make(url)
                buf = BytesIO()
                img.save(buf)

                st.image(buf)
                st.code(url)

    st.divider()

    st.subheader("Recent Submissions")

    recent = conn.table("upsell_sessions") \
        .select("*") \
        .eq("is_submitted", True) \
        .order("created_at", desc=True) \
        .limit(10) \
        .execute()

    if recent.data:
        for r in recent.data:
            with st.expander(f"{r['customer_name']} - ${r['final_total']}"):
                st.write("Items:", ", ".join(r['selected_items']) or "None")
                st.write("Base:", f"${r['base_price']}")
    else:
        st.info("No submissions yet.")
