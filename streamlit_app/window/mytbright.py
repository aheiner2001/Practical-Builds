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
from reportlab.platypus import HRFlowable

# --- Theme ---
NAVY = colors.HexColor("#1F3A5F")
SLATE = colors.HexColor("#6B7A8F")
LIGHT_BG = colors.HexColor("#F4F7FB")
ACCENT = colors.HexColor("#448AFF")
GREEN = colors.HexColor("#1F3A5F")
CTA_BORDER = colors.HexColor("#1F3A5F")

import os
LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")


def get_weather(city):
    try:
        lat = 40.0966
        lon = -111.5707
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current_weather=true&temperature_unit=fahrenheit"
        )
        w_res = requests.get(weather_url).json()
        temp = w_res['current_weather']['temperature']
        return f"{int(temp)}°F"
    except Exception:
        return "Weather unavailable"


def create_pdf(name, phone, notes, before_imgs, after_imgs, city, crew_member=""):
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

    # --- TIME ---
    local_tz = pytz.timezone('US/Mountain')
    now_local = datetime.now(local_tz)
    submit_time = now_local.strftime("%B %d, %Y at %I:%M %p")

    current_weather = get_weather(city)

    # --- STYLES (left-aligned throughout) ---

    info_style = ParagraphStyle(
        'Info',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        leading=16,
        alignment=0,  # left
    )

    left_info = ParagraphStyle(
        'LeftInfo',
        parent=info_style,
        spaceBefore=8,
        spaceAfter=8,
        alignment=0,
    )

    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=NAVY,
        alignment=0,  # left
        spaceAfter=2,
        fontName='Helvetica-Bold'
    )

    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=SLATE,
        alignment=0,  # left
        spaceAfter=4,
    )

    customer_style = ParagraphStyle(
        'Customer',
        parent=styles['Normal'],
        fontSize=12,
        textColor=NAVY,
        alignment=0,  # left
        spaceAfter=16,
        fontName='Helvetica-Bold'
    )

    service_tag_style = ParagraphStyle(
        'ServiceTag',
        parent=styles['Normal'],
        fontSize=11,
        textColor=ACCENT,
        alignment=0,  # left
        spaceAfter=14,
        fontName='Helvetica-Bold'
    )

    header_style = ParagraphStyle(
        'HeaderSub',
        parent=styles['Normal'],
        fontSize=11,
        textColor=GREEN,
        alignment=0,
        spaceBefore=20,
        spaceAfter=10,
        leftIndent=0,
        fontName='Helvetica-Bold'
    )

    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=SLATE,
        alignment=1  # center footer only
    )

    # --- HEADER BLOCK ---
    # Logo + title side by side
    if os.path.exists(LOGO_PATH):
        logo_img = Image(LOGO_PATH, width=1.6*inch, height=0.6*inch)
    else:
        logo_img = Paragraph("My-T-Brite", title_style)

    header_title = Paragraph(
        "<b>My-T-Brite</b><br/><font size=9 color='#448AFF'>SERVICE REPORT</font>",
        ParagraphStyle('HdrTitle', parent=styles['Normal'], fontSize=18,
                       textColor=NAVY, alignment=0, fontName='Helvetica-Bold', leading=22)
    )

    header_table = Table(
        [[logo_img, header_title]],
        colWidths=[1.8*inch, 5.0*inch]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(header_table)
    story.append(Paragraph(submit_time, subtitle_style))
    story.append(Paragraph(f"Customer: {name}", customer_style))

    # --- DIVIDER ---
    story.append(HRFlowable(width="100%", thickness=1.5, color=NAVY, spaceBefore=0, spaceAfter=16))

    # --- REVIEW BOX ---
    review_url = "https://share.google/QCCYgjvzS4KF6aCQe"

    # Build the name mention line dynamically
    if crew_member.strip():
        name_mention = f"If you mention <b>Aaron</b> and <b>{crew_member.strip()}</b> by name, it helps even more!"
    else:
        name_mention = "If you mention <b>Aaron</b> by name, it helps even more!"

    review_para = Paragraph(
        f"""
        We'd love it if you left us a review!<br/>
        {name_mention}<br/><br/>
        <font color="#448AFF"><a href="{review_url}"><b>Leave a review here</b></a></font>
        """,
        left_info
    )

    review_box = Table([[review_para]], colWidths=[6.8 * inch])
    review_box.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1.2, CTA_BORDER),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))

    story.append(review_box)
    story.append(Spacer(1, 0.3 * inch))

    # --- NOTES ---
    if notes:
        story.append(Paragraph("JOB NOTES", header_style))
        story.append(HRFlowable(width="100%", thickness=1, color=GREEN, spaceBefore=0, spaceAfter=8))

        notes_table = Table(
            [[Paragraph(notes.replace('\n', '<br/>'), info_style)]],
            colWidths=[6.8 * inch]
        )
        notes_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, SLATE),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(notes_table)

    # --- IMAGE HELPER ---
    def add_imgs(label, files):
        if not files:
            return

        story.append(Paragraph(label, header_style))
        story.append(HRFlowable(width="100%", thickness=1, color=GREEN, spaceBefore=0, spaceAfter=8))

        grid = []
        row = []

        for f in files:
            img = ImageOps.exif_transpose(PILImage.open(f))
            tmp = BytesIO()
            img.save(tmp, format="PNG")
            tmp.seek(0)

            aspect = img.height / img.width
            row.append(Image(tmp, width=3.2 * inch, height=3.2 * inch * aspect))

            if len(row) == 2:
                grid.append(row)
                row = []

        if row:
            row.append("")
            grid.append(row)

        table = Table(grid, colWidths=[3.4 * inch, 3.4 * inch])
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ]))

        story.append(table)
        story.append(Spacer(1, 0.25 * inch))

    # --- IMAGES ---
    add_imgs("BEFORE – FEATURED PHOTOS", before_imgs)
    add_imgs("AFTER – FEATURED PHOTOS", after_imgs)

    # --- FOOTER ---
    story.append(Spacer(1, 0.3 * inch))
    story.append(HRFlowable(width="100%", thickness=0.5, color=SLATE, spaceBefore=0, spaceAfter=8))
    story.append(Paragraph("• My-T-Brite •", footer_style))

    doc.build(story)
    return buffer.getvalue()


