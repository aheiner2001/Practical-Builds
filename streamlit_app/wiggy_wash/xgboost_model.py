# Wiggy Wash Forecast Dashboard (Full Feature Version)
# Run: streamlit run wiggy_wash_app.py

import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
import re
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor

st.set_page_config(page_title="Wiggy Wash Forecast", layout="wide")

# -----------------------------
# HELPERS
# -----------------------------

def parse_hour(interval_str):
    try:
        parts = str(interval_str).strip().split(' - ')
        start_time = parts[0].strip()
        ampm = parts[1].strip().split()[-1]
        hour = int(start_time.split(':')[0])
        if ampm.lower() == 'pm' and hour != 12:
            hour += 12
        elif ampm.lower() == 'am' and hour == 12:
            hour = 0
        return hour
    except:
        return np.nan

# -----------------------------
# FEATURE ENGINEERING (CENTRALIZED)
# -----------------------------

def create_time_features(df):
    df['hour_of_day'] = df['time_interval'].apply(parse_hour)
    df['date'] = pd.to_datetime(df['day'], errors='coerce')
    df['hour_sin'] = np.sin(2*np.pi*df['hour_of_day']/24)
    df['hour_cos'] = np.cos(2*np.pi*df['hour_of_day']/24)
    df['day_num'] = df['date'].dt.dayofweek
    return df

# -----------------------------
# LOAD + TRAIN
# -----------------------------
@st.cache_data(show_spinner="Training model...")
def load_and_train():

    url = "https://raw.githubusercontent.com/aheiner2001/Machine-Learning/refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data.csv"

    df_raw = pd.read_csv(url, header=None)

    col_names = [
        'Time Interval', '# Cars (Total)', 'drop1', '$ Sales (Total)',
        '$ Sales (Total/Car)', 'drop2', '$ Sales (Base)', '# Cars (Extra)',
        '$ Sales (Extra)', '$ Sales (Ext/Car)', 'drop3', '% Cars (Extra)',
        '# Cars (Inv)', '$ Sales (Inv)'
    ]
    df_raw.columns = col_names

    date_pattern = r'\d{2}/\d{2}/\d{4}'
    df_raw['Date'] = df_raw['Time Interval'].apply(
        lambda x: x if re.match(date_pattern, str(x)) else None
    )
    df_raw['Date'] = df_raw['Date'].ffill()

    df = df_raw[df_raw['Time Interval'].str.contains('am|pm', case=False, na=False)].copy()
    df = df.drop(columns=[c for c in df.columns if 'drop' in c])

    numeric_cols = df.columns.drop(['Time Interval', 'Date'])
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

    df = df.rename(columns={
        'Time Interval': 'time_interval',
        '# Cars (Total)': 'cars_total',
        'Date': 'day'
    })

    # Feature engineering
    df = create_time_features(df)

    df['datetime'] = df['date'] + pd.to_timedelta(df['hour_of_day'], unit='h')
    df['car_count'] = df['cars_total']

    # ---------------- WEATHER (HISTORICAL) ----------------
    params = {
        'latitude': 40.1618,
        'longitude': -111.6348,
        'start_date': df['date'].min().strftime('%Y-%m-%d'),
        'end_date': df['date'].max().strftime('%Y-%m-%d'),
        'hourly': ['temperature_2m', 'precipitation', 'wind_speed_10m'],
        'timezone': 'America/Denver'
    }

    response = requests.get("https://archive-api.open-meteo.com/v1/archive", params=params)

    if response.status_code != 200:
        st.error("Weather API failed")
        st.stop()

    w = response.json()

    if "hourly" not in w:
        st.error("Weather API response missing hourly data")
        st.write(w)
        st.stop()

    weather = pd.DataFrame({
        'datetime': pd.to_datetime(w['hourly']['time']),
        'temp': w['hourly']['temperature_2m'],
        'precip': w['hourly']['precipitation'],
        'wind': w['hourly']['wind_speed_10m']
    })

    df = pd.merge(df, weather, on='datetime', how='left')

    # ---------------- FULL FEATURE SET ----------------
    feature_cols = [
        # original numeric business features
        '# Cars (Total)',
        '$ Sales (Total)',
        '$ Sales (Total/Car)',
        '$ Sales (Base)',
        '# Cars (Extra)',
        '$ Sales (Extra)',
        '$ Sales (Ext/Car)',
        '% Cars (Extra)',
        '# Cars (Inv)',
        '$ Sales (Inv)',

        # engineered features
        'hour_of_day',
        'hour_sin',
        'hour_cos',
        'day_num',

        # weather features
        'temp',
        'precip',
        'wind'
    ]

    df = df.dropna()

    X = df[feature_cols]
    y = np.log1p(df['car_count'])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    model = GradientBoostingRegressor()
    model.fit(X_train, y_train)

    return df, model, feature_cols

