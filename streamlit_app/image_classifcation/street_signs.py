import streamlit as st
import numpy as np
from PIL import Image
import tensorflow as tf
import os
import urllib.request

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

  h1, h2, h3 {
    font-family: 'Bebas Neue', sans-serif;
    letter-spacing: 2px;
  }

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
    width: 60px;
    height: 4px;
    background: #e84c3d;
    margin: 1rem 0 2rem 0;
    border-radius: 2px;
  }

  /* Upload zone */
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

  /* Result card */
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

  .conf-bar-bg {
    background: #2a2a2a;
    border-radius: 4px;
    height: 8px;
    margin-top: 1rem;
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

  /* Streamlit overrides */
  .stButton > button {
    background: #e84c3d;
    color: white;
    border: none;
    border-radius: 8px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
    letter-spacing: 1px;
    padding: 0.5rem 2rem;
    transition: opacity 0.2s;
  }
  .stButton > button:hover { opacity: 0.85; }

  /* Hide streamlit chrome */
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

# ─── Model Loading ──────────────────────────────────────────────────────────────
@st.cache_resource
def load_model():
    """Load a trained model if available, otherwise build an untrained placeholder."""
    model_path = "road_sign_model.h5"

    if os.path.exists(model_path):
        return tf.keras.models.load_model(model_path), True

    # Build the same architecture from the notebook so weights can be loaded later
    model = tf.keras.models.Sequential([
        tf.keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=(100, 100, 3)),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.MaxPooling2D((2, 2)),

        tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.MaxPooling2D((2, 2)),

        tf.keras.layers.Conv2D(128, (3, 3), activation='relu'),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.MaxPooling2D((2, 2)),

        tf.keras.layers.Conv2D(256, (3, 3), activation='relu'),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.Flatten(),

        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dropout(0.5),
        tf.keras.layers.Dense(43, activation='softmax'),
    ])
    model.compile(
        optimizer='adam',
        loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=False),
        metrics=['accuracy']
    )
    return model, False


def preprocess_image(pil_img: Image.Image) -> np.ndarray:
    """Resize, normalize and expand dims for model input."""
    img = pil_img.convert("RGB").resize(IMAGE_SIZE)
    arr = np.array(img, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)


# ─── Hero Header ───────────────────────────────────────────────────────────────
st.markdown('<p class="hero-title">Road Sign<br>Classifier</p>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">CNN · 43 Classes · German Traffic Signs</p>', unsafe_allow_html=True)
st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)

# ─── Model Status ──────────────────────────────────────────────────────────────
model, model_loaded = load_model()

if not model_loaded:
    st.warning(
        "⚠️  No trained model found (`road_sign_model.h5`). "
        "Train your model in the Colab notebook, save it with `model.save('road_sign_model.h5')`, "
        "then place it in the same directory as this app. "
        "The architecture is ready — predictions below will be random until weights are loaded."
    )
else:
    st.markdown('<span class="pill">✓ Model Loaded</span>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# ─── Upload ────────────────────────────────────────────────────────────────────
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
        with st.spinner("Classifying…"):
            input_arr = preprocess_image(pil_img)
            probabilities = model.predict(input_arr, verbose=0)[0]  # shape (43,)

        top_idx = int(np.argmax(probabilities))
        top_conf = float(probabilities[top_idx])
        top_label = TARGET_NAMES[top_idx]

        st.markdown(f"""
        <div class="result-card">
          <p class="result-label">{top_label}</p>
          <p class="result-confidence">Confidence: {top_conf:.1%}</p>
          <div class="conf-bar-bg">
            <div style="width:{top_conf*100:.1f}%;background:#e84c3d;height:8px;border-radius:4px;"></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Top-5
        st.markdown("<br>**Top 5 predictions**", unsafe_allow_html=True)
        top5_idx = np.argsort(probabilities)[::-1][:5]
        for rank, idx in enumerate(top5_idx):
            label = TARGET_NAMES[idx]
            conf = probabilities[idx]
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

# ─── How to Save Your Model ────────────────────────────────────────────────────
with st.expander("💾  How to save your trained model from Colab"):
    st.code("""
# After training in Colab, add this line:
model.save('road_sign_model.h5')

# Then download it (Colab file browser, or):
from google.colab import files
files.download('road_sign_model.h5')

# Place road_sign_model.h5 in the same folder as app.py and restart.
""", language="python")

# ─── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<hr style="border:none;border-top:1px solid #222;margin-top:3rem;">
<p style="color:#444;font-size:0.75rem;text-align:center;letter-spacing:1px;">
  CSE 450 · Module 5 · German Traffic Sign Recognition Benchmark
</p>
""", unsafe_allow_html=True)
