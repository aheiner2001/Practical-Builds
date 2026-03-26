import streamlit as st
import requests
import pytz
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.units import inch
from io import BytesIO
from PIL import Image as PILImage, ImageOps
import base64

# --- Theme Setup ---
NAVY = colors.Color(0.05, 0.08, 0.12)
SLATE = colors.Color(0.44, 0.50, 0.56)
LIGHT_BG = colors.Color(0.98, 0.98, 0.98)
WHITE = colors.white

def get_weather(city):
    """Fetches simple weather via Open-Meteo (No API Key needed)"""
    try:
        # Defaulting to Rexburg coordinates as requested
        lat = 40.0966
        lon = -111.5707
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&temperature_unit=fahrenheit"
        w_res = requests.get(weather_url).json()
        temp = w_res['current_weather']['temperature']
        return f"{int(temp)}°F and Clear/Fair"
    except:
        return "Weather: Data unavailable"

def create_pdf(name, phone, notes, before_imgs, after_imgs, city):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=70)
    story, styles = [], getSampleStyleSheet()

    # --- TIMEZONE FIX ---
    local_tz = pytz.timezone('US/Mountain')
    now_local = datetime.now(local_tz)
    submit_time = now_local.strftime("%B %d, %Y at %I:%M %p")
    
    current_weather = get_weather(city)

    # --- Styles ---
    title_s = ParagraphStyle('T', parent=styles['Heading1'], fontSize=22, textColor=NAVY, spaceAfter=5)
    meta_s = ParagraphStyle('M', parent=styles['Normal'], fontSize=9, textColor=SLATE, spaceAfter=20)
    sect_s = ParagraphStyle('S', parent=styles['Heading2'], fontSize=10, textColor=NAVY, backColor=LIGHT_BG, 
                            borderColor=SLATE, borderWidth=0.5, borderPadding=8, spaceBefore=20, 
                            spaceAfter=12, fontName='Helvetica-Bold', textTransform='uppercase')
    info_s = ParagraphStyle('I', parent=styles['Normal'], fontSize=10, leading=14, textColor=NAVY)

    # 1. Header
    story.append(Paragraph("SERVICE REPORT", title_s))
    story.append(Paragraph(f"Submitted: {submit_time} | {current_weather}", meta_s))
    
    review_url = "https://share.google/KKCvRlDReYr8iJceZ"
    story.append(Paragraph(f"<b>Customer:</b> {name.upper()} | <b>Phone:</b> {phone}", info_s))

    # 2. Notes
    if notes:
        story.append(Paragraph("JOB NOTES", sect_s))
        nt = Table([[Paragraph(notes.replace('\n', '<br/>'), info_s)]], colWidths=[6.8*inch])
        nt.setStyle(TableStyle([('BOX',(0,0),(-1,-1),0.5,SLATE),('LEFTPADDING',(0,0),(-1,-1),12),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)]))
        story.append(nt)

    # 3. Images
    def add_imgs(label, files):
        if not files: return
        story.append(Paragraph(label, sect_s))
        grid, row = [], []
        for f in files:
            img = ImageOps.exif_transpose(PILImage.open(f))
            tmp = BytesIO(); img.save(tmp, format="PNG"); tmp.seek(0)
            row.append(Image(tmp, width=3.2*inch, height=3.2*inch*(img.height/img.width)))
            if len(row) == 2: grid.append(row); row = []
        if row: row.append(""); grid.append(row)
        t = Table(grid, colWidths=[3.4*inch, 3.4*inch])
        t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('BOTTOMPADDING',(0,0),(-1,-1),15)]))
        story.append(t)

    add_imgs("BEFORE PHOTOS", before_imgs)
    add_imgs("AFTER PHOTOS", after_imgs)

    # 4. Personal Note & Footer
    story.append(Spacer(1, 0.4*inch))
    story.append(Paragraph(f"It would help me a ton if you could leave a review for Glide Window Cleaning! If you could mention <b>Aaron</b>, it helps me out even more. <a href='{review_url}' color='#448AFF'><b><u>Please leave a review here!</u></b></a>", info_s))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("GLIDE WINDOW CLEANING • REXBURG, ID", ParagraphStyle('F', parent=styles['Normal'], fontSize=8, textColor=SLATE, alignment=1)))

    doc.build(story)
    return buffer.getvalue()

# --- Streamlit UI ---
st.set_page_config(page_title="Glide Report Generator", layout="centered")
st.markdown("<style>.stButton>button { background-color: #2C3E50; color: white; border-radius: 4px; font-weight: bold; } header {visibility: hidden;}</style>", unsafe_allow_html=True)

st.title("📄 Service Report Generator")

# User Inputs
name = st.text_input("Customer Name")
phone = st.text_input("Customer Phone")
notes = st.text_area("Job Notes & Observations")

# Hardcoded city since the input was removed
city = "Rexburg"

c1, c2 = st.columns(2)
with c1: 
    before = st.file_uploader("Before Photos", accept_multiple_files=True)
with c2: 
    after = st.file_uploader("After Photos", accept_multiple_files=True)

if st.button("GENERATE CLEAN PDF"):
    if name: # Only check for name now
        with st.spinner("Processing..."):
            pdf = create_pdf(name, phone, notes, before, after, city)
            st.success("Report Ready!")
            st.download_button("📥 Download PDF", pdf, f"Glide_Report_{name}.pdf", "application/pdf")
            
    else: 
        st.error("Please provide a Customer Name.")