# -----------------------------
# FUTURE FORECAST
# -----------------------------
@st.cache_data(hash_funcs={GradientBoostingRegressor: lambda _: None}, show_spinner="Generating forecasts...")
def build_future_forecast(_model, feature_cols):

    params = {
        'latitude': 40.1618,
        'longitude': -111.6348,
        'hourly': ['temperature_2m','precipitation','wind_speed_10m'],
        'forecast_days': 14,
        'timezone': 'America/Denver'
    }

    response = requests.get("https://api.open-meteo.com/v1/forecast", params=params)

    if response.status_code != 200:
        st.error("Forecast API failed")
        st.stop()

    w = response.json()

    if "hourly" not in w:
        st.error("Invalid forecast response")
        st.write(w)
        st.stop()

    hourly = w["hourly"]

    weather = pd.DataFrame({
        'datetime': pd.to_datetime(hourly.get('time', [])),
        'temp': hourly.get('temperature_2m', []),
        'precip': hourly.get('precipitation', []),
        'wind': hourly.get('wind_speed_10m', [])
    })

    # Build additional required features
    weather['hour_of_day'] = weather['datetime'].dt.hour
    weather['date'] = weather['datetime'].dt.date
    weather['hour_sin'] = np.sin(2*np.pi*weather['hour_of_day']/24)
    weather['hour_cos'] = np.cos(2*np.pi*weather['hour_of_day']/24)
    weather['day_num'] = pd.to_datetime(weather['date']).dayofweek

    # Placeholder columns for non-weather numeric features (assume averages)
    for col in [c for c in feature_cols if c not in ['hour_of_day','hour_sin','hour_cos','day_num','temp','precip','wind']]:
        weather[col] = 0

    X_future = weather[feature_cols]

    preds = np.expm1(_model.predict(X_future))
    weather['predicted_cars'] = preds

    return weather

# -----------------------------
# LOAD MODEL
# -----------------------------
with st.spinner("Training model..."):
    df_hist, model, feature_cols = load_and_train()

forecast_df = build_future_forecast(model, feature_cols)

# -----------------------------
# UI
# -----------------------------

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Forecast Overview", "Day Breakdown"])

if page == "Forecast Overview":
    st.title("Next 14-Day Forecast")

    daily = forecast_df.groupby('date')['predicted_cars'].sum().reset_index()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily['date'], y=daily['predicted_cars'], mode='lines+markers'))

    fig.update_layout(title="Daily Predicted Traffic", height=400)

    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(daily)

elif page == "Day Breakdown":
    st.title("Hourly Breakdown")

    available_dates = sorted(forecast_df['date'].unique())

    selected_date = st.selectbox(
        "Select Date",
        available_dates,
        format_func=lambda d: pd.to_datetime(d).strftime("%A %b %d")
    )

    day_df = forecast_df[forecast_df['date'] == selected_date]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=day_df['hour_of_day'], y=day_df['predicted_cars']))

    fig.update_layout(title="Hourly Forecast", height=400)

    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(day_df)
