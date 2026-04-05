
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Page Config ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Realms of Legend",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="auto",
)

# ── Global Styling ─────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');

  /* Base theme */
  .stApp {
    background-color: #0a0a1a;
    color: #e8e0d0;
  }

  /* Headings */
  h1, h2, h3 {
    font-family: 'Cinzel', serif !important;
    color: #FFD700 !important;
    text-shadow: 0 0 20px rgba(255, 215, 0, 0.3);
  }

  h4, h5, h6 {
    font-family: 'Cinzel', serif !important;
    color: #c0a060 !important;
  }

  /* Body text */
  p, li, label, .stMarkdown {
    font-family: 'Crimson Text', serif !important;
    font-size: 1.05rem;
    color: #e8e0d0;
  }

  /* Cards / Containers */
  .stContainer, [data-testid="stVerticalBlock"] {
    background: transparent;
  }

  /* Buttons */
  .stButton > button {
    font-family: 'Cinzel', serif !important;
    font-size: 0.85rem;
    letter-spacing: 0.05em;
    border: 1px solid #4a3a1a;
    background: #1a1a2e;
    color: #e8d5a0;
    transition: all 0.2s ease;
  }

  .stButton > button:hover {
    border-color: #FFD700;
    color: #FFD700;
    box-shadow: 0 0 12px rgba(255, 215, 0, 0.2);
    transform: translateY(-1px);
  }

  .stButton > button[kind="primary"] {
    background: #2a1a00;
    border-color: #FFD700;
    color: #FFD700;
  }

  .stButton > button[kind="primary"]:hover {
    background: #3a2a00;
    box-shadow: 0 0 20px rgba(255, 215, 0, 0.4);
  }

  /* Text inputs */
  .stTextInput > div > div > input,
  .stTextArea > div > div > textarea {
    background: #0f0f23 !important;
    color: #e8e0d0 !important;
    border: 1px solid #3a3a5a !important;
    font-family: 'Crimson Text', serif !important;
    font-size: 1rem !important;
  }

  /* Selectbox */
  .stSelectbox > div > div {
    background: #0f0f23 !important;
    color: #e8e0d0 !important;
    border-color: #3a3a5a !important;
  }

  /* Progress bars */
  .stProgress > div > div > div {
    background: linear-gradient(90deg, #8B0000, #cc2200);
  }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background: #0a0a14 !important;
    border-right: 1px solid #2a2a3a;
  }

  [data-testid="stSidebar"] h3 {
    font-size: 1rem !important;
  }

  /* Tabs */
  .stTabs [data-baseweb="tab"] {
    font-family: 'Cinzel', serif !important;
    color: #888 !important;
    font-size: 0.85rem;
  }

  .stTabs [aria-selected="true"] {
    color: #FFD700 !important;
    border-bottom-color: #FFD700 !important;
  }

  /* Divider */
  hr {
    border-color: #2a2a3a;
  }

  /* Expander */
  .streamlit-expanderHeader {
    font-family: 'Cinzel', serif !important;
    color: #c0a060 !important;
  }

  /* Metrics */
  [data-testid="stMetricValue"] {
    color: #FFD700 !important;
    font-family: 'Cinzel', serif !important;
  }

  /* Info/Success/Error boxes */
  .stAlert {
    background: #0f0f23 !important;
    border-left: 4px solid #444;
  }

  /* Scrollbar */
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: #0a0a14; }
  ::-webkit-scrollbar-thumb { background: #3a3a5a; border-radius: 3px; }
  ::-webkit-scrollbar-thumb:hover { background: #FFD700; }
</style>
""", unsafe_allow_html=True)

# ── Session State Init ────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state["page"] = "home"
if "game_mode" not in st.session_state:
    st.session_state["game_mode"] = "story"

# ── Router ────────────────────────────────────────────────────────────
page = st.session_state.get("page", "home")

if page == "home":
    from pages.home import render_home
    render_home()

elif page == "campaign_create":
    from pages.campaign_create import render_campaign_create
    render_campaign_create()

elif page == "character_select":
    from pages.character_select import render_character_select
    render_character_select()

elif page == "lobby":
    from pages.lobby import render_lobby
    render_lobby()

elif page == "game":
    from pages.game_page import render_game
    render_game()

else:
    st.error(f"Unknown page: {page}")
    if st.button("Go Home"):
        st.session_state["page"] = "home"
        st.rerun()
