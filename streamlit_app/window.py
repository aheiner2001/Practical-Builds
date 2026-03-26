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
NAVY = colors.HexColor("#1F3A5F")
SLATE = colors.HexColor("#6B7A8F")
LIGHT_BG = colors.HexColor("#F4F7FB")
ACCENT = colors.HexColor("#448AFF")

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

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=70
    )

    story = []
    styles = getSampleStyleSheet()

    # --- TIMEZONE ---
    local_tz = pytz.timezone('US/Mountain')
    now_local = datetime.now(local_tz)
    submit_time = now_local.strftime("%B %d, %Y at %I:%M %p")

    current_weather = get_weather(city)

    # --- STYLES ---

    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=NAVY,
        alignment=1,  # center
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )

    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=SLATE,
        alignment=1,
        spaceAfter=15
    )

    section_style = ParagraphStyle(
        'Section',
        parent=styles['Normal'],
        fontSize=10,
        textColor=NAVY,
        backColor=LIGHT_BG,
        borderPadding=6,
        spaceBefore=18,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    )

    info_style = ParagraphStyle(
        'Info',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        leading=14
    )

    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=SLATE,
        alignment=1
    )

    # --- HEADER ---
    story.append(Paragraph("GLIDE WINDOW CLEANING", title_style))
    story.append(Paragraph("SERVICE REPORT", ParagraphStyle(
        'HeaderSub',
        parent=styles['Normal'],
        fontSize=11,
        textColor=ACCENT,
        alignment=1,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    )))

    story.append(Paragraph(
        f"{submit_time} • {city} • {current_weather}",
        subtitle_style
    ))

    # Customer info box
    # customer_table = Table([
    story.append(Paragraph(f"For {name}", ParagraphStyle(
        'HeaderSub',
        parent=styles['Normal'],
        fontSize=11,
        textColor=NAVY,
        alignment=0,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    ))
         # Paragraph(f"<b>Phone:</b> {phone}", info_style)]
    # ], colWidths=[3.4*inch, 3.4*inch])

    # customer_table.setStyle(TableStyle([
    #     ('BACKGROUND', (0,0), (-1,-1), LIGHT_BG),
    #     ('BOX', (0,0), (-1,-1), 0.5, SLATE),
    #     ('INNERGRID', (0,0), (-1,-1), 0.25, SLATE),
    #     ('LEFTPADDING', (0,0), (-1,-1), 10),
    #     ('RIGHTPADDING', (0,0), (-1,-1), 10),
    #     ('TOPPADDING', (0,0), (-1,-1), 8),
    #     ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    # ]))
                )
    # story.append(customer_table)

    # --- NOTES ---
    if notes:
        story.append(Paragraph("JOB NOTES", ParagraphStyle(
        'HeaderSub',
        parent=styles['Normal'],
        fontSize=11,
        textColor=ACCENT,
        alignment=0,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    )))

        notes_table = Table([
            [Paragraph(notes.replace('\n', '<br/>'), info_style)]
        ], colWidths=[6.8*inch])

        notes_table.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.5, SLATE),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ]))

        story.append(notes_table)

    # --- IMAGE FUNCTION ---
    def add_imgs(label, files):
        if not files:
            return

        story.append(Paragraph(label, ParagraphStyle(
        'HeaderSub',
        parent=styles['Normal'],
        fontSize=11,
        textColor=ACCENT,
        alignment=0,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    )))

        grid = []
        row = []

        for f in files:
            img = ImageOps.exif_transpose(PILImage.open(f))
            tmp = BytesIO()
            img.save(tmp, format="PNG")
            tmp.seek(0)

            aspect = img.height / img.width
            row.append(Image(tmp, width=3.2*inch, height=3.2*inch * aspect))

            if len(row) == 2:
                grid.append(row)
                row = []

        if row:
            row.append("")
            grid.append(row)

        table = Table(grid, colWidths=[3.4*inch, 3.4*inch])

        table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ]))

        story.append(table)

    # --- IMAGES ---
       # --- REVIEW SECTION ---
    review_url = "https://share.google/KKCvRlDReYr8iJceZ"

    story.append(Spacer(1, 0.4*inch))

    story.append(Paragraph(
        f"""
        It would mean a lot if you left a review!<br/>
        If you mention <b>Aaron</b>, it would help even more! <br/><br/>
        <font color="#448AFF">
        <a href="{review_url}"><b>Leave a review here</b></a>
        </font>
        """,
        info_style
    ))
    add_imgs("BEFORE – FEATURED PHOTOS", before_imgs)
    add_imgs("AFTER – FEATURED PHOTOS", after_imgs)

 

    # --- FOOTER ---
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("REXBURG, ID • GLIDE WINDOW CLEANING", footer_style))

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
