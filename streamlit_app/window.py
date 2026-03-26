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

def create_pdf(name, phone, notes, before_imgs, after_imgs):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=70)
    story = []
    styles = getSampleStyleSheet()

    # --- Styles ---
    title_style = ParagraphStyle(
        'TitleStyle', parent=styles['Heading1'], fontSize=28, textColor=DUSTY_BLUE, 
        spaceAfter=15, fontName='Helvetica-Bold'
    )
    
    # NEW: Cleaner Section Header Style (Bordered)
    section_style = ParagraphStyle(
        'SectionStyle', parent=styles['Heading2'], fontSize=12, textColor=DUSTY_BLUE, 
        backColor=colors.whitesmoke, borderColor=DUSTY_BLUE, borderWidth=1,
        borderPadding=8, spaceBefore=20, spaceAfter=10, fontName='Helvetica-Bold',
        alignment=0, borderRadius=4
    )

    info_style = ParagraphStyle(
        'InfoStyle', parent=styles['Normal'], fontSize=11, leading=16, textColor=colors.black
    )
    
    notes_style = ParagraphStyle(
        'NotesStyle', parent=styles['Normal'], fontSize=11, leading=15, 
        textColor=colors.black
    )

    footer_style = ParagraphStyle(
        'FooterStyle', parent=styles['Normal'], fontSize=11, textColor=WHITE, 
        backColor=DUSTY_BLUE, borderPadding=10, alignment=1, borderRadius=4
    )

    # 1. Header Section
    story.append(Paragraph("WINDOW WASHING REPORT", title_style))
    
    review_url = "https://share.google/jPmaCiXb5TcV3MCwu"
    service_text = f"""
    <b>Serviced by:</b> Aaron Heiner<br/>
    <b>Customer:</b> {name.upper()} &nbsp;&nbsp; | &nbsp;&nbsp; <b>Phone:</b> {phone}<br/>
    <a href="{review_url}" color="#487087"><u>It would help me a ton if you could leave a review for Glide Window Cleaning! If you could mention my name (Aaron) in the review, it helps me out even more. Thank you for your support!"</u></a>
    """
    story.append(Paragraph(service_text, info_style))
    story.append(Spacer(1, 0.1 * inch))

    # 2. JOB NOTES (Boxed Section)
    if notes:
        story.append(Paragraph("JOB NOTES & OBSERVATIONS", section_style))
        
        # Wrapping notes in a table to create a clean border box
        notes_data = [[Paragraph(notes.replace('\n', '<br/>'), notes_style)]]
        notes_table = Table(notes_data, colWidths=[6.8 * inch])
        notes_table.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('LEFTPADDING', (0,0), (-1,-1), 15),
            ('RIGHTPADDING', (0,0), (-1,-1), 15),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('BACKGROUND', (0,0), (-1,-1), colors.white),
        ]))
        story.append(notes_table)

    # 3. Image Processing
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
            width = 3.2 * inch
            height = width * aspect
            
            img_rl = Image(img_tmp, width=width, height=height)
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
            ('BOTTOMPADDING', (0,0), (-1,-1), 15),
        ]))
        story.append(t)

    add_image_section("BEFORE PHOTOS", before_imgs)
    add_image_section("AFTER PHOTOS", after_imgs)

    # 4. Footer
    story.append(Spacer(1, 0.4 * inch))
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
