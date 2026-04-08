import streamlit as st
import pandas as pd
import numpy as np
import re
import requests
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor

st.set_page_config(layout="wide")
st.title("🚗 Wiggy Wash AI Dashboard")

# ==============================
# DATA CLEANING FUNCTION
# ==============================
def clean_and_tag_dates(url):
    df = pd.read_csv(url, header=None)

    location = df.iloc[3, 0] if "Location" in str(df.iloc[3,0]) else "UT0032"

    col_names = [
        'Time Interval', '# Cars (Total)', 'drop1', '$ Sales (Total)',
        '$ Sales (Total/Car)', 'drop2', '$ Sales (Base)', '# Cars (Extra)',
        '$ Sales (Extra)', '$ Sales (Ext/Car)', 'drop3', '% Cars (Extra)',
        '# Cars (Inv)', '$ Sales (Inv)'
    ]
    df.columns = col_names

    date_pattern = r'\d{2}/\d{2}/\d{4}'
    df['Date'] = df['Time Interval'].apply(lambda x: x if re.match(date_pattern, str(x)) else None)
    df['Date'] = df['Date'].ffill()

    df_clean = df[df['Time Interval'].str.contains('am|pm', na=False, case=False)].copy()
    df_clean['Location'] = location
    df_clean = df_clean.drop(columns=[c for c in df_clean.columns if 'drop' in c])

    numeric_cols = df_clean.columns.drop(['Time Interval', 'Date', 'Location'])
    for col in numeric_cols:
        df_clean[col] = pd.to_numeric(df_clean[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

    return df_clean

# ==============================
# LOAD + TRAIN MODEL (CACHED)
# ==============================
@st.cache_data(show_spinner=True)
def load_and_train():

    urls = [
        'https://raw.githubusercontent.com/aheiner2001/Machine-Learning/refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data%20(3).csv',
        'https://raw.githubusercontent.com/aheiner2001/Machine-Learning/refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data.csv',
        'https://raw.githubusercontent.com/aheiner2001/Machine-Learning/refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data%20(4).csv',
        'https://raw.githubusercontent.com/aheiner2001/Machine-Learning/refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data%20(5).csv',
        'https://raw.githubusercontent.com/aheiner2001/Machine-Learning/refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data%20(6).csv'
    ]

    dfs = [clean_and_tag_dates(u) for u in urls]
    df = pd.concat(dfs, ignore_index=True)

    # Rename
    df = df.rename(columns={
        'Time Interval': 'time_interval',
        '# Cars (Total)': 'cars_total',
        'Date': 'day'
    })

    df['hour_of_day'] = df['time_interval'].apply(lambda x: int(str(x).split(':')[0]) if isinstance(x, str) else 0)
    df['date'] = pd.to_datetime(df['day'], errors='coerce')
    df['datetime'] = df['date'] + pd.to_timedelta(df['hour_of_day'], unit='h')

    df['hour_sin'] = np.sin(2 * np.pi * df['hour_of_day'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour_of_day'] / 24)

    df['car_count'] = pd.to_numeric(df['cars_total'], errors='coerce').fillna(0)

    # ================= WEATHER =================
    params = {
        'latitude': 40.1618,
        'longitude': -111.6348,
        'start_date': df['date'].min().strftime('%Y-%m-%d'),
        'end_date': df['date'].max().strftime('%Y-%m-%d'),
        'hourly': ['temperature_2m', 'precipitation', 'wind_speed_10m', 'weather_code'],
        'daily': ['temperature_2m_max', 'precipitation_sum', 'wind_speed_10m_max'],
        'timezone': 'America/Denver',
    }

    w = requests.get('https://archive-api.open-meteo.com/v1/archive', params=params).json()

    hourly = pd.DataFrame({
        'datetime': pd.to_datetime(w['hourly']['time']),
        'hour_temp': w['hourly']['temperature_2m'],
        'hour_precip': w['hourly']['precipitation'],
        'hour_wind': w['hourly']['wind_speed_10m'],
    })

    daily = pd.DataFrame({
        'date': pd.to_datetime(w['daily']['time']),
        'day_precip_sum': w['daily']['precipitation_sum'],
        'day_wind_max': w['daily']['wind_speed_10m_max']
    })

    df = df.merge(hourly, on='datetime', how='left')
    df = df.merge(daily, on='date', how='left')

    df['day_num'] = df['date'].dt.dayofweek
    df['month_sin'] = np.sin(2 * np.pi * df['date'].dt.month / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['date'].dt.month / 12)

    df['precip_yesterday'] = df['day_precip_sum'].shift(1)
    df['precip_last_7days'] = df['day_precip_sum'].rolling(7).sum().shift(1)

    df['days_since_last_rain'] = (df['day_precip_sum'] == 0).astype(int).cumsum()

    df['is_pay_day'] = df['date'].dt.day.isin([1,15]).astype(int)

    features = [
        'hour_of_day','hour_sin','hour_cos','day_num',
        'hour_temp','hour_precip','hour_wind',
        'precip_yesterday','precip_last_7days',
        'days_since_last_rain','month_sin','month_cos','is_pay_day'
    ]

    df_model = df.dropna(subset=features)

    X = df_model[features]
    y = np.log1p(df_model['car_count'])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    model = XGBRegressor(n_estimators=300)
    model.fit(X_train, y_train)

    preds = np.expm1(model.predict(X_test))
    actuals = np.expm1(y_test)

    mae = mean_absolute_error(actuals, preds)
    rmse = np.sqrt(mean_squared_error(actuals, preds))
    r2 = r2_score(actuals, preds)

    df_model['predicted'] = np.expm1(model.predict(X))

    return df_model, mae, rmse, r2

df, mae, rmse, r2 = load_and_train()

# ==============================
# DASHBOARD
# ==============================

st.header("📉 Model Performance")
col1, col2, col3 = st.columns(3)
col1.metric("MAE", f"{mae:.2f}")
col2.metric("RMSE", f"{rmse:.2f}")
col3.metric("R²", f"{r2:.2f}")

# ==============================
# WEEK VIEW
# ==============================
st.header("📅 Weekly Traffic")

daily = df.groupby(df['date'].dt.date)['predicted'].sum()
st.bar_chart(daily)

# ==============================
# DAY VIEW
# ==============================
selected_day = st.selectbox("Select Day", sorted(df['date'].dt.date.unique()))
day_df = df[df['date'].dt.date == selected_day]

st.subheader("Hourly Traffic Prediction")
st.line_chart(day_df.set_index('hour_of_day')['predicted'])

st.subheader("Weather vs Traffic")
st.line_chart(day_df.set_index('hour_of_day')[['hour_temp','predicted']])

# ==============================
# UPSSELL LOGIC
# ==============================
day_df['upsell_score'] = (
    (day_df['hour_temp'] > 60).astype(int)*0.5 +
    (day_df['hour_precip']==0).astype(int)*0.3 +
    (day_df['predicted'] > day_df['predicted'].mean()).astype(int)*0.2
)

def label(x):
    if x > .7: return "🔥 HIGH"
    elif x > .4: return "⚡ MED"
    else: return "❄️ LOW"

day_df['upsell'] = day_df['upsell_score'].apply(label)

st.subheader("Upsell Opportunities")
st.dataframe(day_df[['hour_of_day','predicted','hour_temp','hour_precip','upsell']])
