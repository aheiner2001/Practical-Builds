import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- CONFIGURATION ---
st.set_page_config(page_title="My-T-Brite AI Assistant", page_icon="🪟")

# Securely get your API Key (Set this in your environment or Streamlit secrets)
# For local testing, you can replace with st.sidebar.text_input("API Key", type="password")
API_KEY = st.secrets.get("GEMINI_API_KEY", "")

if not API_KEY:
    st.error("Please set the GEMINI_API_KEY in your secrets or environment.")
    st.stop()

genai.configure(api_key=API_KEY)

# --- SYSTEM INSTRUCTIONS ---
SYSTEM_PROMPT = """
You are the official AI assistant for My-T-Brite, a professional window washing company. 
Your goal is to assist both employees and customers with estimates, technical questions, and company standards.

CORE COMPANY STANDARDS:
1. 7-Day Rain Guarantee: If it rains within 7 days of service, we touch up affected windows for free.
2. Pricing Units: "Per Pane" does NOT mean "Per Window." A single window frame may contain multiple panes. Explain this clearly to customers.
3. Gutter Pricing: Quoted "per foot."
4. Minimum Job Totals: SE Idaho: $160 | Victor/Jackson/Driggs: $250.
5. Timing: Most residential jobs take 1-2 hours depending on the window count.
6. Water Quality: We use pure water (often via water-fed pole). If asked about spots, explain that the water is purified so windows dry crystal clear without spotting.
7. Technical Issues: 
   - Hard Water: We use specialized hard water removal techniques for stubborn stains.
   - Gas Leaks: If a window looks foggy between the glass, explain it is a "seal failure" or "gas leak" (argon/krypton escaping), which requires glass replacement, not just cleaning.

PRICING DATA (Internal Use Only - Use these to calculate totals):
- SE Idaho: Interior $3-4/pane, Exterior $4/pane, French Panes $1/pane, New Construction $7/pane, Gutters $2-2.50/ft, Blinds $25, Screens $3.
- Victor/Driggs/Jackson/Swan Valley: Interior $7/pane ($6 for Victor/Driggs), Exterior $7/pane, French Panes $1.25/pane, New Construction $13-15/pane, Gutters $4-5/ft, Blinds $30, Screens $5.
- Pressure Washing: SE Idaho $299-$499. For Victor/Jackson area, tell the user to "Talk to Jeff" for a custom quote.

INSTRUCTIONS FOR ESTIMATES:
- If a user uploads a photo, analyze the number of panes and window types visible to provide a rough estimate.
- Always remind the user that AI estimates are preliminary and subject to onsite verification.
"""

# --- UI SETUP ---
st.title("🪟 My-T-Brite AI Assistant")
st.caption("Estimates, Technical Support, and Company Standards")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- SIDEBAR: PHOTO UPLOAD ---
with st.sidebar:
    st.header("Estimate Tools")
    uploaded_file = st.file_uploader("Upload window/house photos for an estimate", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)
    
    if st.button("Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

# Display Chat History
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- CHAT LOGIC ---
if prompt := st.chat_input("How can I help with your windows today?"):
    # Add user message to history
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Response
    with st.chat_message("assistant"):
        model = genai.GenerativeModel('gemini-1.5-flash') # Using Flash for speed/cost
        
        content_parts = [SYSTEM_PROMPT]
        
        # Include image if uploaded
        if uploaded_file:
            img = Image.open(uploaded_file)
            content_parts.append(img)
            content_parts.append(f"Based on this image and the user's request: {prompt}, provide an estimate or answer.")
        else:
            # Include history for context
            history_context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_history[-5:]])
            content_parts.append(f"Context:\n{history_context}\nUser: {prompt}")

        try:
            response = model.generate_content(content_parts)
            full_response = response.text
            st.markdown(full_response)
            st.session_state.chat_history.append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"Error: {e}")
