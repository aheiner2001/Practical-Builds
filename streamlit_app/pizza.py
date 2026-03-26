import streamlit as st
import google.generativeai as genai

# 1. SETUP & CONFIG
st.set_page_config(page_title="Remy's Pizza Cheat Sheet", layout="wide", page_icon="🍕")

# Configure Gemini API
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
    # Using the current stable flash model
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("API Key not found. Please add GOOGLE_API_KEY to your Streamlit Secrets.")

# 2. CUSTOM CSS (The Visual Magic)
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
      --chat-user: #f4eee7;
      --chat-ai: #ffffff;
    }

    .stApp {
        background-color: var(--bg);
        color: var(--ink);
        font-family: 'Inter', sans-serif;
    }

    /* Header Styling */
    .pizza-header {
        text-align: center;
        padding: 2rem 0 1rem 0;
    }

    h1, h2, h3 {
        font-family: 'Playfair Display', serif !important;
        color: var(--ink) !important;
    }

    /* Card Styling */
    .pizza-card {
        background: var(--card-bg);
        padding: 1.8rem;
        border: 1px solid var(--border);
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        margin-bottom: 1.5rem;
    }

    .callout {
      margin: 1rem 0;
      padding: 1rem;
      background: #f9f6f1;
      border-left: 4px solid var(--accent);
      font-style: italic;
      color: var(--muted);
    }

    /* Chat Styling */
    [data-testid="stChatMessage"] {
        border: 1px solid var(--border);
        border-radius: 15px;
        padding: 1rem;
        margin-bottom: 0.5rem;
    }

    /* Lightly tint user messages */
    [data-testid="stChatMessageContent"]:has(div:contains("user")) {
        background-color: var(--chat-user);
    }

    /* Buttons & Links */
    .stButton>button {
        border-radius: 20px;
        border: 1px solid var(--accent);
        background-color: transparent;
        color: var(--ink);
    }
    
    .stButton>button:hover {
        background-color: var(--accent);
        color: white;
    }

</style>
""", unsafe_allow_html=True)

# 3. CHAT LOGIC & SESSION STATE
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "🍕 Ciao! I'm Remy's Pizza Bot. Need help with your dough hydration or sauce seasoning?"
    }]

def get_gemini_response(prompt):
    # System context ensures the AI stays on topic and follows your personality requirements
    system_context = (
        "You are an expert New York Style Pizza Assistant. "
        "Keep your answers helpful, concise, and focused on pizza making. "
        "Context: The user is looking at Remy's Pizza Cheat Sheet. "
        "Respond warmly but quickly."
    )
    
    try:
        # Combining history for context-aware chat
        chat_session = model.start_chat(history=[])
        full_query = f"{system_context}\n\nUser Question: {prompt}"
        response = model.generate_content(full_query)
        return response.text
    except Exception as e:
        return "I think the oven's out of wood! (Error connecting to Gemini API)."

# 4. PAGE LAYOUT
st.markdown('<div class="pizza-header"><span style="color:var(--accent); letter-spacing:0.3em; font-size:0.8rem; text-transform:uppercase;">Remy\'s</span><h1>Pizza Cheat Sheet</h1></div>', unsafe_allow_html=True)

# Navigation Row
nav_col1, nav_col2, nav_col3 = st.columns(3)
with nav_col1:
    st.link_button("📊 My Dough Stats", "https://aheiner2001.github.io/Machine-Learning/", use_container_width=True)
with nav_col2:
    st.link_button("✍️ Add Dough Stats", "https://docs.google.com/forms/...", use_container_width=True)
with nav_col3:
    st.link_button("🎥 Video Tutorials", "#tutorial-section", use_container_width=True)

st.write("---")

# 5. CHAT INTERFACE
# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("Ask about pizza..."):
    # User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Assistant Response
    with st.chat_message("assistant"):
        with st.spinner("Proofing the response..."):
            response = get_gemini_response(prompt)
            st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

st.write("---")

# 6. INFORMATION CARDS
col_main, col_side = st.columns([2, 1])

with col_main:
    st.markdown("""
    <div class="pizza-card">
      <h2>Basic Dough Process</h2>
      <ol>
        <li>Calculate ingredients using a dough tool.</li>
        <li>Cold ferment in the fridge for <b>2-5 days</b> (3 days is the sweet spot).</li>
        <li>Remove and sit at room temp for <b>3-4 hours</b> before stretching.</li>
        <li>Bake at 550°F until the crust is charred and cheese is bubbly.</li>
      </ol>
      <div class="callout">
        <strong>Pro Tip:</strong> Never use a rolling pin! It kills the bubbles in the crust. Use your knuckles to stretch.
      </div>
    </div>
    """, unsafe_allow_html=True)

with col_side:
    st.markdown("""
    <div class="pizza-card">
      <h3>Equipment Rank</h3>
      <ol>
        <li><b>Steel:</b> Best conductivity.</li>
        <li><b>Stone:</b> Classic & reliable.</li>
        <li><b>Baking Sheet:</b> For beginners.</li>
      </ol>
      <p><small>Preheat for 45+ mins!</small></p>
    </div>
    """, unsafe_allow_html=True)

# 7. TUTORIALS
st.markdown('<div id="tutorial-section"></div>', unsafe_allow_html=True)
st.header("Tutorial Videos")
v1, v2 = st.columns(2)
with v1:
    st.markdown(f'<iframe src="https://www.instagram.com/reel/DM3K4oouFIp/embed/" width="100%" height="480" frameborder="0" scrolling="no" allowtransparency="true"></iframe>', unsafe_allow_html=True)
with v2:
    st.markdown(f'<iframe src="https://www.instagram.com/reel/DM5g1kbuvZG/embed/" width="100%" height="480" frameborder="0" scrolling="no" allowtransparency="true"></iframe>', unsafe_allow_html=True)

st.markdown('<footer style="text-align:center; padding:4rem; color:var(--muted); font-size:0.8rem;">© 2026 Aaron Heiner</footer>', unsafe_allow_html=True)
