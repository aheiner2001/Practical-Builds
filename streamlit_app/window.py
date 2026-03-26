import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.units import inch
from io import BytesIO
from PIL import Image as PILImage, ImageOps

# --- Configuration ---
DUSTY_BLUE = colors.Color(0.28, 0.44, 0.53) # RGB: 72, 112, 135
WHITE = colors.white

def create_pdf(name, phone, before_imgs, after_imgs):
    buffer = BytesIO()
    # Bottom margin increased to 70 to make room for the footer
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=70)
    story = []
    styles = getSampleStyleSheet()

    # --- Styles ---
    title_style = ParagraphStyle(
        'TitleStyle', parent=styles['Heading1'], fontSize=26, textColor=DUSTY_BLUE, 
        spaceAfter=10, fontName='Helvetica-Bold'
    )
    section_style = ParagraphStyle(
        'SectionStyle', parent=styles['Heading2'], fontSize=14, textColor=WHITE, 
        backColor=DUSTY_BLUE, borderPadding=6, spaceBefore=15, spaceAfter=12, alignment=1
    )
    footer_style = ParagraphStyle(
        'FooterStyle', parent=styles['Normal'], fontSize=12, textColor=WHITE, 
        backColor=DUSTY_BLUE, borderPadding=10, alignment=1
    )

    # 1. Header Section
    story.append(Paragraph("WINDOW WASHING REPORT", title_style))
    story.append(Paragraph(f"<b>Customer:</b> {name.upper()} &nbsp;&nbsp; | &nbsp;&nbsp; <b>Phone:</b> {phone}", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))

    # 2. Image Processing Logic (with Rotation Fix)
    def add_image_section(label, files):
        if not files: return
        story.append(Paragraph(label, section_style))
        grid_data = []
        row = []
        
        for uploaded_file in files:
            # FIX: Open and correct orientation
            img = PILImage.open(uploaded_file)
            img = ImageOps.exif_transpose(img) 
            
            # Save corrected image to a temporary buffer
            img_tmp = BytesIO()
            img.save(img_tmp, format="PNG")
            img_tmp.seek(0)

            # Standardize sizing for a 2-column layout
            aspect = img.height / float(img.width)
            width = 3.1 * inch
            height = width * aspect
            
            img_rl = Image(img_tmp, width=width, height=height)
            row.append(img_rl)
            
            if len(row) == 2:
                grid_data.append(row)
                row = []
        
        if row: # Add remaining image
            row.append("")
            grid_data.append(row)

        t = Table(grid_data, colWidths=[3.3 * inch, 3.3 * inch])
        t.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 15),
        ]))
        story.append(t)

    # Add the sections
    add_image_section("BEFORE SERVICE", before_imgs)
    story.append(Spacer(1, 0.2 * inch))
    add_image_section("AFTER SERVICE", after_imgs)

    # 3. Professional "Thank You" Footer
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("THANK YOU FOR YOUR BUSINESS! WE APPRECIATE YOU.", footer_style))

    # Build PDF
    doc.build(story)
    pdf_out = buffer.getvalue()
    buffer.close()
    return pdf_out

# --- Streamlit UI ---
st.set_page_config(page_title="Pro Window Report", page_icon="🧽")

# Custom CSS for that Dusty Blue feel in the app itself
st.markdown("""
    <style>
    .stButton>button { background-color: #487087; color: white; width: 100%; border-radius: 8px; height: 3em; font-weight: bold; }
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

st.title("🧽 Report Generator")

name = st.text_input("Customer Name", placeholder="John Smith")
phone = st.text_input("Customer Phone", placeholder="(555) 000-0000")

col1, col2 = st.columns(2)
with col1:
    before = st.file_uploader("Before Photos", accept_multiple_files=True)
with col2:
    after = st.file_uploader("After Photos", accept_multiple_files=True)
import base64

def display_pdf(pdf_bytes):
    # Encode the PDF to base64 for embedding in an iframe
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)
if st.button("GENERATE PROFESSIONAL PDF"):
    if name:
        with st.spinner("Processing images and generating report..."):
            pdf_data = create_pdf(name, phone, before, after)
            st.success("Report Generated!")
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_data,
                file_name=f"Report_{name.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )
    else:
        st.error("Please enter a Customer Name to continue.")