# --- STREAMLIT UI ---
st.set_page_config(page_title="My-T-Brite Report Generator", layout="centered")

import os as _os
_logo = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "logo.png")
if _os.path.exists(_logo):
    st.image(_logo, width=220)
else:
    st.title("My-T-Brite")
st.subheader("Service Report Generator")
st.markdown("---")

col_name, col_phone = st.columns(2)
with col_name:
    name = st.text_input("Customer Name")
with col_phone:
    phone = st.text_input("Customer Phone")

crew_member = st.text_input("Crew Member (optional)", placeholder="e.g. Jake")

st.markdown("**Quick Message Snippets**")
st.caption("Check any that apply — they'll be added to the notes automatically.")

use_simple = st.checkbox("✅ Simple / Thank you")
use_trash = st.checkbox("🗑️ Trash pickup")
use_hardwater = st.checkbox("💧 Hard water stains")
use_damage = st.checkbox("🪟 Window Pane Damage (pictures added)")
use_closing = st.checkbox("👋 Closing message")

notes = st.text_area("Job Notes & Observations", height=120)

city = "Rexburg"

st.markdown("**Photos**")
c1, c2 = st.columns(2)
with c1:
    before = st.file_uploader("Before Photos", accept_multiple_files=True)
with c2:
    after = st.file_uploader("After Photos", accept_multiple_files=True)

st.markdown("")
if st.button("GENERATE REPORT PDF", use_container_width=True, type="primary"):
    if name:
        with st.spinner("Building your report..."):
            # Build snippet messages (closing always pinned to end)
            snippets = []
            if use_simple:
                snippets.append(f"Thank you {name}, everything looks great.")
            if use_trash:
                snippets.append("We were able to pick up a bit of trash around the house that we saw.")
            if use_hardwater:
                snippets.append("A few windows had bad hard water stains, we did the best we could. We used hard water removal and it looks a ton better.")
            if use_damage:
                snippets.append("We added pictures of some windows that had a gas leak.")

            # Manual notes sit after snippets; closing always last
            all_parts = snippets + ([notes.strip()] if notes.strip() else [])
            if use_closing:
                all_parts.append(f"Have a wonderful day! Enjoy your windows, {name}!")

            final_notes = "  ".join(all_parts)

            pdf = create_pdf(name, phone, final_notes, before, after, city, crew_member)
            st.download_button(
                "📥 Download PDF",
                pdf,
                f"MyTBrite_Report_{name.replace(' ', '_')}.pdf",
                "application/pdf",
                use_container_width=True
            )
    else:
        st.error("Please enter a Customer Name.")
