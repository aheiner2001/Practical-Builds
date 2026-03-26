import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.units import inch
from io import BytesIO
from PIL import Image as PILImage, ImageOps
import base64

# --- Glide Brand Colors ---
GLIDE_ORANGE = colors.Color(0.95, 0.53, 0.23) # RGB: 242, 135, 58
GLIDE_NAVY = colors.Color(0.05, 0.08, 0.12)   # Deep Navy/Black
GLIDE_SKY = colors.Color(0.88, 0.96, 0.98)    # Light Sky Blue Background
WHITE = colors.white

def create_pdf(name, phone, notes, before_imgs, after_imgs):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=70)
    story = []
    styles = getSampleStyleSheet()

    # --- Enhanced Styles ---
    title_style = ParagraphStyle(
        'TitleStyle', parent=styles['Heading1'], fontSize=30, textColor=GLIDE_NAVY, 
        spaceAfter=15, fontName='Helvetica-Bold'
    )
    
    # Modern Card-Style Header
    section_style = ParagraphStyle(
        'SectionStyle', parent=styles['Heading2'], fontSize=12, textColor=GLIDE_NAVY, 
        backColor=GLIDE_SKY, borderColor=GLIDE_ORANGE, borderWidth=1.5,
        borderPadding=10, spaceBefore=20, spaceAfter=12, fontName='Helvetica-Bold',
        borderRadius=6
    )

    info_style = ParagraphStyle(
        'InfoStyle', parent=styles['Normal'], fontSize=11, leading=16, textColor=GLIDE_NAVY
    )

    # 1. Header Section
    story.append(Paragraph("WINDOW WASHING REPORT", title_style))
    
    review_url = "https://share.google/qJDmPYd7266QpvRys"
    
    # Branded Service Text
    service_text = f"""
    <b>Serviced by:</b> Aaron Heiner<br/>
    <b>Customer:</b> {name.upper()} &nbsp;&nbsp; | &nbsp;&nbsp; <b>Phone:</b> {phone}<br/><br/>
    It would help me a ton if you could leave a review for Glide Window Cleaning! If you could mention my name (Aaron) in the review, it helps me out even more. Thank you for your support!<br/>
    <a href="{review_url}" color="#f2873a"><b><u>Please leave a review!</u></b></a>
    """
    
    story.append(Paragraph(service_text, info_style))
    story.append(Spacer(1, 0.1 * inch))

    # 2. JOB NOTES (Enhanced Card Box)
    if notes:
        story.append(Paragraph("JOB NOTES & OBSERVATIONS", section_style))
        notes_data = [[Paragraph(notes.replace('\n', '<br/>'), info_style)]]
        notes_table = Table(notes_data, colWidths=[6.8 * inch])
        notes_table.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 1, colors.lightgrey),
            ('LEFTPADDING', (0,0), (-1,-1), 15),
            ('TOPPADDING', (0,0), (-1,-1), 12),
            ('BOTTOMPADDING', (0,0), (-1,-1), 12),
            ('BACKGROUND', (0,0), (-1,-1), WHITE),
        ]))
        story.append(notes_table)

    # 3. Image Grid Logic
    def add_image_section(label, files):
        if not files: return
        story.append(Paragraph(label, section_style))
        grid_data, row = [], []
        
        for uploaded_file in files:
            img = ImageOps.exif_transpose(PILImage.open(uploaded_file))
            img_tmp = BytesIO()
            img.save(img_tmp, format="PNG")
            img_tmp.seek(0)
            
            width = 3.2 * inch
            img_rl = Image(img_tmp, width=width, height=width * (img.height/img.width))
            row.append(img_rl)
            
            if len(row) == 2:
                grid_data.append(row)
                row = []
        
        if row: 
            row.append("")
            grid_data.append(row)

        t = Table(grid_data, colWidths=[3.4 * inch, 3.4 * inch])
        t.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 18),
        ]))
        story.append(t)

    add_image_section("BEFORE PHOTOS", before_imgs)
    add_image_section("AFTER PHOTOS", after_imgs)

    # 4. Branded Footer
    story.append(Spacer(1, 0.4 * inch))
    footer_style = ParagraphStyle('F', parent=styles['Normal'], fontSize=12, textColor=WHITE, backColor=GLIDE_NAVY, borderPadding=12, alignment=1, borderRadius=6)
    story.append(Paragraph("THANK YOU FOR YOUR BUSINESS! WE APPRECIATE YOU.", footer_style))

    doc.build(story)
    return buffer.getvalue()

# --- Streamlit UI ---
st.set_page_config(page_title="Glide Report Generator", page_icon="🧽")

# Glide Website Theme CSS
st.markdown(f"""
    <style>
    .stButton>button {{ 
        background: linear-gradient(90deg, #f2873a 0%, #ff9e5a 100%);
        color: white; 
        width: 100%; 
        border-radius: 30px; 
        height: 3.5em; 
        font-weight: bold; 
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    .stTextInput div[data-baseweb="input"], .stTextArea div[data-baseweb="base-input"] {{
        border-radius: 10px;
        border-color: #e0e0e0;
    }}
    .stTextInput div[data-baseweb="input"]:focus-within, 
    .stTextArea div[data-baseweb="base-input"]:focus-within {{
        border-color: #f2873a !important;
        box-shadow: 0 0 0 1px #f2873a !important;
    }}
    header {{visibility: hidden;}}
    body {{ background-color: #f0f9fb; }}
    </style>
    """, unsafe_allow_html=True)

st.title("🧽 Glide Report Generator")

name = st.text_input("Customer Name")
phone = st.text_input("Customer Phone")
job_notes = st.text_area("Job Notes")

col1, col2 = st.columns(2)
with col1: before = st.file_uploader("Before Photos", accept_multiple_files=True)
with col2: after = st.file_uploader("After Photos", accept_multiple_files=True)

if st.button("GENERATE GLIDE PDF"):
    if name:
        with st.spinner("Polishing your report..."):
            pdf_data = create_pdf(name, phone, job_notes, before, after)
            st.success("Report Generated!")
            st.download_button("📥 Download Glide Report", pdf_data, f"Glide_Report_{name}.pdf", "application/pdf")
            st.divider()
            st.markdown(f'<iframe src="data:application/pdf;base64,{base64.b64encode(pdf_data).decode()}" width="100%" height="800"></iframe>', unsafe_allow_html=True)
    else:
        st.error("Please enter a Customer Name.")
