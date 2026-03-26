import streamlit as st
import google.generativeai as genai

# 1. SETUP & CONFIG
st.set_page_config(page_title="Pizza Cheat Sheet", layout="wide")

# Configure Gemini API
# Make sure "GOOGLE_API_KEY" is set in your Streamlit Secrets
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
except Exception as e:
    st.error("API Key not found. Please add GOOGLE_API_KEY to your Streamlit Secrets.")

# 2. INJECT YOUR CUSTOM CSS (Fonts, Colors, and Cards)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Inter:wght@400;500;600&display=swap');

    :root {
      --bg: #fdfcf9;
      --card-bg: #ffffff;
      --ink: #2d2d2d;
      --muted: #5a5a5a;
      --accent: #c4a484;
      --border: #ece8e1;
      --link: #8b4513;
    }

    .stApp {
        background-color: var(--bg);
        color: var(--ink);
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3 {
        font-family: 'Playfair Display', serif !important;
        color: var(--ink) !important;
    }

    .pizza-header {
        text-align: center;
        padding: 3rem 0 1rem 0;
    }

    .pizza-card {
        background: var(--card-bg);
        padding: 2rem;
        border: 1px solid var(--border);
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.02);
        margin-bottom: 2rem;
        color: var(--ink);
    }

    .callout {
      margin: 1.5rem 0;
      padding: 1rem 1.5rem;
      background: #f9f6f1;
      border-left: 4px solid var(--accent);
      font-style: italic;
      color: var(--muted);
    }

    .jump-link {
      display: inline-block;
      margin-bottom: 1rem;
      font-weight: 600;
      color: var(--link) !important;
      text-decoration: underline;
      cursor: pointer;
    }

    /* Fixed height for chat messages to match your UI */
    .stChatMessage {
        background-color: #ece8e1 !important;
        border-radius: 15px !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. CHAT LOGIC
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "🍕 Hi! I'm your Pizza Assistant! Ask me anything about dough, cheese, or bake times."
    }]

def get_gemini_response(prompt, chat_history):
    # Pass the context to Gemini
    response = model.generate_content(f"Answer this pizza question: {prompt}")
    return response.text

# 4. PAGE CONTENT
st.markdown('<div class="pizza-header"><span style="color:var(--accent); letter-spacing:0.3em; font-size:0.8rem; text-transform:uppercase;">Remy\'s</span><h1>Pizza Cheat Sheet</h1></div>', unsafe_allow_html=True)

# Navigation / Links
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    st.markdown('<a href="https://aheiner2001.github.io/Machine-Learning/" target="_blank" class="jump-link">My dough stats</a>', unsafe_allow_html=True)
with col2:
    st.markdown('<a href="https://docs.google.com/forms/d/e/1FAIpQLSfpMG-FE4jG8ExdcKj43wn1D63XO7GMSmVn7CGQh6pfiUz5Ug/viewform" target="_blank" class="jump-link">Add your dough stats</a>', unsafe_allow_html=True)
with col3:
    # This is the JUMP LINK fix
    st.markdown('<a href="#tutorial-section" class="jump-link">Jump to tutorial videos ↓</a>', unsafe_allow_html=True)

# Chat Interface
with st.container():
    st.write("---")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask about pizza making..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            response = get_gemini_response(prompt, st.session_state.messages[:-1])
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
    st.write("---")

# Content Sections
st.markdown("""
<div class="pizza-card">
  <h2>Basic Dough Process</h2>
  <ol>
    <li>Make dough using <b><a href="https://doughguy.co/pages/dough" target="_blank">Dough Calculator</a></b>.</li>
    <li>Cold ferment in the fridge for 2-5 days (3 days is optimal).</li>
    <li>Remove dough and let sit at room temperature for <b>3-4 hours</b> before baking.</li>
    <li>Follow dough stretching tutorial below.</li>
    <li>Cook pizza for 6-7 min (Steel) or 7-8 min (Stone).</li>
  </ol>
  <div class="callout">
    <strong>Pro Tip:</strong> Room-temperature dough stretches significantly easier and prevents "snap-back" while shaping.
  </div>
</div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns(2)

with col_left:
    st.markdown("""
    <div class="pizza-card">
      <h2>Equipment</h2>
      <p>Ranked by crust quality:</p>
      <ol>
        <li><strong>Pizza Steel</strong></li>
        <li><strong>Pizza Stone</strong></li>
        <li><strong>Baking Sheet</strong> (Upside down)</li>
      </ol>
      <p><strong>Preheat:</strong> 550°F for 40-45 minutes.</p>
    </div>
    """, unsafe_allow_html=True)

with col_right:
    st.markdown("""
    <div class="pizza-card">
      <h2>Pizza Sauce</h2>
      <h3>NY-Style Sauce (Recommended)</h3>
      <ul>
        <li>28 oz can crushed tomatoes</li>
        <li>2 tsp salt, 1 tsp sugar</li>
        <li>2 tsp oregano, 3 tsp basil</li>
      </ul>
      <p><small><em>Note: Blend briefly for a smooth texture.</em></small></p>
    </div>
    """, unsafe_allow_html=True)

# Target for the Jump Link
st.markdown('<div id="tutorial-section"></div>', unsafe_allow_html=True)
st.header("Tutorial Videos")

v1, v2 = st.columns(2)
with v1:
    st.video("https://www.instagram.com/reel/DM3K4oouFIp/")
with v2:
    st.video("https://www.instagram.com/reel/DM5g1kbuvZG/")

st.markdown('<footer style="text-align:center; padding:4rem; color:var(--muted); font-size:0.8rem;">© 2025 Aaron Heiner</footer>', unsafe_allow_html=True)
