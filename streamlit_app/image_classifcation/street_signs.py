import streamlit as st
import numpy as np
from PIL import Image
import os

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Road Sign Classifier",
    page_icon="🚦",
    layout="centered",
)

# ─── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500&display=swap');

  html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0d0d0d;
    color: #f0ece4;
  }

  h1, h2, h3 { font-family: 'Bebas Neue', sans-serif; letter-spacing: 2px; }

  .hero-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 4rem;
    line-height: 1;
    letter-spacing: 4px;
    color: #f0ece4;
    margin: 0;
  }
  .hero-sub {
    font-size: 0.95rem;
    color: #888;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 0.25rem;
  }
  .accent-bar {
    width: 60px; height: 4px;
    background: #e84c3d;
    margin: 1rem 0 2rem 0;
    border-radius: 2px;
  }
  section[data-testid="stFileUploadDropzone"] {
    background: #1a1a1a !important;
    border: 2px dashed #333 !important;
    border-radius: 12px !important;
    padding: 2rem !important;
    transition: border-color 0.2s;
  }
  section[data-testid="stFileUploadDropzone"]:hover {
    border-color: #e84c3d !important;
  }
  .result-card {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-left: 4px solid #e84c3d;
    border-radius: 12px;
    padding: 1.5rem 2rem;
    margin-top: 1.5rem;
  }
  .result-label {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2rem;
    letter-spacing: 2px;
    color: #f0ece4;
    margin: 0;
  }
  .result-confidence {
    font-size: 0.85rem;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 0.25rem;
  }
  .top-prediction {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.4rem 0;
    border-bottom: 1px solid #222;
    font-size: 0.85rem;
  }
  .top-prediction:last-child { border-bottom: none; }
  .pill {
    display: inline-block;
    background: #e84c3d22;
    color: #e84c3d;
    border: 1px solid #e84c3d55;
    border-radius: 20px;
    padding: 2px 12px;
    font-size: 0.75rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    font-weight: 500;
  }
  .stButton > button {
    background: #e84c3d; color: white; border: none;
    border-radius: 8px; font-family: 'DM Sans', sans-serif;
    font-weight: 500; letter-spacing: 1px;
    padding: 0.5rem 2rem; transition: opacity 0.2s;
  }
  .stButton > button:hover { opacity: 0.85; }
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 3rem; max-width: 720px; }
</style>
""", unsafe_allow_html=True)

# ─── Class Labels ───────────────────────────────────────────────────────────────
TARGET_NAMES = [
    'Speed 20', 'Speed 30', 'Speed 50', 'Speed 60', 'Speed 70',
    'Speed 80', 'Speed Limit Ends', 'Speed 100', 'Speed 120', 'Overtaking Prohibited',
    'Overtaking Prohibited (Trucks)', 'Priority', 'Priority Road Ahead', 'Yield', 'STOP',
    'Entry Forbidden', 'Trucks Forbidden', 'No Entry (One-Way)', 'General Danger (!)', 'Left Curve Ahead',
    'Right Curve Ahead', 'Double Curve', 'Poor Surface Ahead', 'Slippery Surface Ahead', 'Road Narrows Right',
    'Roadwork Ahead', 'Traffic Light Ahead', 'Warning: Pedestrians', 'Warning: Children', 'Warning: Bikes',
    'Ice / Snow', 'Deer Crossing', 'End Previous Limitation', 'Turn Right (Mandatory)', 'Turn Left (Mandatory)',
    'Ahead Only', 'Straight or Right', 'Straight or Left', 'Pass Right', 'Pass Left',
    'Roundabout', 'End Overtaking Prohibition', 'End Overtaking Prohibition (Trucks)'
]

IMAGE_SIZE = (100, 100)

# ─── Lazy Model Loading ─────────────────────────────────────────────────────────
@st.cache_resource
def load_model():
    model_path = os.path.join(os.path.dirname(__file__), "road_sign_model.h5")
```

`__file__` always points to where the script itself is, so this will correctly look for `road_sign_model.h5` **in the same folder as `street_signs.py`** regardless of what directory Streamlit runs from.

Your folder should look like:
```
streamlit_app/
└── image_classifcation/
    ├── street_signs.py
    ├── road_sign_model.h5   ← same folder
    └── requirements.txt
    if not os.path.exists(model_path):
        return None, "no_file"
    try:
        import tensorflow as tf
        model = tf.keras.models.load_model(model_path)
        return model, "loaded"
    except ImportError:
        return None, "no_tf"
    except Exception as e:
        return None, f"error: {e}"

def preprocess_image(pil_img):
    img = pil_img.convert("RGB").resize(IMAGE_SIZE)
    arr = np.array(img, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)

def predict(model, pil_img):
    arr = preprocess_image(pil_img)
    probs = model.predict(arr, verbose=0)[0]
    return probs

# ─── Hero ───────────────────────────────────────────────────────────────────────
st.markdown('<p class="hero-title">Road Sign<br>Classifier</p>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">CNN · 43 Classes · German Traffic Signs</p>', unsafe_allow_html=True)
st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)

# ─── Model Status ───────────────────────────────────────────────────────────────
model, status = load_model()

if status == "loaded":
    st.markdown('<span class="pill">✓ Model Loaded</span>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
elif status == "no_file":
    st.warning(
        "⚠️ No model file found. Save your trained model as `road_sign_model.h5` "
        "and place it in the same directory as this app."
    )
elif status == "no_tf":
    st.error(
        "❌ TensorFlow is not installed in this environment. "
        "Add `tensorflow` to your `requirements.txt`."
    )
else:
    st.error(f"❌ Failed to load model: {status}")

# ─── Upload ─────────────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "Drop a road sign image here, or click to browse",
    type=["jpg", "jpeg", "png", "bmp", "webp"],
    label_visibility="collapsed",
)

if uploaded_file:
    pil_img = Image.open(uploaded_file)
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.image(pil_img, caption="Uploaded image", use_container_width=True)

    with col2:
        if model is None:
            st.error("No model loaded — cannot classify.")
        else:
            with st.spinner("Classifying…"):
                probabilities = predict(model, pil_img)

            top_idx = int(np.argmax(probabilities))
            top_conf = float(probabilities[top_idx])
            top_label = TARGET_NAMES[top_idx]

            st.markdown(f"""
            <div class="result-card">
              <p class="result-label">{top_label}</p>
              <p class="result-confidence">Confidence: {top_conf:.1%}</p>
              <div style="background:#2a2a2a;border-radius:4px;height:8px;margin-top:1rem;">
                <div style="width:{top_conf*100:.1f}%;background:#e84c3d;height:8px;border-radius:4px;"></div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<br>**Top 5 predictions**", unsafe_allow_html=True)
            top5_idx = np.argsort(probabilities)[::-1][:5]
            for rank, idx in enumerate(top5_idx):
                label = TARGET_NAMES[idx]
                conf = float(probabilities[idx])
                bar_color = "#e84c3d" if rank == 0 else "#444"
                st.markdown(f"""
                <div class="top-prediction">
                  <span>{label}</span>
                  <span style="color:#aaa;font-variant-numeric:tabular-nums">{conf:.1%}</span>
                </div>
                <div style="background:#2a2a2a;border-radius:3px;height:4px;margin-bottom:4px;">
                  <div style="width:{conf*100:.1f}%;background:{bar_color};height:4px;border-radius:3px;"></div>
                </div>
                """, unsafe_allow_html=True)

# ─── How to save ────────────────────────────────────────────────────────────────
with st.expander("💾  How to save your trained model from Colab"):
    st.code("""
# After training in Colab, add this line:
model.save('road_sign_model.h5')

# Then download it:
from google.colab import files
files.download('road_sign_model.h5')

# Place road_sign_model.h5 in the same folder as street_signs.py
""", language="python")

# ─── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("""
<hr style="border:none;border-top:1px solid #222;margin-top:3rem;">
<p style="color:#444;font-size:0.75rem;text-align:center;letter-spacing:1px;">
  CSE 450 · Module 5 · German Traffic Sign Recognition Benchmark
</p>
""", unsafe_allow_html=True)
