import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.units import inch
from io import BytesIO
from PIL import Image as PILImage

# --- Configuration & Styling ---
DUSTY_BLUE = colors.Color(0.28, 0.44, 0.53) # Professional Dusty Blue
WHITE = colors.white

def create_pdf(name, phone, before_imgs, after_imgs):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    story = []
    styles = getSampleStyleSheet()

    # Custom Styles
    title_style = ParagraphStyle(
        'TitleStyle', parent=styles['Heading1'], fontSize=24, textColor=DUSTY_BLUE, 
        spaceAfter=10, alignment=0, fontName='Helvetica-Bold'
    )
    sub_style = ParagraphStyle(
        'SubStyle', parent=styles['Normal'], fontSize=12, textColor=colors.grey, spaceAfter=20
    )
    section_style = ParagraphStyle(
        'SectionStyle', parent=styles['Heading2'], fontSize=16, textColor=WHITE, 
        backColor=DUSTY_BLUE, borderPadding=5, spaceBefore=15, spaceAfter=10
    )

    # Header Section
    story.append(Paragraph("Window Washing Service Report", title_style))
    story.append(Paragraph(f"Customer: {name}  |  Phone: {phone}", sub_style))
    story.append(Spacer(1, 0.2 * inch))

    def process_image_grid(label, uploaded_files):
        if not uploaded_files:
            return
        
        story.append(Paragraph(label, section_style))
        
        row = []
        grid_data = []
        
        for uploaded_file in uploaded_files:
            # Open with PIL to get aspect ratio and resize for the PDF
            img = PILImage.open(uploaded_file)
            aspect = img.height / float(img.width)
            
            # Width is 3 inches per image (2-column grid)
            width = 3 * inch
            height = width * aspect
            
            # Create ReportLab Image
            img_rl = Image(uploaded_file, width=width, height=height)
            row.append(img_rl)
            
            if len(row) == 2:
                grid_data.append(row)
                row = []
        
        if row: # Add the last odd image
            row.append("") # Empty cell for alignment
            grid_data.append(row)

        # Create Table for the Image Grid
        t = Table(grid_data, colWidths=[3.2 * inch, 3.2 * inch])
        t.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ]))
        story.append(t)

    # Add Photos
    process_image_grid("BEFORE TREATMENT", before_imgs)
    story.append(Spacer(1, 0.3 * inch))
    process_image_grid("AFTER TREATMENT", after_imgs)

    # Build PDF
    doc.build(story)
    pdf_out = buffer.getvalue()
    buffer.close()
    return pdf_out

# --- Streamlit UI ---
st.set_page_config(page_title="Pro Window Report", page_icon="🧽")

# Inject some Dusty Blue CSS into the Streamlit Sidebar/Buttons
st.markdown(f"""
    <style>
    .stButton>button {{ background-color: #487087; color: white; border-radius: 5px; }}
    .stTextInput>div>div>input {{ border-color: #487087; }}
    </style>
    """, unsafe_allow_html=True)

st.title("🧽 Pro Window Washing Reports")

with st.container():
    col1, col2 = st.columns(2)
    name = col1.text_input("Customer Name")
    phone = col2.text_input("Customer Phone")

st.divider()

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Before Photos")
    before_files = st.file_uploader("Upload Before", accept_multiple_files=True, key="before")
with col_b:
    st.subheader("After Photos")
    after_files = st.file_uploader("Upload After", accept_multiple_files=True, key="after")

if st.button("✨ Create Professional PDF"):
    if name:
        with st.spinner("Polishing the report..."):
            pdf_data = create_pdf(name, phone, before_files, after_files)
            st.success("Report Ready!")
            st.download_button(
                label="📥 Download Report",
                data=pdf_data,
                file_name=f"Report_{name.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )
    else:
        st.warning("Please enter a customer name.")
