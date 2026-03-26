import streamlit as st
from fpdf import FPDF
from PIL import Image
import tempfile
import os

# --- Helper Functions ---

class WindowWashingPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Window Washing Job Report', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')

    def add_section_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(2)

    def add_customer_details(self, name, phone, details):
        self.set_font('Arial', '', 11)
        self.cell(0, 10, f"Customer Name: {name}", 0, 1, 'L')
        self.cell(0, 10, f"Customer Phone: {phone}", 0, 1, 'L')
        self.ln(5)
        if details:
            self.add_section_title("Job Details:")
            self.set_font('Arial', '', 10)
            self.multi_cell(0, 5, details)
            self.ln(5)

    def add_images(self, title, image_files):
        self.add_section_title(title)
        
        if not image_files:
            self.set_font('Arial', 'I', 10)
            self.cell(0, 10, 'No images provided for this section.', 0, 1, 'L')
            self.ln(5)
            return

        x_start = 10
        y_start = self.get_y()
        # Define image width (assuming 2 columns, leaving margins)
        img_width = (210 - 20 - 10) / 2 # 210mm A4 width - 20mm margins - 10mm gap

        column = 0
        for uploaded_file in image_files:
            try:
                # Need to use PIL to handle different formats and potentially rotate based on EXIF
                # However, FPDF handles resizing directly. We'll simplify here and just use the file object.
                # In production, processing with PIL is recommended.
                
                # Check if adding this image will cause a page break. FPDF isn't great at auto-managing this
                # when mixed with multi_cell or specific image placements. Simplified for now.
                
                # Create a temporary file because FPDF needs a file path or URL
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmpfile:
                    image = Image.open(uploaded_file)
                    # Simple conversion to RGB/PNG to ensure compatibility and consistent handling
                    image = image.convert('RGB')
                    image.save(tmpfile.name, format="PNG")
                    tmp_filename = tmpfile.name

                self.image(tmp_filename, x=x_start + (column * (img_width + 10)), y=None, w=img_width)
                
                # Delete temporary file
                os.unlink(tmp_filename)

                # Track position to decide next action
                column += 1
                if column > 1:
                    column = 0
                    # This method of placing images requires manual Y adjustment, which is complex.
                    # Simplified layout: Just put images one after another in a list format.
                    # self.ln(5) # Add spacing after a row
            
            except Exception as e:
                self.set_font('Arial', 'I', 10)
                self.cell(0, 10, f"Error processing image: {str(e)}", 0, 1, 'L')

        self.ln(10) # Add final spacing after the section

def generate_pdf(customer_name, customer_phone, job_details, before_images, after_images):
    pdf = WindowWashingPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Customer and Job Details
    pdf.add_customer_details(customer_name, customer_phone, job_details)
    
    # Before Images
    pdf.add_images("Before Photos:", before_images)
    
    # After Images
    pdf.add_images("After Photos:", after_images)
    
    # Save to memory stream
    return pdf.output(dest='S').encode('latin-1')

# --- Main App Interface ---

st.set_page_config(page_title="Window Washing Report Generator", layout="centered")

st.title("🧽 Window Washing Job Report Generator")
st.markdown("Create a simple PDF report for your customer.")

st.header("1. Customer Information")
col1, col2 = st.columns(2)
with col1:
    customer_name = st.text_input("Customer Name", placeholder="e.g. John Doe")
with col2:
    customer_phone = st.text_input("Customer Phone", placeholder="e.g. 555-123-4567")

st.header("2. Job Details (Optional)")
job_details = st.text_area("Add notes about the job, specifics, or feedback:", height=100)

st.header("3. Photos")
st.info("You can upload multiple pictures at once in each section.")

# Define image upload components
uploaded_before = st.file_uploader("Upload 'Before' photos", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
uploaded_after = st.file_uploader("Upload 'After' photos", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)

st.header("4. Generate Report")

if st.button("Create Document"):
    if not customer_name:
        st.error("Please enter the customer name before generating the PDF.")
    else:
        with st.spinner("Generating PDF report..."):
            try:
                pdf_bytes = generate_pdf(
                    customer_name,
                    customer_phone,
                    job_details,
                    uploaded_before,
                    uploaded_after
                )
                
                # Setup download button
                # Generate a filename using the customer name
                filename = f"{customer_name.replace(' ', '_')}_JobReport.pdf"
                
                st.success("Report generated successfully!")
                st.download_button(
                    label="📥 Download PDF Report",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf"
                )
                
            except Exception as e:
                st.error(f"An error occurred during PDF generation: {e}")
                st.info("Ensure all uploaded files are valid image formats (JPG, PNG).")
