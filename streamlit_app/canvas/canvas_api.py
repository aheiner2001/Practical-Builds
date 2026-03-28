import streamlit as st
from canvasapi import Canvas
from datetime import datetime, timezone
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from collections import defaultdict

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Canvas Dashboard",
    page_icon="📚",
    layout="wide",
)

# ─── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Instrument+Sans:wght@300;400;500&display=swap');

  html, body, [class*="css"] {
    font-family: 'Instrument Sans', sans-serif;
    background: #f7f4ef;
    color: #1a1a1a;
  }

  h1, h2, h3 { font-family: 'Syne', sans-serif; }

  .brand {
    font-family: 'Syne', sans-serif;
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -1px;
    color: #1a1a1a;
    line-height: 1;
  }
  .brand span { color: #d4622a; }

  .greeting {
    font-size: 0.85rem;
    color: #888;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 0.2rem;
  }

  .metric-card {
    background: #fff;
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    border: 1px solid #e8e4de;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  }

  .metric-label {
    font-size: 0.72rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #999;
    margin-bottom: 0.3rem;
  }

  .metric-value {
    font-family: 'Syne', sans-serif;
    font-size: 2.4rem;
    font-weight: 700;
    color: #1a1a1a;
    line-height: 1;
  }

  .metric-sub {
    font-size: 0.78rem;
    color: #aaa;
    margin-top: 0.2rem;
  }

  .assignment-row {
    background: #fff;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.6rem;
    border: 1px solid #e8e4de;
    display: flex;
    align-items: center;
    gap: 1rem;
    transition: box-shadow 0.15s;
  }

  .assignment-row:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.08); }

  .due-badge {
    font-family: 'Syne', sans-serif;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 20px;
    white-space: nowrap;
  }

  .badge-urgent { background: #fde8e0; color: #c0390f; }
  .badge-soon   { background: #fef3cd; color: #a07000; }
  .badge-later  { background: #e8f4e8; color: #2d7a2d; }
  .badge-none   { background: #f0f0f0; color: #888; }

  .course-chip {
    font-size: 0.72rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    padding: 2px 10px;
    border-radius: 20px;
    font-weight: 500;
    white-space: nowrap;
  }

  .section-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: -0.3px;
    margin: 1.5rem 0 0.8rem 0;
    color: #1a1a1a;
  }

  .divider {
    border: none;
    border-top: 1px solid #e8e4de;
    margin: 1.5rem 0;
  }

  /* Streamlit overrides */
  .stTextInput input, .stTextInput textarea {
    border-radius: 10px !important;
    border: 1px solid #ddd !important;
    font-family: 'Instrument Sans', sans-serif !important;
  }
  .stButton > button {
    background: #d4622a !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px !important;
    padding: 0.5rem 1.5rem !important;
  }
  .stButton > button:hover { opacity: 0.88 !important; }
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 2rem; max-width: 1200px; }

  .stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    background: transparent;
    border-bottom: 2px solid #e8e4de;
  }
  .stTabs [data-baseweb="tab"] {
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    color: #aaa !important;
    background: transparent !important;
    border: none !important;
    padding: 0.5rem 1rem !important;
  }
  .stTabs [aria-selected="true"] {
    color: #d4622a !important;
    border-bottom: 2px solid #d4622a !important;
  }
</style>
""", unsafe_allow_html=True)

COURSE_COLORS = ["#d4622a", "#2a7dd4", "#2ad47a", "#d4c02a", "#9b2ad4", "#2ad4c0"]

# ─── Helpers ───────────────────────────────────────────────────────────────────
def days_until(due_date):
    if due_date is None:
        return None
    now = datetime.now(timezone.utc)
    if not due_date.tzinfo:
        due_date = due_date.replace(tzinfo=timezone.utc)
    return (due_date - now).days

def urgency_badge(days):
    if days is None:
        return "badge-none", "No Due Date"
    if days < 0:
        return "badge-urgent", "Overdue"
    if days == 0:
        return "badge-urgent", "Due Today"
    if days <= 3:
        return "badge-urgent", f"{days}d left"
    if days <= 7:
        return "badge-soon", f"{days}d left"
    return "badge-later", f"{days}d left"

def get_grade_color(score):
    if score is None: return "#ccc"
    if score >= 90: return "#2d7a2d"
    if score >= 80: return "#5a9e5a"
    if score >= 70: return "#a07000"
    if score >= 60: return "#c0390f"
    return "#8b0000"

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="brand">canvas<span>.</span></p>', unsafe_allow_html=True)
    st.markdown('<p class="greeting">Student Dashboard</p>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Load API key from Streamlit secrets
    api_key = st.secrets.get("CANVAS_API_KEY", "")
    api_url = st.secrets.get("CANVAS_URL", "https://byui.instructure.com/")

    if not api_key:
        st.error("Add CANVAS_API_KEY to your Streamlit secrets.")
    else:
        st.markdown('<p style="font-size:0.78rem;color:#2d7a2d;">🔒 API key loaded from secrets</p>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Course IDs** (comma separated)")
    course_ids_input = st.text_input("", value="404060, 403442, 406222", label_visibility="collapsed")

    load_btn = st.button("Load Dashboard", use_container_width=True)

# ─── Main ──────────────────────────────────────────────────────────────────────
if not api_key or not load_btn:
    # Landing state
    st.markdown('<p class="brand" style="font-size:3rem;">canvas<span style="color:#d4622a">.</span></p>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:1.1rem;color:#888;max-width:480px;margin-top:0.5rem;">Click Load Dashboard in the sidebar to get started.</p>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    for col, icon, title, desc in [
        (c1, "📅", "Assignments by Due Date", "See everything sorted by deadline"),
        (c2, "📊", "Grade Visualizations", "Charts for your current standing"),
        (c3, "🔥", "Urgency Tracker", "Know what needs attention now"),
    ]:
        with col:
            st.markdown(f"""
            <div class="metric-card">
              <div style="font-size:1.8rem;margin-bottom:0.5rem;">{icon}</div>
              <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:1rem;">{title}</div>
              <div style="font-size:0.82rem;color:#999;margin-top:0.3rem;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
    st.stop()

# ─── Load Data ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_canvas_data(api_key, api_url, course_ids):
    canvas = Canvas(api_url, api_key)
    user = canvas.get_current_user()
    courses_data = []
    all_assignments = []

    for i, cid in enumerate(course_ids):
        try:
            course = canvas.get_course(int(cid.strip()))
            color = COURSE_COLORS[i % len(COURSE_COLORS)]

            # Grades
            enrollment = None
            try:
                enrollments = list(course.get_enrollments(user_id=user.id, type=['StudentEnrollment']))
                if enrollments:
                    enrollment = enrollments[0]
            except:
                pass

            grade = None
            if enrollment and hasattr(enrollment, 'grades'):
                grade = enrollment.grades.get('current_score')

            courses_data.append({
                "id": cid.strip(),
                "name": course.name,
                "short": course.name.split()[0],
                "color": color,
                "grade": grade,
            })

            # Assignments
            try:
                assignments = course.get_assignments(bucket='unsubmitted', order_by='due_at')
                for a in assignments:
                    due = getattr(a, 'due_at_date', None)
                    points = getattr(a, 'points_possible', None)
                    all_assignments.append({
                        "name": a.name,
                        "course": course.name,
                        "course_short": course.name.split()[0],
                        "color": color,
                        "due_date": due,
                        "days_until": days_until(due),
                        "points": points,
                        "url": getattr(a, 'html_url', '#'),
                    })
            except:
                pass

        except Exception as e:
            st.warning(f"Could not load course {cid}: {e}")

    # Sort assignments by due date
    all_assignments.sort(key=lambda x: (x['due_date'] is None, x['due_date'] or datetime.max.replace(tzinfo=timezone.utc)))
    return user, courses_data, all_assignments

course_ids = [c.strip() for c in course_ids_input.split(",") if c.strip()]

with st.spinner("Loading your Canvas data..."):
    try:
        user, courses_data, all_assignments = load_canvas_data(api_key, api_url, tuple(course_ids))
    except Exception as e:
        st.error(f"❌ Could not connect to Canvas: {e}")
        st.stop()

# ─── Header ────────────────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown(f'<p class="brand">Hey, {user.name.split()[0]}<span>.</span></p>', unsafe_allow_html=True)
    st.markdown(f'<p class="greeting">{datetime.now().strftime("%A, %B %d")}</p>', unsafe_allow_html=True)

# ─── Metric Cards ──────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
m1, m2, m3, m4 = st.columns(4)

overdue = sum(1 for a in all_assignments if a['days_until'] is not None and a['days_until'] < 0)
due_soon = sum(1 for a in all_assignments if a['days_until'] is not None and 0 <= a['days_until'] <= 3)
avg_grade = None
grades = [c['grade'] for c in courses_data if c['grade'] is not None]
if grades:
    avg_grade = sum(grades) / len(grades)

for col, label, value, sub, accent in [
    (m1, "Unsubmitted", str(len(all_assignments)), "assignments", "#d4622a"),
    (m2, "Overdue", str(overdue), "need attention", "#c0390f"),
    (m3, "Due in 3 Days", str(due_soon), "coming up fast", "#a07000"),
    (m4, "Avg Grade", f"{avg_grade:.1f}%" if avg_grade else "—", "across courses", "#2d7a2d"),
]:
    with col:
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-label">{label}</div>
          <div class="metric-value" style="color:{accent}">{value}</div>
          <div class="metric-sub">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📅  Assignments", "📊  Grades", "🔥  Urgency"])

# ══ Tab 1: Assignments ════════════════════════════════════════════════════════
with tab1:
    if not all_assignments:
        st.success("🎉 No unsubmitted assignments found!")
    else:
        # Filter
        filter_col1, filter_col2 = st.columns([2, 1])
        with filter_col1:
            search = st.text_input("Search assignments", placeholder="Filter by name...", label_visibility="collapsed")
        with filter_col2:
            course_filter = st.selectbox("Course", ["All"] + [c['name'] for c in courses_data], label_visibility="collapsed")

        filtered = all_assignments
        if search:
            filtered = [a for a in filtered if search.lower() in a['name'].lower()]
        if course_filter != "All":
            filtered = [a for a in filtered if a['course'] == course_filter]

        st.markdown(f'<p style="font-size:0.8rem;color:#aaa;margin-bottom:0.8rem;">{len(filtered)} assignments</p>', unsafe_allow_html=True)

        for a in filtered:
            badge_class, badge_text = urgency_badge(a['days_until'])
            due_str = a['due_date'].strftime("%b %d, %I:%M %p") if a['due_date'] else "No due date"
            pts = f"{int(a['points'])} pts" if a['points'] else ""

            st.markdown(f"""
            <div class="assignment-row">
              <div style="width:10px;height:40px;border-radius:4px;background:{a['color']};flex-shrink:0;"></div>
              <div style="flex:1;min-width:0;">
                <div style="font-family:'Syne',sans-serif;font-weight:600;font-size:0.95rem;
                     white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{a['name']}</div>
                <div style="font-size:0.78rem;color:#999;margin-top:2px;">
                  <span class="course-chip" style="background:{a['color']}22;color:{a['color']}">{a['course_short']}</span>
                  &nbsp;{due_str}&nbsp;{pts}
                </div>
              </div>
              <span class="due-badge {badge_class}">{badge_text}</span>
            </div>
            """, unsafe_allow_html=True)

# ══ Tab 2: Grades ═════════════════════════════════════════════════════════════
with tab2:
    if not any(c['grade'] for c in courses_data):
        st.info("No grade data available for your courses.")
    else:
        g1, g2 = st.columns([1, 1])

        with g1:
            st.markdown('<p class="section-title">Current Grades</p>', unsafe_allow_html=True)
            for c in courses_data:
                grade = c['grade']
                if grade is None:
                    continue
                bar_color = get_grade_color(grade)
                st.markdown(f"""
                <div class="metric-card" style="margin-bottom:0.6rem;padding:1rem 1.2rem;">
                  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;">
                    <span style="font-family:'Syne',sans-serif;font-weight:600;font-size:0.9rem;">{c['name']}</span>
                    <span style="font-family:'Syne',sans-serif;font-weight:700;color:{bar_color}">{grade:.1f}%</span>
                  </div>
                  <div style="background:#f0ece4;border-radius:4px;height:8px;">
                    <div style="width:{min(grade,100):.1f}%;background:{bar_color};height:8px;border-radius:4px;transition:width 0.5s;"></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

        with g2:
            st.markdown('<p class="section-title">Grade Overview</p>', unsafe_allow_html=True)
            graded = [(c['name'], c['grade'], c['color']) for c in courses_data if c['grade'] is not None]
            if graded:
                fig = go.Figure()
                names, vals, colors = zip(*graded)
                fig.add_trace(go.Bar(
                    x=list(names),
                    y=list(vals),
                    marker_color=list(colors),
                    marker_line_width=0,
                    text=[f"{v:.1f}%" for v in vals],
                    textposition='outside',
                    textfont=dict(family="Syne", size=13, color="#1a1a1a"),
                ))
                fig.add_hline(y=90, line_dash="dot", line_color="#2d7a2d", line_width=1, annotation_text="A", annotation_font_color="#2d7a2d")
                fig.add_hline(y=70, line_dash="dot", line_color="#a07000", line_width=1, annotation_text="C", annotation_font_color="#a07000")
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    yaxis=dict(range=[0, 110], showgrid=True, gridcolor="#e8e4de", ticksuffix="%"),
                    xaxis=dict(showgrid=False),
                    margin=dict(t=20, b=10, l=10, r=10),
                    font=dict(family="Instrument Sans"),
                    showlegend=False,
                    height=280,
                )
                st.plotly_chart(fig, use_container_width=True)

        # Points at stake chart
        st.markdown('<p class="section-title">Points at Stake (Unsubmitted)</p>', unsafe_allow_html=True)
        points_by_course = defaultdict(float)
        count_by_course = defaultdict(int)
        for a in all_assignments:
            if a['points']:
                points_by_course[a['course_short']] += a['points']
                count_by_course[a['course_short']] += 1

        if points_by_course:
            df_pts = pd.DataFrame({
                'Course': list(points_by_course.keys()),
                'Points': list(points_by_course.values()),
                'Count': [count_by_course[k] for k in points_by_course.keys()]
            })
            color_map = {c['short']: c['color'] for c in courses_data}
            fig2 = px.treemap(
                df_pts, path=['Course'], values='Points',
                color='Course',
                color_discrete_map=color_map,
                custom_data=['Count']
            )
            fig2.update_traces(
                texttemplate="<b>%{label}</b><br>%{value:.0f} pts<br>%{customdata[0]} assignments",
                textfont=dict(family="Syne", size=14),
                marker_line_width=2,
                marker_line_color="#f7f4ef",
            )
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=10, b=10, l=10, r=10),
                height=220,
            )
            st.plotly_chart(fig2, use_container_width=True)

# ══ Tab 3: Urgency ════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<p class="section-title">Assignment Timeline</p>', unsafe_allow_html=True)

    dated = [a for a in all_assignments if a['due_date'] is not None]
    if dated:
        df_time = pd.DataFrame(dated)
        df_time['due_str'] = df_time['due_date'].apply(lambda d: d.strftime("%b %d") if d else "")
        df_time['urgency_color'] = df_time['days_until'].apply(
            lambda d: "#c0390f" if d is not None and d <= 3 else ("#a07000" if d is not None and d <= 7 else "#2d7a2d")
        )

        fig3 = go.Figure()
        for i, a in enumerate(dated[:20]):  # show up to 20
            days = a['days_until'] if a['days_until'] is not None else 30
            clamp = max(0, min(days, 30))
            color = "#c0390f" if days <= 3 else ("#a07000" if days <= 7 else "#2d7a2d")
            fig3.add_trace(go.Bar(
                x=[clamp],
                y=[a['name'][:35] + ("…" if len(a['name']) > 35 else "")],
                orientation='h',
                marker_color=color,
                marker_line_width=0,
                text=f"  {days}d" if days >= 0 else "  Overdue",
                textposition='outside',
                textfont=dict(size=11, color="#666"),
                showlegend=False,
                hovertemplate=f"<b>{a['name']}</b><br>{a['course']}<br>Due: {a['due_date'].strftime('%b %d %I:%M %p') if a['due_date'] else 'N/A'}<extra></extra>"
            ))

        fig3.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(title="Days Until Due", showgrid=True, gridcolor="#e8e4de", range=[0, 35]),
            yaxis=dict(showgrid=False, autorange="reversed"),
            margin=dict(t=10, b=30, l=10, r=60),
            height=max(300, len(dated[:20]) * 38),
            font=dict(family="Instrument Sans"),
            bargap=0.35,
        )
        st.plotly_chart(fig3, use_container_width=True)

    # Urgency breakdown donuts
    st.markdown('<p class="section-title">Urgency Breakdown</p>', unsafe_allow_html=True)
    u1, u2, u3 = st.columns(3)
    buckets = {
        "🔴 Overdue": sum(1 for a in all_assignments if a['days_until'] is not None and a['days_until'] < 0),
        "🟡 This Week": sum(1 for a in all_assignments if a['days_until'] is not None and 0 <= a['days_until'] <= 7),
        "🟢 Later": sum(1 for a in all_assignments if a['days_until'] is None or a['days_until'] > 7),
    }
    bucket_colors = ["#c0390f", "#a07000", "#2d7a2d"]

    for col, (label, count), color in zip([u1, u2, u3], buckets.items(), bucket_colors):
        with col:
            st.markdown(f"""
            <div class="metric-card" style="text-align:center;">
              <div style="font-size:1.5rem;">{label.split()[0]}</div>
              <div style="font-family:'Syne',sans-serif;font-size:2rem;font-weight:800;color:{color}">{count}</div>
              <div style="font-size:0.78rem;color:#999;">{label.split(None,1)[1]}</div>
            </div>
            """, unsafe_allow_html=True)
