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
load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(page_title="Glide Upsell", layout="centered")

# -----------------------------
# CSS (Improved styling + sticky total)
# -----------------------------
st.markdown("""
<style>
.main {
    background-color: #f6f0ed;
}

h1, h2, h3 {
    color: #28536b;
}

/* Sticky total bar */
.sticky-total {
    position: sticky;
    top: 0;
    z-index: 999;
    background: white;
    padding: 14px;
    border-radius: 0 0 12px 12px;
    border-bottom: 2px solid #eee;
    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
}

/* Buttons */
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

/* Checkbox cards */
.stCheckbox {
    padding: 12px;
    background: white;
    border-radius: 12px;
    margin-bottom: 10px;
    border: 1px solid #ddd;
}

/* Total text */
.total-value {
    font-size: 2rem;
    font-weight: bold;
    color: #688b58;
}

/* Metric color */
div[data-testid="stMetricValue"] {
    color: #688b58;
}

/* Remove number arrows */
input[type=number]::-webkit-inner-spin-button,
input[type=number]::-webkit-outer-spin-button {
    -webkit-appearance: none;
    margin: 0;
}
input[type=number] {
    -moz-appearance: textfield;
}

.block-container {
    padding-top: 2rem;
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

# add create pdf function that takes in summary and creates a pdf with the summary as content and a header image of the freshpane logo
from fpdf import FPDF
def create_pdf(summary):
    # 1. Initialize the PDF object
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # 2. Setup the path (The fix from before)
    script_path = Path(__file__).resolve().parent
    logo_path = script_path / "logofreshpoane.png"
    
    # 3. Add the logo (check if exists first to avoid crashes)
    if logo_path.exists():
        pdf.image(str(logo_path), x=10, y=8, w=33)
    else:
        # Optional: Add a placeholder or warning if logo is missing
        pdf.cell(200, 10, txt="[Logo Missing]", ln=1, align='C')

    # 4. Add the summary text
    # Moving the cursor down so it doesn't overlap the logo
    pdf.ln(35) 
    pdf.multi_cell(0, 10, summary)

    # 5. Output to buffer
    # Use 'S' to return the document as a byte string
    pdf_output = pdf.output(dest='S')
    
    # Depending on your FPDF version, .output(dest='S') 
    # might return bytes or a string. 
    # Streamlit's download_button likes bytes.
    return pdf_output.encode('latin-1') if isinstance(pdf_output, str) else pdf_output
# =============================
# CUSTOMER FLOW
# =============================
if upsell_id:

    res = conn.table("upsell_sessions").select("*").eq("id", upsell_id).execute()

    if not res.data:
        st.error("Invalid Link.")
        st.stop()

    data = res.data[0]

    if data.get("is_submitted"):
        st.success("Your bid has been submitted!")
        st.subheader("Your Bid Summary")
        st.write(f"Total Price: ${data['final_total']:,.2f}")
        if data['selected_items']:
            st.write("Selected Services:")
            for item in data['selected_items']:
                st.write(f"- {item}")
        else:
            st.write("No additional services selected.")
            # get data for [original price only] case and display that in a more user friendly way

        summary = f"Customer: {data['customer_name']}\nExterior: ${data['base_price']:,.2f}\nAdd on Services:\n - {'\n -'.join(data['selected_items']) if data['selected_items'] else 'None'}\n\nTOTAL: ${data['final_total']:,.2f}"
        # download as pdf with image
        pdf = create_pdf(summary)

        st.download_button(
            label="Download Summary PDF",
            data=pdf,
            file_name=f"{data['customer_name']}_bid_summary.pdf",
            mime="application/pdf"
        )
        st.link_button(
            label="Schedule Later Time", 
            url="https://freshpanecustomerbooking.streamlit.app/",
            use_container_width=True  # Optional: makes the button stretch to match the UI
        )
        st.stop()

    st.title(f"Hello, {data['customer_name']} (see total price below)")

    base_price = float(data["base_price"])
    running_total = base_price
    applied_items = []

    none_op = st.checkbox("Exterior Only: ${:.2f}".format(base_price), key="none_box")

    if not none_op:
        st.divider()

        services = [
            ("Interior Windows", "", "interior_price", False, False),
            ("Deep Screen Clean", "", "screens_price", False, False),
            # ("Ceiling Fan Dusting", "", "fan_price", True, False),
            ("Gutter Cleaning", "", "gutters_price", False, False),
            # ("Window Well Cover Cleaning", "", "well_covers_price", False, False),
            ("Mirror Cleaning", "", "mirrors_price", False, False),
        ]

        for label, icon, field, per_unit, always_show in services:

            raw_price = data.get(field, 0)
        
            if always_show:
                price = get_service_price(raw_price, base_price)
            else:
                if raw_price <= 0:
                    continue
                price = get_service_price(raw_price, base_price)
        
            selected, total, desc = render_service(label, price, icon, field, per_unit)
        
            if selected:
                running_total += total
                applied_items.append(f"{desc} - ${total:.0f}")

        # if data.get("perm_lighting_info") and data["perm_lighting_info"].strip():
        #     if st.checkbox("💡 Interested in permanent year-round lighting? (check for more info)"):
        #         st.info(data["perm_lighting_info"])
        #         applied_items.append("Lighting Interest - $0")
       
    # Sticky total
    st.markdown(f"""
    <div class="sticky-total">
        <div style="display:flex; justify-content:space-between;">
            <div><strong>Total</strong></div>
            <div class="total-value">${running_total:,.2f}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()


    if st.button("Confirm & Submit"):

        submission_time = datetime.now().strftime("%A, %B %d at %I:%M %p")

        conn.table("upsell_sessions").update({
            "selected_items": applied_items,
            "final_total": running_total,
            "is_submitted": True,
            # "submission_time": submission_time
        }).eq("id", upsell_id).execute()

        st.rerun()

# =============================
# ADMIN FLOW
# =============================
else:
    
    # have button withhyperlink for this website google.com
    st.markdown("""
    <a href="https://freshpanebookings.streamlit.app/" target="_blank">
        <button style="width:100%; padding: 12px; background-color:#28536b; color:white; font-weight:600; border:none; border-radius:12px; margin-bottom:20px;">
            View Booking Calendar
        </button>
    </a>
    """, unsafe_allow_html=True)
    st.markdown("""
    <a href="https://notebooklm.google.com/notebook/10f219ed-c70e-4857-a070-dc1c12007f3a" target="_blank">
        <button style="width:100%; padding: 12px; background-color:#28536b; color:white; font-weight:600; border:none; border-radius:12px; margin-bottom:20px;">
           Schedule Time off
        </button>
    </a>
    """, unsafe_allow_html=True)

    st.title("FreshPane Bidding")
    with st.form("creator"):

        c_name = st.text_input("Customer Name")

        c_base = st.number_input(
            "Base Price",
            min_value=150.0,
            value=150.0,
            step=5.0,
            key="base_price"
        )

        st.subheader("Services")

        auto_int = fallback_price(c_base)

        # --- SAFE SESSION STATE ---
        if "v_int" not in st.session_state:
            st.session_state.v_int = float(auto_int)

        if "refresh_int" not in st.session_state:
            st.session_state.refresh_int = False

        if st.session_state.refresh_int:
            st.session_state.v_int = fallback_price(st.session_state.base_price)
            st.session_state.refresh_int = False

        # Interior row
        col1, col2, col3 = st.columns([1, 2, 1])

        active_int = col1.checkbox("Interior", value=True, key="a_int")

        val_int = col2.number_input(
            "Interior Price",
            step=5.0,
            label_visibility="collapsed",
            key="v_int"
        )

        if col3.form_submit_button("🔄"):
            st.session_state.refresh_int = True
            st.rerun()

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

        val_scr = admin_row("Screens", 25.0, "scr")
        val_gut = admin_row("Gutters", 175.0, "gut")
        # val_fan = admin_row("Fans", 10.0, "fan") 
        # val_well = admin_row("Wells", 25.0, "well")
        val_mir = admin_row("Mirrors", 25.0, "mir")

        st.divider()

        # inc_light = st.checkbox("Permanent lighting info")
        # light_txt = st.text_area(
        #     "Lighting Pitch Text",
        #     "We’ll go over lighting options with you at the door!"
        # ) if inc_light else ""

        submitted = st.form_submit_button("Generate QR Code")

        if submitted:
            if not c_name:
                st.error("Please enter a name!")
            else:
                new = conn.table("upsell_sessions").insert({
                    "customer_name": c_name,
                    "base_price": c_base,
                    "interior_price": float(val_int if active_int else 0),
                    "screens_price": float(val_scr),
                    "gutters_price": float(val_gut),
                    # "fan_price": float(val_fan),
                    # "well_covers_price": float(val_well),
                    "mirrors_price": float(val_mir),
                    # add datetime of submission
                    # "created_at": datetime.now().isoformat(),
                    # "perm_lighting_info": light_txt
                }).execute()

                base_url = "https://freshbids.streamlit.app/"
                full_url = f"{base_url}?id={new.data[0]['id']}"

                st.success(f"Upsell Created for {c_name}!")

                qr_img = qrcode.make(full_url)
                buf = BytesIO()
                qr_img.save(buf)

                st.image(buf, caption="Customer scans this code")
                st.code(full_url)

    st.divider()

    # 🔥 Refresh submissions button (RESTORED)
    if st.button("🔄 Refresh Submissions"):
        st.rerun()

    st.subheader("Recent Submissions")

    recent = conn.table("upsell_sessions") \
        .select("*") \
        .eq("is_submitted", True) \
        .order("created_at", desc=True) \
        .limit(10) \
        .execute()
# formate created_at to be more readable


    if recent.data:
        for r in recent.data:
            raw_date = r.get('created_at')

# Convert string to datetime object, then to Mountain Time
            dt_utc = pd.to_datetime(raw_date)
            dt_local = dt_utc.tz_convert('America/Denver')

            formatted_date = dt_local.strftime("%b %d, %Y %I:%M %p")
           

            with st.expander(f"✅ {r['customer_name']} - ${r['final_total']} | {formatted_date}"):
                st.write(f"Selected: {', '.join(r['selected_items']) if r['selected_items'] else 'None'}")
                st.write(f"Base Price: ${r['base_price']}")
    else:
        st.info("No customer submissions found yet.")
