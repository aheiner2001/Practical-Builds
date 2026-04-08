# wiggy_wash_app.py – Forecast Dashboard (FULL FEATURES + FUTURE PREDICTION)
# Run: streamlit run wiggy_wash_app.py

import streamlit as st
st.write("App starting...")

import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
import re
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Wiggy Wash Forecast",
    layout="wide"
)

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def parse_hour(interval_str):
    try:
        parts = str(interval_str).split(' - ')
        start_time = parts[0].strip()
        ampm = parts[1].strip().split()[-1]
        hour = int(start_time.split(':')[0])
        if ampm.lower() == 'pm' and hour != 12: hour += 12
        elif ampm.lower() == 'am' and hour == 12: hour = 0
        return hour
    except:
        return np.nan

# ─────────────────────────────────────────────────────────────────────────────
# DATA + TRAINING (UNCHANGED FEATURE ENGINEERING)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Training model...")

def load_and_train():

    def clean_and_tag_dates(url):
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

        df_clean = df_raw[df_raw['Time Interval'].str.contains('am|pm', case=False, na=False)].copy()
        df_clean = df_clean.drop(columns=[c for c in df_clean.columns if 'drop' in c])

        numeric_cols = df_clean.columns.drop(['Time Interval', 'Date'])
        for col in numeric_cols:
            df_clean[col] = pd.to_numeric(
                df_clean[col].astype(str).str.replace(',', ''), errors='coerce'
            ).fillna(0)

        return df_clean

    urls = [
        'https://raw.githubusercontent.com/aheiner2001/Machine-Learning/refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data.csv'
    ]

    df = pd.concat([clean_and_tag_dates(u) for u in urls], ignore_index=True)

    df = df.rename(columns={
        'Time Interval': 'time_interval',
        '# Cars (Total)': 'cars_total',
        'Date': 'day'
    })

    df['hour_of_day'] = df['time_interval'].apply(parse_hour)
    df['date'] = pd.to_datetime(df['day'], errors='coerce')
    df['datetime'] = df['date'] + pd.to_timedelta(df['hour_of_day'], unit='h')

    df['car_count'] = df['cars_total']

    # ── WEATHER (HISTORICAL) ─────────────────────────────────────────────
    params = {
        'latitude': 40.1618,
        'longitude': -111.6348,
        'start_date': df['date'].min().strftime('%Y-%m-%d'),
        'end_date': df['date'].max().strftime('%Y-%m-%d'),
        'hourly': ['temperature_2m','precipitation','wind_speed_10m'],
        'timezone': 'America/Denver'
    }

    w = requests.get("https://archive-api.open-meteo.com/v1/archive", params=params).json()

    weather = pd.DataFrame({
        'datetime': pd.to_datetime(w['hourly']['time']),
        'temp': w['hourly']['temperature_2m'],
        'precip': w['hourly']['precipitation'],
        'wind': w['hourly']['wind_speed_10m']
    })

    df = pd.merge(df, weather, on='datetime', how='left')

    # ── FEATURE ENGINEERING (UNCHANGED - FULL) ───────────────────────────
    df['hour_sin'] = np.sin(2*np.pi*df['hour_of_day']/24)
    df['hour_cos'] = np.cos(2*np.pi*df['hour_of_day']/24)
    df['day_num'] = df['date'].dt.dayofweek

    df['month_sin'] = np.sin(2*np.pi*df['date'].dt.month/12)
    df['month_cos'] = np.cos(2*np.pi*df['date'].dt.month/12)

    df['is_monday'] = (df['day_num'] == 0).astype(int)

    df['precip_yesterday'] = df['precip'].shift(24)
    df['precip_2days_ago'] = df['precip'].shift(48)
    df['precip_last_7days'] = df['precip'].rolling(24*7).sum().shift(1)

    df['wind_yesterday'] = df['wind'].shift(24)
    df['rolling_3day_wind'] = df['wind'].rolling(72).mean().shift(1)

    df['days_left_in_month'] = df['date'].dt.days_in_month - df['date'].dt.day

    df['is_holiday'] = df['date'].dt.month.isin([1,7,12]).astype(int)

    df = df.dropna()

    features = [
        'hour_of_day','hour_sin','hour_cos','day_num',
        'month_sin','month_cos',
        'temp','precip','wind',
        'precip_yesterday','precip_2days_ago','precip_last_7days',
        'wind_yesterday','rolling_3day_wind',
        'is_monday','days_left_in_month','is_holiday'
    ]

    X = df[features]
    y = np.log1p(df['car_count'])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    model = GradientBoostingRegressor()
    model.fit(X_train, y_train)

    return df, model, features

