import streamlit as st
import requests
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
        # 1. Geocoding (City to Lat/Lon)
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        geo_res = requests.get(geo_url).json()
        if not geo_res.get('results'): return "Weather: N/A"
        
        lat = geo_res['results'][0]['latitude']
        lon = geo_res['results'][0]['longitude']
        
        # 2. Get Weather
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&temperature_unit=fahrenheit"
        w_res = requests.get(weather_url).json()
        temp = w_res['current_weather']['temperature']
        return f"{temp}°F and Clear/Fair" # Simplified for readability
    except:
        return "Weather: Data unavailable"

def create_pdf(name, phone, notes, before_imgs, after_imgs, city):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=70)
    story = []
    styles = getSampleStyleSheet()

    # Get current time and weather
    submit_time = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    current_weather = get_weather(city)

    # --- Styles ---
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=22, textColor=NAVY, spaceAfter=5)
    meta_style = ParagraphStyle('Meta', parent=styles['Normal'], fontSize=9, textColor=SLATE, spaceAfter=20)
    section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=10, textColor=NAVY, 
                                   backColor=LIGHT_BG, borderColor=SLATE, borderWidth=0.5, borderPadding=8, 
                                   spaceBefore=20, spaceAfter=12, fontName='Helvetica-Bold', textTransform='uppercase')
    info_style = ParagraphStyle('Info', parent=styles['Normal'], fontSize=10, leading=14, textColor=NAVY)

    # 1. Header & Timestamp
    story.append(Paragraph("SERVICE REPORT", title_style))
    story.append(Paragraph(f"Submitted: {submit_time} | {current_weather}", meta_style))
    
    review_url = "https://www.google.com/search?q=Glide+Window+Cleaning+Reviews"
    service_text = f"<b>Customer:</b> {name.upper()} &nbsp;&nbsp; | &nbsp;&nbsp; <b>Phone:</b> {phone}<br/>"
    story.append(Paragraph(service_text, info_style))

    # 2. JOB NOTES
    if notes:
        story.append(Paragraph("JOB NOTES", section_style))
        notes_table = Table([[Paragraph(notes.replace('\n', '<br/>'), info_style)]], colWidths=[6.8 * inch])
        notes_table.setStyle(TableStyle([('BOX', (0,0), (-1,-1), 0.5, SLATE), ('LEFTPADDING', (0,0), (-1,-1), 12), ('TOPPADDING', (0,0), (-1,-1), 10), ('BOTTOMPADDING', (0,0), (-1,-1), 10)]))
        story.append(notes_table)

    # 3. Image Sections
    def add_imgs(label, files):
        if not files: return
        story.append(Paragraph(label, section_style))
        grid, row = [], []
        for f in files:
            img = ImageOps.exif_transpose(PILImage.open(f))
            img_tmp = BytesIO(); img.save(img_tmp, format="PNG"); img_tmp.seek(0)
            row.append(Image(img_tmp, width=3.2*inch, height=3.2*inch*(img.height/img.width)))
            if len(row) == 2: grid.append(row); row = []
        if row: row.append(""); grid.append(row)
        t = Table(grid, colWidths=[3.4*inch, 3.4*inch])
        t.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('BOTTOMPADDING', (0,0), (-1,-1), 15)]))
        story.append(t)

    add_imgs("BEFORE PHOTOS", before_imgs)
    add_imgs("AFTER PHOTOS", after_imgs)

    # 4. Footer
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph(f"Please mention <b>Aaron</b> in your <a href='{review_url}' color='#448AFF'>Google Review!</a>", info_style))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("GLIDE WINDOW CLEANING • SATISFACTION GUARANTEED", 
                           ParagraphStyle('Foot', parent=styles['Normal'], fontSize=9, textColor=SLATE, alignment=1)))

    doc.build(story)
    return buffer.getvalue()

# --- Streamlit UI ---
st.set_page_config(page_title="Glide Report", page_icon="📄")
st.markdown("<style>.stButton>button { background-color: #2C3E50; color: white; width: 100%; }</style>", unsafe_allow_html=True)

st.title("📄 Professional Report Generator")

colA, colB = st.columns(2)
with colA: name = st.text_input("Customer Name")
with colB: city = st.text_input("Service City (for weather)", value="Rexburg") # Default to your area

phone = st.text_input("Customer Phone")
job_notes = st.text_area("Job Notes")

c1, c2 = st.columns(2)
with c1: before = st.file_uploader("Before Photos", accept_multiple_files=True)
with c2: after = st.file_uploader("After Photos", accept_multiple_files=True)

if st.button("GENERATE REPORT"):
    if name and city:
        pdf_data = create_pdf(name, phone, job_notes, before, after, city)
        st.download_button("📥 Download PDF", pdf_data, f"Report_{name}.pdf", "application/pdf")
       
