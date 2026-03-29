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
    initial_sidebar_state="expanded",
)

# ─── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

  html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background: #0f0f0f;
    color: #f0ece4;
  }

  h1, h2, h3 { font-family: 'DM Serif Display', serif; }

  /* ─── Sidebar ────────────────────────────────────────────────────────────── */
  section[data-testid="stSidebar"] {
    background: #161616 !important;
    border-right: 1px solid #2a2a2a !important;
    min-width: 280px !important;
    padding-top: 0 !important;
  }
  section[data-testid="stSidebar"] > div {
    padding-top: 1.5rem !important;
  }
  /* Ensure sidebar toggle button is always visible */
  button[data-testid="collapsedControl"],
  [data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    background: #1e1e1e !important;
    border: 1px solid #333 !important;
    border-radius: 8px !important;
    color: #f0ece4 !important;
  }
  button[kind="header"] {
    color: #f0ece4 !important;
  }

  /* ─── Main content ───────────────────────────────────────────────────────── */
  .block-container {
    padding: 2rem 2.5rem 3rem 2.5rem !important;
    max-width: 1280px !important;
  }

  /* ─── Typography ─────────────────────────────────────────────────────────── */
  .brand {
    font-family: 'DM Serif Display', serif;
    font-size: 2rem;
    font-weight: 400;
    color: #f0ece4;
    line-height: 1;
    letter-spacing: -0.5px;
  }
  .brand em { color: #ff6b35; font-style: italic; }

  .eyebrow {
    font-size: 0.68rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #666;
    margin-bottom: 0.3rem;
  }

  /* ─── Cards ──────────────────────────────────────────────────────────────── */
  .metric-card {
    background: #1a1a1a;
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    border: 1px solid #2a2a2a;
  }
  .metric-label {
    font-size: 0.68rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #555;
    margin-bottom: 0.5rem;
  }
  .metric-value {
    font-family: 'DM Serif Display', serif;
    font-size: 2.8rem;
    font-weight: 400;
    line-height: 1;
  }
  .metric-sub {
    font-size: 0.75rem;
    color: #555;
    margin-top: 0.3rem;
  }

  /* ─── Assignment rows ────────────────────────────────────────────────────── */
  .assignment-row {
    background: #1a1a1a;
    border-radius: 10px;
    padding: 0.9rem 1.1rem;
    margin-bottom: 0.5rem;
    border: 1px solid #242424;
    display: flex;
    align-items: center;
    gap: 1rem;
    transition: border-color 0.15s, background 0.15s;
  }
  .assignment-row:hover {
    border-color: #3a3a3a;
    background: #1e1e1e;
  }

  /* ─── Badges ─────────────────────────────────────────────────────────────── */
  .due-badge {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    padding: 4px 10px;
    border-radius: 6px;
    white-space: nowrap;
  }
  .badge-urgent { background: #3d1a14; color: #ff6b35; border: 1px solid #5c2518; }
  .badge-soon   { background: #2d2510; color: #f0c040; border: 1px solid #4a3c18; }
  .badge-later  { background: #0f2a1a; color: #4caf7d; border: 1px solid #1a4430; }
  .badge-none   { background: #222; color: #666; border: 1px solid #333; }

  .course-chip {
    display: inline-block;
    font-size: 0.68rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: 600;
  }

  /* ─── Section headers ────────────────────────────────────────────────────── */
  .section-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.15rem;
    font-weight: 400;
    letter-spacing: -0.3px;
    margin: 1.5rem 0 0.9rem 0;
    color: #f0ece4;
  }

  /* ─── Sidebar elements ───────────────────────────────────────────────────── */
  section[data-testid="stSidebar"] label {
    color: #aaa !important;
    font-size: 0.85rem !important;
  }
  section[data-testid="stSidebar"] .stCheckbox label {
    color: #ccc !important;
    font-size: 0.82rem !important;
  }
  section[data-testid="stSidebar"] .stCheckbox > label > div {
    background: #222 !important;
    border-color: #3a3a3a !important;
  }

  /* ─── Streamlit UI overrides ─────────────────────────────────────────────── */
  .stTextInput input {
    background: #1a1a1a !important;
    border: 1px solid #333 !important;
    border-radius: 8px !important;
    color: #f0ece4 !important;
    font-family: 'DM Sans', sans-serif !important;
  }
  .stTextInput input:focus {
    border-color: #ff6b35 !important;
    box-shadow: 0 0 0 2px rgba(255,107,53,0.15) !important;
  }
  .stSelectbox > div > div {
    background: #1a1a1a !important;
    border: 1px solid #333 !important;
    border-radius: 8px !important;
    color: #f0ece4 !important;
  }
  .stButton > button {
    background: #ff6b35 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    letter-spacing: 0.5px !important;
    padding: 0.55rem 1.5rem !important;
    transition: opacity 0.15s !important;
  }
  .stButton > button:hover { opacity: 0.85 !important; }
  .stButton > button:active { opacity: 0.75 !important; }

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: transparent;
    border-bottom: 1px solid #2a2a2a;
    margin-bottom: 1rem;
  }
  .stTabs [data-baseweb="tab"] {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    color: #555 !important;
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    padding: 0.6rem 1.2rem !important;
    margin-bottom: -1px !important;
  }
  .stTabs [aria-selected="true"] {
    color: #ff6b35 !important;
    border-bottom-color: #ff6b35 !important;
  }

  /* Divider */
  hr { border-color: #2a2a2a !important; }

  /* Spinner */
  .stSpinner > div { border-top-color: #ff6b35 !important; }

  /* Alert / info boxes */
  .stAlert { background: #1a1a1a !important; border-color: #333 !important; color: #aaa !important; }

  #MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

COURSE_COLORS = ["#ff6b35", "#4da6ff", "#4caf7d", "#f0c040", "#c77dff", "#4dd9c0"]

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
    if score is None: return "#555"
    if score >= 90: return "#4caf7d"
    if score >= 80: return "#89c97a"
    if score >= 70: return "#f0c040"
    if score >= 60: return "#ff8c42"
    return "#ff4444"

# ─── Fetch courses ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=600, show_spinner=False)
def fetch_all_courses(api_key, api_url):
    canvas = Canvas(api_url, api_key)
    user = canvas.get_current_user()
    courses = user.get_courses(enrollment_state='active', include=['term'])
    result = []
    for c in courses:
        try:
            result.append({"id": c.id, "name": c.name})
        except:
            pass
    result.sort(key=lambda x: x['name'])
    return result

# ─── Sidebar ──────────────────────────────────────────────────────────────────
api_key = st.secrets.get("CANVAS_API_KEY", "")
api_url = st.secrets.get("CANVAS_URL", "https://byui.instructure.com/")

with st.sidebar:
    st.markdown('<div class="brand">canvas<em>.</em></div>', unsafe_allow_html=True)
    st.markdown('<div class="eyebrow" style="margin-bottom:1.5rem;">Student Dashboard</div>', unsafe_allow_html=True)

    if not api_key:
        st.error("Add `CANVAS_API_KEY` to your Streamlit secrets.")
        st.stop()

    st.markdown('<p style="font-size:0.72rem;color:#4caf7d;margin-bottom:1.2rem;letter-spacing:1px;">🔒 API KEY LOADED</p>', unsafe_allow_html=True)

    with st.spinner("Loading courses..."):
        try:
            all_courses = fetch_all_courses(api_key, api_url)
        except Exception as e:
            st.error(f"Cannot connect to Canvas: {e}")
            st.stop()

    st.markdown('<div class="eyebrow" style="margin-bottom:0.6rem;">Select Courses</div>', unsafe_allow_html=True)

    # Select All toggle
    select_all = st.checkbox("Select all", key="select_all_courses")

    selected_ids = []
    for c in all_courses:
        checked = st.checkbox(c['name'], value=select_all, key=f"course_{c['id']}")
        if checked:
            selected_ids.append(str(c['id']))

    st.markdown("---")
    load_btn = st.button("Load Dashboard", use_container_width=True)

# ─── Landing ──────────────────────────────────────────────────────────────────
if not load_btn or not selected_ids:
    st.markdown('<div class="brand" style="font-size:3.5rem;margin-bottom:0.5rem;">canvas<em>.</em></div>', unsafe_allow_html=True)
    if not selected_ids:
        st.markdown('<p style="font-size:1rem;color:#555;max-width:460px;line-height:1.7;">Select your courses in the sidebar, then click <b style="color:#f0ece4;">Load Dashboard</b> to get started.</p>', unsafe_allow_html=True)
    else:
        st.markdown(f'<p style="font-size:1rem;color:#555;max-width:460px;line-height:1.7;"><b style="color:#ff6b35;">{len(selected_ids)}</b> course(s) selected. Click <b style="color:#f0ece4;">Load Dashboard</b>.</p>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    for col, icon, title, desc in [
        (c1, "📅", "Due Date View", "Everything sorted by deadline"),
        (c2, "📊", "Grade Charts", "Visual breakdown of your standing"),
        (c3, "🎯", "Goal Tracker", "What you need to hit 90%"),
    ]:
        with col:
            st.markdown(f"""
            <div class="metric-card">
              <div style="font-size:1.6rem;margin-bottom:0.7rem;">{icon}</div>
              <div style="font-family:'DM Serif Display',serif;font-size:1rem;margin-bottom:0.3rem;">{title}</div>
              <div style="font-size:0.8rem;color:#555;line-height:1.5;">{desc}</div>
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

            enrollment = None
            try:
                enrollments = list(course.get_enrollments(user_id=user.id, type=['StudentEnrollment']))
                if enrollments:
                    enrollment = enrollments[0]
            except:
                pass

            grade = None
            points_earned = None
            total_points = None
            if enrollment and hasattr(enrollment, 'grades'):
                grade = enrollment.grades.get('current_score')
                points_earned = enrollment.grades.get('current_points')
                total_points = (enrollment.grades.get('total_points_possible')
                                or enrollment.grades.get('final_points'))

            courses_data.append({
                "id": cid.strip(),
                "name": course.name,
                "short": course.name.split()[0],
                "color": color,
                "grade": grade,
                "points_earned": points_earned,
                "total_points": total_points,
            })

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

    DT_MAX = datetime.max.replace(tzinfo=timezone.utc)
    all_assignments.sort(key=lambda x: (x['due_date'] is None, x['due_date'] or DT_MAX))
    return user, courses_data, all_assignments

with st.spinner("Fetching your Canvas data..."):
    try:
        user, courses_data, all_assignments = load_canvas_data(api_key, api_url, tuple(selected_ids))
    except Exception as e:
        st.error(f"❌ Could not connect to Canvas: {e}")
        st.stop()

# ─── Header ────────────────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    first_name = user.name.split()[0] if hasattr(user, 'name') else "there"
    st.markdown(f'<div class="brand" style="font-size:3rem;">Hey, <em>{first_name}</em></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="eyebrow" style="margin-top:0.3rem;margin-bottom:0.5rem;">{datetime.now().strftime("%A, %B %d · %Y")}</div>', unsafe_allow_html=True)

# ─── Metric Cards ──────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
m1, m2, m3, m4 = st.columns(4)

overdue  = sum(1 for a in all_assignments if a['days_until'] is not None and a['days_until'] < 0)
due_soon = sum(1 for a in all_assignments if a['days_until'] is not None and 0 <= a['days_until'] <= 3)
grades   = [c['grade'] for c in courses_data if c['grade'] is not None]
avg_grade = (sum(grades) / len(grades)) if grades else None

for col, label, value, sub, accent in [
    (m1, "Unsubmitted", str(len(all_assignments)), "total assignments", "#f0ece4"),
    (m2, "Overdue",     str(overdue),              "need attention",    "#ff6b35"),
    (m3, "Due in 3 Days", str(due_soon),           "coming up fast",    "#f0c040"),
    (m4, "Avg Grade",   f"{avg_grade:.1f}%" if avg_grade else "—", "across courses", "#4caf7d"),
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
tab1, tab2, tab3, tab4 = st.tabs(["📅  Assignments", "📊  Grades", "🔥  Urgency", "🎯  Goal Tracker"])

# ══ Tab 1: Assignments ════════════════════════════════════════════════════════
with tab1:
    if not all_assignments:
        st.success("🎉 No unsubmitted assignments found!")
    else:
        filter_col1, filter_col2, filter_col3 = st.columns([3, 2, 1])
        with filter_col1:
            search = st.text_input(
                "Search", placeholder="🔍  Filter by name...",
                label_visibility="collapsed", key="assign_search"
            )
        with filter_col2:
            course_options = ["All courses"] + [c['name'] for c in courses_data]
            course_filter = st.selectbox(
                "Course", course_options,
                label_visibility="collapsed", key="assign_course_filter"
            )
        with filter_col3:
            urgency_filter = st.selectbox(
                "Urgency", ["All", "Overdue", "This Week", "Later"],
                label_visibility="collapsed", key="assign_urgency_filter"
            )

        # Apply filters
        filtered = list(all_assignments)

        if search.strip():
            filtered = [a for a in filtered if search.strip().lower() in a['name'].lower()]

        if course_filter != "All courses":
            filtered = [a for a in filtered if a['course'] == course_filter]

        if urgency_filter == "Overdue":
            filtered = [a for a in filtered if a['days_until'] is not None and a['days_until'] < 0]
        elif urgency_filter == "This Week":
            filtered = [a for a in filtered if a['days_until'] is not None and 0 <= a['days_until'] <= 7]
        elif urgency_filter == "Later":
            filtered = [a for a in filtered if a['days_until'] is None or a['days_until'] > 7]

        st.markdown(f'<p style="font-size:0.75rem;color:#444;margin:0.6rem 0 0.8rem;letter-spacing:1px;text-transform:uppercase;">{len(filtered)} assignment{"s" if len(filtered) != 1 else ""}</p>', unsafe_allow_html=True)

        for a in filtered:
            badge_class, badge_text = urgency_badge(a['days_until'])
            due_str = a['due_date'].strftime("%b %d, %I:%M %p") if a['due_date'] else "No due date"
            pts = f"{int(a['points'])} pts" if a['points'] else ""

            st.markdown(f"""
            <div class="assignment-row">
              <div style="width:3px;height:42px;border-radius:2px;background:{a['color']};flex-shrink:0;"></div>
              <div style="flex:1;min-width:0;">
                <div style="font-weight:500;font-size:0.9rem;
                     white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#f0ece4;">{a['name']}</div>
                <div style="font-size:0.75rem;color:#555;margin-top:3px;">
                  <span class="course-chip" style="background:{a['color']}22;color:{a['color']};border:1px solid {a['color']}44;">{a['course_short']}</span>
                  &nbsp;&nbsp;{due_str}{('&nbsp;·&nbsp;' + pts) if pts else ''}
                </div>
              </div>
              <span class="due-badge {badge_class}">{badge_text}</span>
            </div>
            """, unsafe_allow_html=True)

# ══ Tab 2: Grades ═════════════════════════════════════════════════════════════
with tab2:
    graded_courses = [c for c in courses_data if c['grade'] is not None]
    if not graded_courses:
        st.info("No grade data available yet.")
    else:
        g1, g2 = st.columns([1, 1])

        with g1:
            st.markdown('<p class="section-title">Current Grades</p>', unsafe_allow_html=True)
            for c in graded_courses:
                grade = c['grade']
                bar_color = get_grade_color(grade)
                st.markdown(f"""
                <div class="metric-card" style="margin-bottom:0.6rem;padding:1rem 1.2rem;">
                  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.6rem;">
                    <span style="font-size:0.88rem;font-weight:500;color:#ccc;">{c['name']}</span>
                    <span style="font-family:'DM Serif Display',serif;font-size:1.2rem;color:{bar_color}">{grade:.1f}%</span>
                  </div>
                  <div style="background:#242424;border-radius:3px;height:6px;">
                    <div style="width:{min(grade,100):.1f}%;background:{bar_color};height:6px;border-radius:3px;transition:width 0.6s;"></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

        with g2:
            st.markdown('<p class="section-title">Grade Overview</p>', unsafe_allow_html=True)
            names   = [c['name'] for c in graded_courses]
            vals    = [c['grade'] for c in graded_courses]
            colors  = [c['color'] for c in graded_courses]
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=names, y=vals,
                marker_color=colors,
                marker_line_width=0,
                text=[f"{v:.1f}%" for v in vals],
                textposition='outside',
                textfont=dict(family="DM Sans", size=12, color="#aaa"),
            ))
            fig.add_hline(y=90, line_dash="dot", line_color="#4caf7d", line_width=1,
                          annotation_text="90%", annotation_font_color="#4caf7d", annotation_font_size=11)
            fig.add_hline(y=70, line_dash="dot", line_color="#f0c040", line_width=1,
                          annotation_text="70%", annotation_font_color="#f0c040", annotation_font_size=11)
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(range=[0, 115], showgrid=True, gridcolor="#222",
                           ticksuffix="%", color="#555", tickfont=dict(size=11)),
                xaxis=dict(showgrid=False, color="#555", tickfont=dict(size=10)),
                margin=dict(t=20, b=10, l=10, r=10),
                font=dict(family="DM Sans"),
                showlegend=False,
                height=280,
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # Points at stake
        st.markdown('<p class="section-title">Points at Stake (Unsubmitted)</p>', unsafe_allow_html=True)
        points_by_course = defaultdict(float)
        count_by_course  = defaultdict(int)
        for a in all_assignments:
            if a['points']:
                points_by_course[a['course_short']] += a['points']
                count_by_course[a['course_short']]  += 1

        if points_by_course:
            df_pts = pd.DataFrame({
                'Course': list(points_by_course.keys()),
                'Points': list(points_by_course.values()),
                'Count':  [count_by_course[k] for k in points_by_course.keys()]
            })
            color_map = {c['short']: c['color'] for c in courses_data}
            fig2 = px.treemap(
                df_pts, path=['Course'], values='Points',
                color='Course', color_discrete_map=color_map,
                custom_data=['Count']
            )
            fig2.update_traces(
                texttemplate="<b>%{label}</b><br>%{value:.0f} pts<br>%{customdata[0]} items",
                textfont=dict(family="DM Sans", size=13),
                marker_line_width=3,
                marker_line_color="#0f0f0f",
            )
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=5, b=5, l=5, r=5),
                height=200,
            )
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        else:
            st.markdown('<p style="color:#444;font-size:0.85rem;">No point data available for unsubmitted assignments.</p>', unsafe_allow_html=True)

# ══ Tab 3: Urgency ════════════════════════════════════════════════════════════
with tab3:
    u1, u2, u3 = st.columns(3)
    buckets = {
        ("🔴", "Overdue",    "#ff6b35"): sum(1 for a in all_assignments if a['days_until'] is not None and a['days_until'] < 0),
        ("🟡", "This Week",  "#f0c040"): sum(1 for a in all_assignments if a['days_until'] is not None and 0 <= a['days_until'] <= 7),
        ("🟢", "Later",      "#4caf7d"): sum(1 for a in all_assignments if a['days_until'] is None or a['days_until'] > 7),
    }
    for col, ((emoji, label, color), count) in zip([u1, u2, u3], buckets.items()):
        with col:
            st.markdown(f"""
            <div class="metric-card" style="text-align:center;padding:1.6rem 1rem;">
              <div style="font-size:1.8rem;margin-bottom:0.4rem;">{emoji}</div>
              <div style="font-family:'DM Serif Display',serif;font-size:3rem;color:{color};line-height:1;">{count}</div>
              <div style="font-size:0.72rem;letter-spacing:2px;text-transform:uppercase;color:#555;margin-top:0.4rem;">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<p class="section-title">Assignment Timeline</p>', unsafe_allow_html=True)
    dated = [a for a in all_assignments if a['due_date'] is not None]
    if dated:
        fig3 = go.Figure()
        for a in dated[:20]:
            days  = a['days_until'] if a['days_until'] is not None else 30
            clamp = max(0, min(days, 30))
            color = "#ff6b35" if days <= 3 else ("#f0c040" if days <= 7 else "#4caf7d")
            label_text = "Overdue" if days < 0 else f"{days}d"
            fig3.add_trace(go.Bar(
                x=[clamp],
                y=[a['name'][:38] + ("…" if len(a['name']) > 38 else "")],
                orientation='h',
                marker_color=color,
                marker_line_width=0,
                text=f"  {label_text}",
                textposition='outside',
                textfont=dict(size=11, color="#666", family="DM Sans"),
                showlegend=False,
                hovertemplate=(
                    f"<b>{a['name']}</b><br>"
                    f"{a['course']}<br>"
                    f"Due: {a['due_date'].strftime('%b %d %I:%M %p') if a['due_date'] else 'N/A'}"
                    "<extra></extra>"
                )
            ))
        fig3.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(title="Days Until Due", showgrid=True, gridcolor="#1e1e1e",
                       range=[0, 35], color="#555", tickfont=dict(size=11)),
            yaxis=dict(showgrid=False, autorange="reversed", color="#ccc", tickfont=dict(size=11)),
            margin=dict(t=10, b=30, l=10, r=70),
            height=max(300, len(dated[:20]) * 38),
            font=dict(family="DM Sans"),
            bargap=0.38,
        )
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No dated assignments found.")

# ══ Tab 4: Goal Tracker ═══════════════════════════════════════════════════════
with tab4:
    TARGET = 90.0
    st.markdown('<p class="section-title">🎯 90% Goal Tracker</p>', unsafe_allow_html=True)
    st.markdown(
        '<p style="font-size:0.83rem;color:#555;margin-bottom:1.5rem;line-height:1.6;">'
        'See what average score you need on remaining work to hit 90% in each course.</p>',
        unsafe_allow_html=True
    )

    DT_MAX = datetime.max.replace(tzinfo=timezone.utc)

    for course in courses_data:
        current_grade = course.get('grade')
        points_earned = course.get('points_earned')
        total_points  = course.get('total_points')
        color         = course['color']

        course_assignments = [
            a for a in all_assignments
            if a['course'] == course['name'] and a['points'] and a['points'] > 0
        ]
        total_remaining_pts = sum(a['points'] for a in course_assignments)

        pct_needed    = None
        points_needed = None
        if (points_earned is not None and total_points is not None
                and total_points > 0 and total_remaining_pts > 0):
            new_possible  = total_points + total_remaining_pts
            points_needed = (TARGET / 100) * new_possible - points_earned
            pct_needed    = (points_needed / total_remaining_pts) * 100

        already_at_90 = current_grade is not None and current_grade >= TARGET
        impossible    = pct_needed is not None and pct_needed > 100

        grade_str = f"{current_grade:.1f}%" if current_grade is not None else "N/A"

        if already_at_90:
            status_html = '<span class="due-badge badge-later">✓ At 90%+</span>'
        elif impossible:
            status_html = '<span class="due-badge badge-urgent">⚠ Needs near-perfect</span>'
        elif pct_needed is not None:
            status_html = f'<span class="due-badge badge-soon">Need {pct_needed:.0f}% avg</span>'
        else:
            status_html = '<span class="due-badge badge-none">No data</span>'

        st.markdown(f"""
        <div style="background:#1a1a1a;border-radius:14px;padding:1.4rem 1.6rem;
                    border:1px solid #2a2a2a;border-left:3px solid {color};margin-bottom:1.2rem;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.9rem;">
            <div>
              <span style="font-family:'DM Serif Display',serif;font-size:1rem;color:#f0ece4;">{course['name']}</span>
              <span style="font-size:0.78rem;color:#555;margin-left:0.8rem;">Current: <b style="color:#aaa;">{grade_str}</b></span>
            </div>
            {status_html}
          </div>
        """, unsafe_allow_html=True)

        if already_at_90:
            st.markdown('<p style="color:#4caf7d;font-size:0.85rem;padding-bottom:0.3rem;">🎉 You\'re already at 90% or above!</p>', unsafe_allow_html=True)
        elif not course_assignments:
            st.markdown('<p style="color:#444;font-size:0.83rem;padding-bottom:0.3rem;">No unsubmitted assignments with point values found.</p>', unsafe_allow_html=True)
        else:
            if pct_needed is not None:
                clamped   = min(pct_needed, 100)
                bar_color = "#ff6b35" if pct_needed > 95 else ("#f0c040" if pct_needed > 75 else "#4caf7d")
                pts_str   = (f"Earn at least <b>{max(points_needed, 0):.1f}</b> of the <b>{total_remaining_pts:.0f}</b> remaining points."
                             if points_needed is not None else "")
                st.markdown(f"""
                <div style="margin-bottom:1rem;">
                  <div style="display:flex;justify-content:space-between;font-size:0.75rem;color:#555;margin-bottom:5px;">
                    <span style="letter-spacing:1px;text-transform:uppercase;">Required average on remaining</span>
                    <span style="font-weight:600;color:{bar_color}">{pct_needed:.1f}%</span>
                  </div>
                  <div style="background:#242424;border-radius:3px;height:8px;">
                    <div style="width:{clamped:.1f}%;background:{bar_color};height:8px;border-radius:3px;"></div>
                  </div>
                  <p style="font-size:0.78rem;color:#555;margin-top:0.5rem;">{pts_str}</p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('<p style="font-size:0.68rem;letter-spacing:2px;text-transform:uppercase;color:#444;margin-bottom:0.5rem;">Assignments to complete</p>', unsafe_allow_html=True)

            sorted_assignments = sorted(
                course_assignments,
                key=lambda x: (x['due_date'] is None, x['due_date'] or DT_MAX)
            )

            for a in sorted_assignments:
                badge_class, badge_text = urgency_badge(a['days_until'])
                due_str = a['due_date'].strftime("%b %d") if a['due_date'] else "No date"
                pts     = int(a['points'])
                pct_of  = (a['points'] / total_remaining_pts * 100) if total_remaining_pts > 0 else 0
                st.markdown(f"""
                <div class="assignment-row" style="margin-bottom:0.35rem;">
                  <div style="width:3px;height:36px;border-radius:2px;background:{color};flex-shrink:0;"></div>
                  <div style="flex:1;min-width:0;">
                    <div style="font-size:0.85rem;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#ccc;">{a['name']}</div>
                    <div style="font-size:0.73rem;color:#555;">Due {due_str} &nbsp;·&nbsp; <b style="color:#aaa;">{pts} pts</b> &nbsp;·&nbsp; {pct_of:.1f}% of remaining</div>
                  </div>
                  <span class="due-badge {badge_class}">{badge_text}</span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
