import streamlit as st
import google.generativeai as genai

# 1. SETUP & CONFIG
st.set_page_config(page_title="Pizza Cheat Sheet", layout="wide")

# Configure Gemini API
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
    # FORCING THE FULL MODEL PATH TO FIX THE 404 ERROR
    model = genai.GenerativeModel(model_name='models/gemini-1.5-flash')
except Exception as e:
    st.error("Check your Streamlit Secrets for GOOGLE_API_KEY")

# 2. INJECT CUSTOM CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Inter:wght@400;500;600&display=swap');
    :root { --bg: #fdfcf9; --card-bg: #ffffff; --ink: #2d2d2d; --accent: #c4a484; --border: #ece8e1; --link: #8b4513; }
    .stApp { background-color: var(--bg); color: var(--ink); font-family: 'Inter', sans-serif; }
    h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: var(--ink) !important; }
    .pizza-header { text-align: center; padding: 2rem 0; }
    .pizza-card { background: var(--card-bg); padding: 1.5rem; border: 1px solid var(--border); border-radius: 8px; margin-bottom: 1.5rem; }
    .jump-link { font-weight: 600; color: var(--link) !important; text-decoration: underline; }
</style>
""", unsafe_allow_html=True)

# 3. CHAT LOGIC
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "🍕 Ask me anything about pizza!"}]

def get_gemini_response(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Model Error: {str(e)}"

# 4. PAGE HEADER
st.markdown('<div class="pizza-header"><span style="color:var(--accent); letter-spacing:0.3em; font-size:0.8rem; text-transform:uppercase;">Remy\'s</span><h1>Pizza Cheat Sheet</h1></div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1: st.markdown('<a href="https://aheiner2001.github.io/Machine-Learning/" target="_blank" class="jump-link">My dough stats</a>', unsafe_allow_html=True)
with col2: st.markdown('<a href="https://docs.google.com/forms/d/e/1FAIpQLSfpMG-FE4jG8ExdcKj43wn1D63XO7GMSmVn7CGQh6pfiUz5Ug/viewform" target="_blank" class="jump-link">Add your dough stats</a>', unsafe_allow_html=True)
with col3: st.markdown('<a href="#videos" class="jump-link">Jump to tutorial videos ↓</a>', unsafe_allow_html=True)

# 5. CHAT UI
st.write("---")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input("Ask about pizza..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    with st.chat_message("assistant"):
        res = get_gemini_response(prompt)
        st.markdown(res)
        st.session_state.messages.append({"role": "assistant", "content": res})
st.write("---")

# 6. TUTORIAL VIDEOS (IFRAME FIX)
st.markdown('<div id="videos"></div>', unsafe_allow_html=True)
st.header("Tutorial Videos")
v1, v2 = st.columns(2)
with v1:
    st.markdown('<iframe src="https://www.instagram.com/reel/DM3K4oouFIp/embed/" width="100%" height="480" frameborder="0" scrolling="no" style="border-radius:12px;"></iframe>', unsafe_allow_html=True)
with v2:
    st.markdown('<iframe src="https://www.instagram.com/reel/DM5g1kbuvZG/embed/" width="100%" height="480" frameborder="0" scrolling="no" style="border-radius:12px;"></iframe>', unsafe_allow_html=True)

st.markdown('<footer style="text-align:center; padding:2rem; color:grey; font-size:0.8rem;">© 2025 Aaron Heiner</footer>', unsafe_allow_html=True)
