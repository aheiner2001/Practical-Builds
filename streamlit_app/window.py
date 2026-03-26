import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.units import inch
from io import BytesIO
from PIL import Image as PILImage, ImageOps
import base64

# --- Configuration ---
DUSTY_BLUE = colors.Color(0.28, 0.44, 0.53) # RGB: 72, 112, 135
WHITE = colors.white

def create_pdf(name, phone, notes, before_imgs, after_imgs): # Added 'notes' parameter
    buffer = BytesIO()
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
    # Style for the notes text
    notes_style = ParagraphStyle(
        'NotesStyle', parent=styles['Normal'], fontSize=11, leading=14, 
        textColor=colors.black, leftIndent=10, rightIndent=10
    )
    footer_style = ParagraphStyle(
        'FooterStyle', parent=styles['Normal'], fontSize=12, textColor=WHITE, 
        backColor=DUSTY_BLUE, borderPadding=10, alignment=1
    )

    # 1. Header Section
    story.append(Paragraph("WINDOW WASHING REPORT", title_style))
    story.append(Paragraph(f"<b>Customer:</b> {name.upper()} &nbsp;&nbsp; | &nbsp;&nbsp; <b>Phone:</b> {phone}", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))

    # --- NEW: Notes Section ---
    if notes:
        story.append(Paragraph("JOB NOTES & OBSERVATIONS", section_style))
        # We put notes in a simple table to give it a slight border/structure if desired
        story.append(Paragraph(notes.replace('\n', '<br/>'), notes_style))
        story.append(Spacer(1, 0.2 * inch))

    # 2. Image Processing Logic
    def add_image_section(label, files):
        if not files: return
        story.append(Paragraph(label, section_style))
        grid_data = []
        row = []
        
        for uploaded_file in files:
            img = PILImage.open(uploaded_file)
            img = ImageOps.exif_transpose(img) 
            img_tmp = BytesIO()
            img.save(img_tmp, format="PNG")
            img_tmp.seek(0)

            aspect = img.height / float(img.width)
            width = 3.1 * inch
            height = width * aspect
            
            img_rl = Image(img_tmp, width=width, height=height)
            row.append(img_rl)
            
            if len(row) == 2:
                grid_data.append(row)
                row = []
        
        if row:
            row.append("")
            grid_data.append(row)

        t = Table(grid_data, colWidths=[3.3 * inch, 3.3 * inch])
        t.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 15),
        ]))
        story.append(t)

    add_image_section("BEFORE SERVICE", before_imgs)
    story.append(Spacer(1, 0.2 * inch))
    add_image_section("AFTER SERVICE", after_imgs)

    # 3. Footer
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("THANK YOU FOR YOUR BUSINESS! WE APPRECIATE YOU.", footer_style))

    doc.build(story)
    pdf_out = buffer.getvalue()
    buffer.close()
    return pdf_out

# --- Streamlit UI ---
st.set_page_config(page_title="Pro Window Report", page_icon="🧽")

# Custom CSS for that Dusty Blue feel and fixing the red outline
st.markdown(f"""
    <style>
    /* 1. Style the buttons */
    .stButton>button {{ 
        background-color: #487087; 
        color: white; 
        width: 100%; 
        border-radius: 8px; 
        height: 3em; 
        font-weight: bold; 
        border: none;
    }}
    
    /* 2. Change the border color when you CLICK into a box (Focus) */
    .stTextInput div[data-baseweb="input"], .stTextArea div[data-baseweb="base-input"] {{
        border-color: #e0e0e0; /* Default border color when not selected */
    }}

    /* This part removes the red/orange and replaces it with Dusty Blue */
    .stTextInput div[data-baseweb="input"]:focus-within, 
    .stTextArea div[data-baseweb="base-input"]:focus-within {{
        border-color: #487087 !important;
        box-shadow: 0 0 0 1px #487087 !important;
    }}

    /* 3. Hide the Streamlit header for a cleaner look */
    header {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

st.title("🧽 Report Generator")

name = st.text_input("Customer Name", placeholder="John Smith")
phone = st.text_input("Customer Phone", placeholder="(555) 000-0000")

# NEW: Note section in UI
job_notes = st.text_area("Job Notes", placeholder="E.g., Cleared hard water stains on west side, noted small screen tear in kitchen...")

col1, col2 = st.columns(2)
with col1:
    before = st.file_uploader("Before Photos", accept_multiple_files=True)
with col2:
    after = st.file_uploader("After Photos", accept_multiple_files=True)

def display_pdf(pdf_bytes):
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

if st.button("GENERATE PROFESSIONAL PDF"):
    if name:
        with st.spinner("Processing..."):
            # Pass job_notes to the function
            pdf_data = create_pdf(name, phone, job_notes, before, after)
            st.success("Report Generated!")
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_data,
                file_name=f"Report_{name.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )
            
            
    else:
        st.error("Please enter a Customer Name to continue.")
