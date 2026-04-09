import streamlit as st
import pandas as pd
import numpy as np
import requests
import joblib
from datetime import datetime, timedelta

st.set_page_config(page_title="WiggyWash Forecast", layout="wide")

LAT, LON = 40.1618, -111.6348

# ─────────────────────────────────────────────
# LOAD MODEL
# ─────────────────────────────────────────────
@st.cache_resource
def load_pipeline():
    return joblib.load("pipeline.pkl")

data = load_pipeline()
model = data["model"]
feature_cols = data["feature_cols"]
hour_pct_mapping = data["hour_pct_mapping"]

# ─────────────────────────────────────────────
# WEATHER (OPEN METEO)
# ─────────────────────────────────────────────
def fetch_weather(start, end, archive=True):
    url = "https://archive-api.open-meteo.com/v1/archive" if archive else "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": LAT,
        "longitude": LON,
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
        "hourly": ["temperature_2m","precipitation","wind_speed_10m","weather_code"],
        "daily": ["temperature_2m_max","precipitation_sum","wind_speed_10m_max"],
        "timezone": "America/Denver",
        "temperature_unit": "fahrenheit",
        "precipitation_unit": "inch",
        "wind_speed_unit": "mph"
    }

    return requests.get(url, params=params).json()


def parse_weather(w):
    hourly = pd.DataFrame({
        "datetime": pd.to_datetime(w["hourly"]["time"]),
        "hour_temp": w["hourly"]["temperature_2m"],
        "hour_precip": w["hourly"]["precipitation"],
        "hour_wind": w["hourly"]["wind_speed_10m"],
        "weather_code": w["hourly"]["weather_code"],
    })

    daily = pd.DataFrame({
        "date": pd.to_datetime(w["daily"]["time"]),
        "day_temp_max": w["daily"]["temperature_2m_max"],
        "day_precip_sum": w["daily"]["precipitation_sum"],
        "day_wind_max": w["daily"]["wind_speed_10m_max"],
    })

    return hourly, daily


# ─────────────────────────────────────────────
# FEATURE ENGINEERING (CORE)
# ─────────────────────────────────────────────
def add_features(df):

    df["hour_of_day"] = df["datetime"].dt.hour
    df["date"] = df["datetime"].dt.floor("D")

    df["hour_sin"] = np.sin(2*np.pi*df["hour_of_day"]/24)
    df["hour_cos"] = np.cos(2*np.pi*df["hour_of_day"]/24)

    df["day_num"] = df["date"].dt.dayofweek
    df["month_sin"] = np.sin(2*np.pi*df["date"].dt.month/12)
    df["month_cos"] = np.cos(2*np.pi*df["date"].dt.month/12)

    # Rain tracking
    df["is_rainy_day"] = (df["day_precip_sum"] > 0.05).astype(int)
    grp = df["is_rainy_day"].cumsum()
    df["days_since_last_rain"] = df.groupby(grp).cumcount()
    df.loc[df["is_rainy_day"] == 1, "days_since_last_rain"] = 0

    # Lag features
    df["precip_yesterday"] = df["day_precip_sum"].shift(24)
    df["precip_last_7days"] = df["day_precip_sum"].rolling(24*7).sum().shift(1)

    df["wind_yesterday"] = df["day_wind_max"].shift(24)
    df["rolling_7day_wind"] = df["day_wind_max"].rolling(24*7).mean().shift(1)

    # Fill NaNs safely
    df = df.fillna(0)

    # Mapping feature
    df["hour_pct_of_day"] = df.apply(
        lambda r: hour_pct_mapping.get((r["day_num"], r["hour_of_day"]), 0.5),
        axis=1
    )

    return df


# ─────────────────────────────────────────────
# FORECAST PIPELINE
# ─────────────────────────────────────────────
def generate_forecast(start_date, days):

    end_date = start_date + timedelta(days=days)

    # Get past + future
    hist_start = start_date - timedelta(days=10)

    w_hist = fetch_weather(hist_start, start_date - timedelta(days=1), archive=True)
    w_fore = fetch_weather(start_date, end_date, archive=False)

    h1, d1 = parse_weather(w_hist)
    h2, d2 = parse_weather(w_fore)

    hourly = pd.concat([h1, h2]).drop_duplicates("datetime")
    daily = pd.concat([d1, d2]).drop_duplicates("date")

    df = hourly.merge(daily, on="date", how="left")
    df = df.sort_values("datetime").reset_index(drop=True)

    # Add features
    df = add_features(df)

    # Filter prediction window
    df_pred = df[df["date"] >= pd.Timestamp(start_date)]

    # Only business hours
    df_pred = df_pred[df_pred["hour_of_day"].between(7, 20)]

    # Build model input
    X = pd.get_dummies(df_pred, drop_first=True)
    X = X.reindex(columns=feature_cols, fill_value=0)

    preds = np.expm1(model.predict(X))
    df_pred["predicted_cars"] = np.maximum(preds, 0)

    return df_pred


# ─────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────
st.title("🚗 WiggyWash Forecast (Live ML)")

start_date = st.date_input("Start Date", value=datetime.now().date())
days = st.slider("Forecast Days", 7, 14, 14)

if st.button("Run Forecast"):

    with st.spinner("Running ML forecast..."):
        df = generate_forecast(
            datetime(start_date.year, start_date.month, start_date.day),
            days
        )

    daily = df.groupby("date")["predicted_cars"].sum().reset_index()

    st.subheader("📊 Daily Volume")
    st.bar_chart(daily.set_index("date"))

    selected_day = st.selectbox("Select Day", daily["date"])
    st.subheader("⏱ Hourly Breakdown")

    day_df = df[df["date"] == selected_day]
    st.bar_chart(day_df.set_index("hour_of_day")["predicted_cars"])

    st.dataframe(df)
