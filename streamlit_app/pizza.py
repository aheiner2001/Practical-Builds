import streamlit as st
import google.generativeai as genai
from pathlib import Path

# Configure Gemini API
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]  # Add this to your secrets
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize Gemini model
model = genai.GenerativeModel('gemini-pro')

def init_chat():
    # Initialize chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "🍕 Hi! I'm your Pizza Assistant! Ask me anything about:\n"
                "- Ferment time / fridge storage\n"
                "- Rest before baking\n"
                "- Bake / cook time\n"
                "- Type of cheese\n"
                "- How long to knead dough\n"
                "- Cold water tips\n"
                "- Any other pizza-making questions!"
            }
        ]

def get_gemini_response(prompt, chat_history):
    # Convert chat history to Gemini format
    messages = [{"role": msg["role"], "parts": [msg["content"]]} for msg in chat_history]
    messages.append({"role": "user", "parts": [prompt]})

    # Get response from Gemini
    response = model.generate_content([msg["parts"][0] for msg in messages])
    return response.text

def main():
    st.set_page_config(page_title="Pizza Cheat Sheet", layout="wide")

    # Initialize chat
    init_chat()

    # Header
    st.title("🍕 Pizza Cheat Sheet")
    st.caption("By Remy")

    # Chat interface
    with st.container():
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        # Chat input
        if prompt := st.chat_input("Ask about pizza making..."):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Display user message
            with st.chat_message("user"):
                st.write(prompt)

            # Get and display assistant response
            with st.chat_message("assistant"):
                response = get_gemini_response(prompt, st.session_state.messages[:-1])
                st.write(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

    # Main content
    st.divider()

    # Links section
    col1, col2 = st.columns(2)
    with col1:
        st.link_button("My dough stats", "https://aheiner2001.github.io/Machine-Learning/")
    with col2:
        st.link_button("Add your dough stats", "https://docs.google.com/forms/d/e/1FAIpQLSfpMG-FE4jG8ExdcKj43wn1D63XO7GMSmVn7CGQh6pfiUz5Ug/viewform")

    # Basic Dough Process
    st.header("Basic Dough Process")
    st.markdown("""
    1. Make dough using [Dough Calculator](https://doughguy.co/pages/dough)
    2. Cold ferment in the fridge for 2-5 days (3 days is optimal)
    3. Remove dough and let sit at room temperature for **3-4 hours** before baking
    4. Follow dough stretching tutorial
    5. Cook pizza for:
        - 6-7 minutes (Pizza Steel)
        - 7-8 minutes (Pizza Stone/Upside-down Baking Sheet)
    """)

    # Equipment and Sauce sections in columns
    col1, col2 = st.columns(2)

    with col1:
        st.header("Equipment")
        st.markdown("""
        Ranked by crust quality:
        1. **Pizza Steel**
        2. **Pizza Stone**
        3. **Baking Sheet** (Upside down)

        **Preheat:** 550°F for 40-45 minutes
        """)

    with col2:
        st.header("Pizza Sauce")
        st.subheader("NY-Style Sauce (Recommended)")
        st.markdown("""
        - 28 oz can crushed tomatoes
        - 2 tsp salt
        - 1 tsp sugar
        - 2 tsp oregano
        - 3 tsp basil
        """)

    st.divider()
    st.caption("© 2025 Aaron Heiner")

if __name__ == "__main__":
    main()
