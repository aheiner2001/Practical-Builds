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
p, span, [data-testid="stMarkdownContainer"] p { color: #f0e8e4 !important; }
strong, b { color: #ffffff !important; }

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

/* Delete button — red tint */
.delete-btn > div > button {
    background: linear-gradient(135deg, rgba(180,60,60,0.55), rgba(140,30,30,0.65)) !important;
    border: 1px solid rgba(220,100,100,0.5) !important;
    color: #ffd0d0 !important;
    font-size: 0.78rem !important;
    padding: 4px 0 !important;
}
.delete-btn > div > button:hover {
    background: linear-gradient(135deg, rgba(200,70,70,0.75), rgba(160,40,40,0.85)) !important;
    border-color: rgba(240,120,120,0.7) !important;
}

/* Confirm yes button — bright red */
.confirm-yes > div > button {
    background: linear-gradient(135deg, #c0392b, #96281b) !important;
    border: none !important;
    color: #fff !important;
    font-weight: 800 !important;
}
.confirm-yes > div > button:hover {
    background: linear-gradient(135deg, #e74c3c, #c0392b) !important;
}

/* Cancel button — muted */
.confirm-no > div > button {
    background: rgba(126,168,190,0.15) !important;
    border: 1px solid rgba(126,168,190,0.4) !important;
    color: #c8e0f0 !important;
}

.img-card {
    border: 2px solid rgba(126,168,190,0.3);
    border-radius: 12px;
    overflow: hidden;
}
.img-card-pending {
    border: 2px solid rgba(220,100,100,0.7);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 0 16px rgba(200,60,60,0.35);
}
.confirm-box {
    background: linear-gradient(135deg, rgba(100,20,20,0.6), rgba(60,10,10,0.75));
    border: 1px solid rgba(220,100,100,0.5);
    border-radius: 10px;
    padding: 8px 6px 4px;
    margin-top: 4px;
    text-align: center;
}
.confirm-label {
    color: #ffc0c0 !important;
    font-size: 0.78rem !important;
    font-weight: 700 !important;
    margin-bottom: 6px !important;
}
[data-testid="stAlert"] p, [data-testid="stAlert"] div,
div[class*="stAlert"] p { color: #1a3545 !important; font-weight: 700 !important; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if "pending_delete" not in st.session_state:
    st.session_state.pending_delete = None  # stores the id awaiting confirmation

# --- LOAD IMAGES ---
@st.cache_data(ttl=30)
def load_images():
    res = supabase.table("dixit_pool").select("id, url").execute()
    return [(r["id"], r["url"]) for r in res.data if r.get("url")]

# --- HEADER ---
st.markdown('<h1 style="text-align:center;font-size:2rem;margin-bottom:4px;">🖼️ Dixit Image Gallery</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center;color:rgba(232,168,158,0.8);letter-spacing:4px;font-size:0.75rem;margin-bottom:24px;">ALL CARDS IN THE POOL</p>', unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])
with col2:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.session_state.pending_delete = None
        st.rerun()

images = load_images()  # list of (id, url)

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
        for j, (img_id, img_url) in enumerate(row):
            with cols[j]:
                is_pending = (st.session_state.pending_delete == img_id)

                card_class = "img-card-pending" if is_pending else "img-card"
                st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
                st.image(img_url, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

                if not is_pending:
                    # Normal — show remove button
                    st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
                    if st.button("🗑️ Remove", key=f"del_{img_id}", use_container_width=True):
                        st.session_state.pending_delete = img_id
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    # Confirmation state — card glows red
                    st.markdown(
                        '<div class="confirm-box">'
                        '<div class="confirm-label">⚠️ Delete this card?</div>'
                        '</div>',
                        unsafe_allow_html=True
                    )
                    yes_col, no_col = st.columns(2)
                    with yes_col:
                        st.markdown('<div class="confirm-yes">', unsafe_allow_html=True)
                        if st.button("✓ Yes", key=f"yes_{img_id}", use_container_width=True):
                            try:
                                supabase.table("dixit_pool").delete().eq("id", img_id).execute()
                                st.session_state.pending_delete = None
                                st.cache_data.clear()
                                st.success("Card removed.")
                            except Exception as e:
                                st.error(f"Failed: {e}")
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                    with no_col:
                        st.markdown('<div class="confirm-no">', unsafe_allow_html=True)
                        if st.button("✗ No", key=f"no_{img_id}", use_container_width=True):
                            st.session_state.pending_delete = None
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

        # Fill empty slots in last row
        for j in range(len(row), COLS):
            cols[j].empty()