df_hist, model, features = load_and_train()

# ─────────────────────────────────────────────────────────────────────────────
# FUTURE FORECAST (NEXT 14 DAYS)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Generating forecasts...")
def build_future_forecast(model, features):

    params = {
        'latitude': 40.1618,
        'longitude': -111.6348,
        'hourly': ['temperature_2m','precipitation','wind_speed_10m'],
        'forecast_days': 14,
        'timezone': 'America/Denver'
    }

    w = requests.get("https://api.open-meteo.com/v1/forecast", params=params).json()

    weather = pd.DataFrame({
        'datetime': pd.to_datetime(w['hourly']['time']),
        'temp': w['hourly']['temperature_2m'],
        'precip': w['hourly']['precipitation'],
        'wind': w['hourly']['wind_speed_10m']
    })

    weather['hour_of_day'] = weather['datetime'].dt.hour
    weather['date'] = weather['datetime'].dt.date

    # FEATURE ENGINEERING (MATCH TRAINING)
    weather['hour_sin'] = np.sin(2*np.pi*weather['hour_of_day']/24)
    weather['hour_cos'] = np.cos(2*np.pi*weather['hour_of_day']/24)
    weather['day_num'] = pd.to_datetime(weather['date']).dayofweek

    weather['month_sin'] = np.sin(2*np.pi*pd.to_datetime(weather['date']).dt.month/12)
    weather['month_cos'] = np.cos(2*np.pi*pd.to_datetime(weather['date']).dt.month/12)

    weather['is_monday'] = (weather['day_num'] == 0).astype(int)

    # Approximate lag features (future-safe assumptions)
    weather['precip_yesterday'] = weather['precip'].shift(24).fillna(0)
    weather['precip_2days_ago'] = weather['precip'].shift(48).fillna(0)
    weather['precip_last_7days'] = weather['precip'].rolling(24*7).sum().fillna(0)

    weather['wind_yesterday'] = weather['wind'].shift(24).fillna(0)
    weather['rolling_3day_wind'] = weather['wind'].rolling(72).mean().fillna(0)

    weather['days_left_in_month'] = pd.to_datetime(weather['date']).dt.days_in_month - pd.to_datetime(weather['date']).dt.day

    weather['is_holiday'] = pd.to_datetime(weather['date']).dt.month.isin([1,7,12]).astype(int)

    X_future = weather[features]

    preds = np.expm1(model.predict(X_future))
    weather['predicted_cars'] = preds

    return weather

forecast_df = build_future_forecast(model, features)

# ─────────────────────────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────────────────────────
st.sidebar.title("🚗 Wiggy Wash")

page = st.sidebar.radio("Navigate", [
    "📅 Forecast Overview",
    "📊 Day Breakdown"
])

# ─────────────────────────────────────────────────────────────────────────────
# FORECAST OVERVIEW
# ─────────────────────────────────────────────────────────────────────────────
if page == "📅 Forecast Overview":

    st.title("Next 14-Day Forecast")

    daily = forecast_df.groupby('date')['predicted_cars'].sum().reset_index()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily['date'],
        y=daily['predicted_cars'],
        mode='lines+markers'
    ))

    fig.update_layout(
        title="Predicted Daily Traffic",
        xaxis_title="Date",
        yaxis_title="Cars",
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(daily)

# ─────────────────────────────────────────────────────────────────────────────
# DAY BREAKDOWN (FUTURE ONLY)
# ─────────────────────────────────────────────────────────────────────────────
elif page == "📊 Day Breakdown":

    st.title("Future Hourly Breakdown")

    dates = sorted(forecast_df['date'].unique())

    selected_date = st.selectbox(
        "Select a date",
        dates,
        format_func=lambda d: pd.to_datetime(d).strftime("%A %b %d")
    )

    day_df = forecast_df[forecast_df['date'] == selected_date]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=day_df['hour_of_day'],
        y=day_df['predicted_cars']
    ))

    fig.update_layout(
        title=f"Hourly Forecast – {selected_date}",
        xaxis_title="Hour",
        yaxis_title="Predicted Cars",
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(day_df[['hour_of_day','temp','precip','wind','predicted_cars']])
