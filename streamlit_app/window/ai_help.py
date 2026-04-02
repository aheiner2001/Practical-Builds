import streamlit as st
from google import genai
from PIL import Image
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="My-T-Brite AI Assistant", page_icon="🪟")

# Accessing the secret from Streamlit Cloud
# Make sure the key in your Secrets dashboard is named: GEMINI_API_KEY
API_KEY = st.secrets.get("GEMINI_API_KEY")

if not API_KEY:
    st.error("Missing API Key! Go to Settings > Secrets in Streamlit Cloud and add: GEMINI_API_KEY = 'your_key_here'")
    st.stop()

# Initialize the new Google GenAI client
client = genai.Client(api_key=API_KEY)

# --- SYSTEM INSTRUCTIONS ---
SYSTEM_PROMPT = """
You are the official AI assistant for My-T-Brite, a professional window washing company. 

CORE COMPANY STANDARDS:
1. 7-Day Rain Guarantee: If it rains within 7 days, we touch up affected windows for free.
2. Pricing Units: "Per Pane" does NOT mean "Per Window." A single window frame may contain multiple panes. Explain this clearly.
3. Gutter Pricing: Quoted per foot.
4. Minimum Job Totals: SE Idaho: $160 | Victor, Jackson, Driggs, Swan Valley, Irwin: $250.
5. Timing: Most residential jobs take 1-2 hours.
6. Water Quality: We use pure water (water-fed pole). It dries crystal clear without spotting.
7. Technical Issues: Use 'hard water removal' for stains. If foggy between glass, explain it's a 'gas leak/seal failure' (needs replacement, not cleaning).
8. window soap soltuopom to clean with nonscratch abrasive, squee off for a perfect finish

PRICING (Internal):
- SE Idaho: Interior $3-4/pane, Exterior $4/pane, French $1/pane, New Constr. $7/pane, Gutters $2-2.50/ft, Blinds $25, Screens $3.
- Resort Areas (Victor/Jackson/etc): Interior $7/pane ($6 Victor/Driggs), Exterior $7/pane, French $1.25/pane, New Constr. $13-15/pane, Gutters $4-5/ft, Blinds $30, Screens $5.
- Pressure Washing: SE Idaho $299-$499. Victor/Jackson: "Talk to Jeff."
don't give information unless they ask. be prompt and clear. 
when it seems like the converstion is done, ask for review. "https://share.google/HaJYJTKZ2LIqom1Up".


"""

# --- UI SETUP ---
st.title("🪟 My-T-Brite AI")
st.caption("Estimates & Support")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

with st.sidebar:
    st.header("Job Photos")
    uploaded_file = st.file_uploader("Upload photos for estimate", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        st.image(uploaded_file, use_container_width=True)
    if st.button("Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

# Display History
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- CHAT LOGIC ---
if prompt := st.chat_input("Ask about an estimate or window issue..."):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        content_parts = [SYSTEM_PROMPT]
        
        if uploaded_file:
            # Convert uploaded file to PIL image for the new SDK
            img = Image.open(uploaded_file)
            content_parts.append(img)
            content_parts.append(f"User Question: {prompt}")
        else:
            history_str = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_history[-3:]])
            content_parts.append(f"History: {history_str}\nUser: {prompt}")

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=content_parts
            )
            st.markdown(response.text)
            st.session_state.chat_history.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Error: {e}")
