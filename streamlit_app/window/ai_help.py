import streamlit as st
from google import genai
from PIL import Image
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="My-T-Brite AI Assistant", page_icon="🪟")

# Securely get your API Key from Streamlit Secrets
API_KEY = st.secrets.get("GEMINI_API_KEY", "")

if not API_KEY:
    st.error("Please set the GEMINI_API_KEY in your Streamlit secrets.")
    st.stop()

# Initialize the new Google GenAI client
client = genai.Client(api_key=API_KEY)

# --- SYSTEM INSTRUCTIONS ---
SYSTEM_PROMPT = """
You are the official AI assistant for My-T-Brite, a professional window washing company. 
Your goal is to assist both employees and customers with estimates, technical questions, and company standards.

CORE COMPANY STANDARDS:
1. 7-Day Rain Guarantee: If it rains within 7 days of service, we touch up affected windows for free.
2. Pricing Units: "Per Pane" does NOT mean "Per Window." A single window frame may contain multiple panes. Explain this clearly to customers.
3. Gutter Pricing: Quoted "per foot."
4. Minimum Job Totals: SE Idaho: $160 | Victor, Jackson, Driggs, Swan Valley, and Irwin: $250.
5. Timing: Most residential jobs take 1-2 hours depending on the window count.
6. Water Quality: We use pure water (often via water-fed pole). If asked about spots, explain that the water is purified so windows dry crystal clear without spotting.
7. Technical Issues: 
   - Hard Water: We use specialized hard water removal for stubborn stains.
   - Gas Leaks: If a window looks foggy between the glass, explain it is a "seal failure" or "gas leak" (argon/krypton escaping), which requires glass replacement, not just cleaning.

PRICING DATA (Keep this internal - use to calculate totals for the user):
- SE Idaho: Interior $3-4/pane, Exterior $4/pane, French Panes $1/pane, New Construction $7/pane, Gutters $2-2.50/ft, Blinds $25, Screens $3.
- Victor/Driggs/Jackson/Swan Valley/Irwin: Interior $7/pane ($6 for Victor/Driggs), Exterior $7/pane, French Panes $1.25/pane, New Construction $13-15/pane, Gutters $4-5/ft, Blinds $30, Screens $5.
- Pressure Washing: SE Idaho $299-$499. For Victor/Jackson area, tell the user to "Talk to Jeff" for a custom quote.
"""

# --- UI SETUP ---
st.title("🪟 My-T-Brite AI Assistant")
st.caption("Official My-T-Brite Estimator & Technical Support")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- SIDEBAR: PHOTO UPLOAD ---
with st.sidebar:
    st.header("Job Photos")
    uploaded_file = st.file_uploader("Upload photos for an estimate", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        st.image(uploaded_file, caption="User Uploaded Image", use_container_width=True)
    
    if st.button("Clear Conversation"):
        st.session_state.chat_history = []
        st.rerun()

# Display Chat History
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- CHAT LOGIC ---
if prompt := st.chat_input("How can I help with your windows today?"):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Prepare the parts for the model
        content_parts = [SYSTEM_PROMPT]
        
        # Include image if uploaded
        if uploaded_file:
            img = Image.open(uploaded_file)
            content_parts.append(img)
            content_parts.append(f"User is providing this photo. User message: {prompt}")
        else:
            # Build context from recent history
            history_str = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_history[-5:]])
            content_parts.append(f"Context:\n{history_str}\nUser: {prompt}")

        try:
            # Use the new generate method
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=content_parts
            )
            
            full_response = response.text
            st.markdown(full_response)
            st.session_state.chat_history.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"Error communicating with AI: {e}")
