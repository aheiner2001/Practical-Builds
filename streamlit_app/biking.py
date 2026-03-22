import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Bike Rental Predictor", page_icon="🚲", layout="centered")
st.title("🚲 Bike Rental Demand Predictor")
st.write("Enter ride conditions below to get a predicted number of bike rentals.")

# ---------------------------------------------------
# Helper functions
# ---------------------------------------------------
def hour_bin(x):
    if x in [0, 1, 2, 3, 4, 5]:        return 0
    elif x in [7, 8]:                   return 1
    elif x in [11, 12, 13, 14, 15, 16]: return 2
    elif x in [17, 18, 19]:             return 3
    else:                               return 4

def temp_bin(x):
    if x < 0:          return 1
    elif 10 <= x < 36: return 2
    else:              return 3

def engineer_features(df):
    df = df.copy()
    df['dteday'] = pd.to_datetime(df['dteday'])
    df['dateTime'] = df['dteday'].apply(lambda x: x.toordinal()) * 24 + df['hr']
    df['daylight']   = np.sin(df['hr'] / 24 * np.pi * 2)
    df['month']      = df['dteday'].dt.month
    df['day']        = df['dteday'].dt.day
    df['month_sin']  = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos']  = np.cos(2 * np.pi * df['month'] / 12)
    df['day_sin']    = np.sin(2 * np.pi * df['day'] / 31)
    df['day_cos']    = np.cos(2 * np.pi * df['day'] / 31)
    df['hr_sin']     = np.sin(2 * np.pi * df['hr'] / 24)
    df['hr_cos']     = np.cos(2 * np.pi * df['hr'] / 24)
    df['possible_worker'] = np.where(
        (df['hr'] >= 7.5) & (df['hr'] <= 17.5) & (df['workingday'] == 1), 1, 0
    )
    b, c = 17.625, 243.04
    gamma = np.log(df['hum'] / 100 + 1e-9) + (b * df['temp_c']) / (c + df['temp_c'])
    df['dew_point']  = (c * gamma) / (b - gamma)
    df['hour_bin']   = df['hr'].apply(hour_bin)
    df['tempt_bin']  = df['temp_c'].apply(temp_bin)
    df['prime_conditions'] = (
        df['hour_bin'].isin([1, 2, 3]) & (df['tempt_bin'] == 2)
    ).astype(int)
    return df

FEATURE_COLS = [
    'dateTime', 'season', 'holiday', 'workingday', 'weathersit',
    'temp_c', 'feels_like_c', 'hum', 'daylight', 'windspeed',
    'month_sin', 'month_cos', 'day_sin', 'day_cos',
    'hr_sin', 'hr_cos', 'hour_bin', 'prime_conditions',
    'possible_worker', 'dew_point'
]

DATA_URL = "https://raw.githubusercontent.com/byui-cse/cse450-course/master/data/bikes.csv"

# ---------------------------------------------------
# Train model once (cached so it doesn't retrain on every click)
# ---------------------------------------------------
@st.cache_resource
def train_model():
    df = pd.read_csv(DATA_URL)
    df_eng = engineer_features(df)
    X = df_eng[FEATURE_COLS]
    y = df['casual'] + df['registered']
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=20)
    model = GradientBoostingRegressor(
        n_estimators=500, learning_rate=0.05, max_depth=6,
        min_samples_split=6, min_samples_leaf=3, subsample=0.8,
        max_features=0.8, random_state=42
    )
    model.fit(X_train, y_train)
    return model

with st.spinner("Training model on bike data... (only happens once)"):
    model = train_model()

st.success("Model ready!")
st.divider()

# ---------------------------------------------------
# User Inputs
# ---------------------------------------------------
st.subheader("Ride Conditions")

col1, col2 = st.columns(2)
with col1:
    date_input   = st.date_input("Date", value=pd.Timestamp("2012-06-15"))
    hr           = st.number_input("Hour of Day (0-23)", 0, 23, 8)
    temp_c       = st.number_input("Temperature (C)", -10.0, 45.0, 20.0, step=0.5)
    feels_like_c = st.number_input("Feels-Like Temp (C)", -10.0, 45.0, 18.0, step=0.5)
    hum          = st.number_input("Humidity (%)", 0, 100, 60)

with col2:
    windspeed  = st.number_input("Wind Speed (km/h)", 0.0, 70.0, 15.0, step=0.5)
    season     = st.selectbox("Season", [1, 2, 3, 4],
                              format_func=lambda x: {1:"Spring", 2:"Summer", 3:"Fall", 4:"Winter"}[x])
    weathersit = st.selectbox("Weather Situation", [1, 2, 3, 4],
                              format_func=lambda x: {
                                  1:"Clear / Few Clouds",
                                  2:"Mist / Cloudy",
                                  3:"Light Rain / Snow",
                                  4:"Heavy Rain / Ice"
                              }[x])
    workingday = st.selectbox("Working Day?", [0, 1], format_func=lambda x: "Yes" if x else "No")
    holiday    = st.selectbox("Holiday?",     [0, 1], format_func=lambda x: "Yes" if x else "No")

# ---------------------------------------------------
# Build input row and predict
# ---------------------------------------------------
if st.button("Predict Rentals", type="primary"):
    input_dict = {
        'dteday':       str(date_input),
        'hr':           hr,
        'temp_c':       temp_c,
        'feels_like_c': feels_like_c,
        'hum':          hum,
        'windspeed':    windspeed,
        'season':       season,
        'weathersit':   weathersit,
        'workingday':   workingday,
        'holiday':      holiday,
    }

    row     = pd.DataFrame([input_dict])
    row_eng = engineer_features(row)
    X_input = row_eng[FEATURE_COLS]

    prediction = max(0, round(model.predict(X_input)[0]))

    st.divider()
    st.subheader("Prediction")

    col3, col4, col5 = st.columns(3)
    col3.metric("Estimated Rentals", f"{prediction:,} bikes")
    col4.metric("Hour Category",
                {0:"Late Night", 1:"Morning Rush", 2:"Midday",
                 3:"Evening Rush", 4:"Off-Peak"}[hour_bin(hr)])
    col5.metric("Prime Conditions",
                "Yes" if (hour_bin(hr) in [1, 2, 3] and temp_bin(temp_c) == 2) else "No")

    if prediction > 400:
        st.success("High demand expected — make sure bikes are stocked!")
    elif prediction > 150:
        st.info("Moderate demand expected.")
    else:
        st.warning("Low demand expected.")
