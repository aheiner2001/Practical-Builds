import streamlit as st
from supabase import create_client, Client

st.set_page_config(page_title="Dixit Image Gallery", layout="wide", page_icon="🖼️")

# --- CONNECTION ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception:
    st.error("Check your .streamlit/secrets.toml for SUPABASE_URL and SUPABASE_KEY!")
    st.stop()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel+Decorative:wght@700&family=Nunito:wght@400;700&display=swap');

html, body, [class*="css"] { font-family: 'Nunito', sans-serif; }

[data-testid="stAppViewContainer"] {
    background: linear-gradient(160deg, #1a3545 0%, #28536b 40%, #1e3d50 100%) !important;
    min-height: 100vh;
}
[data-testid="stHeader"] { background: transparent !important; }

h1 {
    font-family: 'Cinzel Decorative', cursive !important;
    color: #f6f0ed !important;
    text-shadow: 0 1px 4px rgba(0,0,0,0.4);
}
p, span, [data-testid="stMarkdownContainer"] p {
    color: #f0e8e4 !important;
}
.stButton > button {
    background: linear-gradient(135deg, #28536b, #1e3d50) !important;
    color: #f6f0ed !important;
    border: 1px solid rgba(126,168,190,0.55) !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #3a6d8a, #28536b) !important;
}
.img-card {
    border: 2px solid rgba(126,168,190,0.3);
    border-radius: 12px;
    overflow: hidden;
    transition: border-color 0.2s;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 style="text-align:center;font-size:2rem;margin-bottom:4px;">🖼️ Dixit Image Gallery</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center;color:rgba(232,168,158,0.8);letter-spacing:4px;font-size:0.75rem;margin-bottom:24px;">ALL CARDS IN THE POOL</p>', unsafe_allow_html=True)

# --- LOAD IMAGES ---
@st.cache_data(ttl=30)
def load_images():
    res = supabase.table("dixit_pool").select("url").execute()
    return [r["url"] for r in res.data if r.get("url")]

col1, col2 = st.columns([3, 1])
with col2:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

images = load_images()

with col1:
    st.markdown(
        f'<p style="color:#c8bfba;font-size:0.88rem;margin-bottom:16px;">'
        f'<b style="color:#f0e8e4;">{len(images)}</b> cards in the pool</p>',
        unsafe_allow_html=True
    )

if not images:
    st.markdown(
        '<div style="text-align:center;padding:60px 0;color:#c8bfba;font-size:1.1rem;">'
        '🌙 No images yet — upload some cards to get started!</div>',
        unsafe_allow_html=True
    )
else:
    COLS = 5
    rows = [images[i:i+COLS] for i in range(0, len(images), COLS)]
    for row in rows:
        cols = st.columns(COLS)
        for j, img_url in enumerate(row):
            with cols[j]:
                st.markdown('<div class="img-card">', unsafe_allow_html=True)
                st.image(img_url, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
        # Fill empty slots in last row
        for j in range(len(row), COLS):
            cols[j].empty()
