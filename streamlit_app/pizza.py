import streamlit as st
import google.generativeai as genai

# 1. SETUP & CONFIG
st.set_page_config(page_title="Pizza Cheat Sheet", layout="wide")

# Configure Gemini API
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# 2. INJECT YOUR CUSTOM CSS
# We take the styles you provided and wrap them in a <style> tag
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

    /* Target the Streamlit main container to match your background */
    .stApp {
        background-color: var(--bg);
        color: var(--ink);
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3 {
        font-family: 'Playfair Display', serif !important;
        color: var(--ink);
    }

    .pizza-header {
        text-align: center;
        padding: 2rem 0;
    }

    .pizza-card {
        background: var(--card-bg);
        padding: 2rem;
        border: 1px solid var(--border);
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.02);
        margin-bottom: 2rem;
    }

    .callout {
      margin: 1rem 0;
      padding: 1.5rem;
      background: #f9f6f1;
      border-left: 3px solid var(--accent);
      font-style: italic;
    }

    .jump-link {
      display: inline-block;
      margin-bottom: 1rem;
      font-weight: 500;
      color: var(--link);
      text-decoration: underline;
    }
    
    /* Styling for the chat area to look like your mock */
    .stChatMessage {
        border-radius: 20px !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. CHAT LOGIC
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "🍕 Hi! I'm your Pizza Assistant! Ask me about ferment times, cheese, or baking!"
    }]

def get_gemini_response(prompt, chat_history):
    # Context-aware pizza prompt
    full_prompt = f"You are a pizza expert. Use the following history to answer: {chat_history}. Question: {prompt}"
    response = model.generate_content(full_prompt)
    return response.text

# 4. PAGE CONTENT
st.markdown('<div class="pizza-header"><span style="color:var(--accent); letter-spacing:0.3em; font-size:0.8rem; text-transform:uppercase;">Remy\'s</span><h1>Pizza Cheat Sheet</h1></div>', unsafe_allow_html=True)

# Links
col1, col2 = st.columns(2)
with col1:
    st.markdown('<a href="https://aheiner2001.github.io/Machine-Learning/" class="jump-link">My dough stats</a>', unsafe_allow_html=True)
with col2:
    st.markdown('<a href="https://docs.google.com/forms/d/e/1FAIpQLSfpMG-FE4jG8ExdcKj43wn1D63XO7GMSmVn7CGQh6pfiUz5Ug/viewform" class="jump-link">Add your dough stats</a>', unsafe_allow_html=True)

# Chat Interface
with st.expander("💬 Ask the Pizza Assistant", expanded=True):
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

# Recipe Sections
st.markdown("""
<div class="pizza-card">
  <h2>Basic Dough Process</h2>
  <ol>
    <li>Make dough using <b><a href="https://doughguy.co/pages/dough">Dough Calculator</a></b></li>
    <li>Cold ferment in the fridge for 2-5 days (3 is best).</li>
    <li>Remove and let sit at room temp for <b>3-4 hours</b>.</li>
    <li>Cook for 6-7 min (Steel) or 7-8 min (Stone).</li>
  </ol>
  <div class="callout">
    <b>Pro Tip:</b> Room-temperature dough stretches significantly easier and prevents "snap-back".
  </div>
</div>
""", unsafe_allow_html=True)

# Grid Layout for Equipment and Sauce
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("""
    <div class="pizza-card">
      <h2>Equipment</h2>
      <ol>
        <li><b>Pizza Steel</b></li>
        <li><b>Pizza Stone</b></li>
        <li><b>Baking Sheet</b> (Upside down)</li>
      </ol>
      <p>Preheat: 550°F for 45 minutes.</p>
    </div>
    """, unsafe_allow_html=True)

with col_right:
    st.markdown("""
    <div class="pizza-card">
      <h2>Pizza Sauce</h2>
      <h3>NY-Style</h3>
      <ul>
        <li>28 oz crushed tomatoes</li>
        <li>2 tsp salt, 1 tsp sugar</li>
        <li>2 tsp oregano, 3 tsp basil</li>
      </ul>
    </div>
    """, unsafe_allow_html=True)

# Instagram Embeds (Using Streamlit's native components for reliability)
st.header("Tutorial Videos")
v1, v2 = st.columns(2)
with v1:
    st.video("https://www.instagram.com/reel/DM3K4oouFIp/") # Part 1
with v2:
    st.video("https://www.instagram.com/reel/DM5g1kbuvZG/") # Part 2

st.markdown('<footer style="text-align:center; padding:2rem; color:var(--muted);">© 2025 Aaron Heiner</footer>', unsafe_allow_html=True)
