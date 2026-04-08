# Streamlit App: WiggyWash Forecast

import streamlit as st
import pandas as pd
import numpy as np
import requests
import re
from datetime import datetime, timedelta

from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="WiggyWash Forecast", layout="wide")

st.title("🚗 WiggyWash Demand Forecast (7–14 Day)")

# ==============================
# DATA LOADING & CLEANING
# ==============================
@st.cache_data
def load_and_clean_data():
    urls = [
        'https://raw.githubusercontent.com/aheiner2001/Machine-Learning/refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data%20(3).csv',
        'https://raw.githubusercontent.com/aheiner2001/Machine-Learning/refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data.csv',
        'https://raw.githubusercontent.com/aheiner2001/Machine-Learning/refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data%20(4).csv',
        'https://raw.githubusercontent.com/aheiner2001/Machine-Learning/refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data%20(5).csv',
        'https://raw.githubusercontent.com/aheiner2001/Machine-Learning/refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data%20(6).csv'
    ]

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

    dfs = [clean_and_tag_dates(u) for u in urls]
    df = pd.concat(dfs, ignore_index=True)

    df = df.rename(columns={
        'Time Interval': 'time_interval',
        '# Cars (Total)': 'cars_total',
        '$ Sales (Total)': 'sales_total',
        'Date': 'day'
    })

    df['car_count'] = df['cars_total']
    df['date'] = pd.to_datetime(df['day'], errors='coerce')

    return df

# ==============================
# WEATHER
# ==============================
@st.cache_data
def get_weather(df):
    params = {
        'latitude': 40.1618,
        'longitude': -111.6348,
        'start_date': df['date'].min().strftime('%Y-%m-%d'),
        'end_date': df['date'].max().strftime('%Y-%m-%d'),
        'hourly': ['temperature_2m', 'precipitation', 'wind_speed_10m'],
        'timezone': 'America/Denver'
    }

    r = requests.get('https://archive-api.open-meteo.com/v1/archive', params=params)
    data = r.json()

    if 'hourly' not in data:
        return None

    hourly = pd.DataFrame({
        'datetime': pd.to_datetime(data['hourly']['time']),
        'hour_temp': data['hourly']['temperature_2m'],
        'hour_precip': data['hourly']['precipitation'],
        'hour_wind': data['hourly']['wind_speed_10m']
    })

    return hourly

# ==============================
# FEATURE ENGINEERING
# ==============================
def build_features(df, hourly_weather):
    df['hour_of_day'] = pd.to_datetime(df['time_interval'], errors='coerce').dt.hour.fillna(0)
    df['datetime'] = df['date'] + pd.to_timedelta(df['hour_of_day'], unit='h')

    df = pd.merge(df, hourly_weather, left_on='datetime', right_on='datetime', how='left')

    df['hour_sin'] = np.sin(2*np.pi*df['hour_of_day']/24)
    df['hour_cos'] = np.cos(2*np.pi*df['hour_of_day']/24)
    df['day_num'] = df['date'].dt.dayofweek

    df['precip_yesterday'] = df['hour_precip'].shift(24)

    df['car_count'] = pd.to_numeric(df['car_count'], errors='coerce').fillna(0)

    return df

# ==============================
# MODEL
# ==============================
@st.cache_resource
def train_model(df):
    df = df.dropna(subset=['hour_temp','hour_precip'])

    features = ['hour_of_day','hour_sin','hour_cos','day_num','hour_temp','hour_precip']

    X = df[features]
    y = np.log1p(df['car_count'])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = GradientBoostingRegressor()
    model.fit(X_train, y_train)

    return model, features

# ==============================
# FORECAST
# ==============================
@st.cache_data
def forecast_future(model, df, hourly_weather, days=14):
    future_dates = pd.date_range(start=df['date'].max(), periods=days*24, freq='H')

    future_df = pd.DataFrame({'datetime': future_dates})
    future_df['hour_of_day'] = future_df['datetime'].dt.hour
    future_df['day_num'] = future_df['datetime'].dt.dayofweek

    future_df = pd.merge(future_df, hourly_weather, on='datetime', how='left')

    future_df['hour_sin'] = np.sin(2*np.pi*future_df['hour_of_day']/24)
    future_df['hour_cos'] = np.cos(2*np.pi*future_df['hour_of_day']/24)

    features = ['hour_of_day','hour_sin','hour_cos','day_num','hour_temp','hour_precip']
    X_future = future_df[features].fillna(0)

    preds = np.expm1(model.predict(X_future))
    future_df['predicted_cars'] = preds

    return future_df

# ==============================
# MAIN APP
# ==============================
df = load_and_clean_data()
hourly_weather = get_weather(df)

if hourly_weather is None:
    st.error("Weather API failed")
    st.stop()

features_df = build_features(df, hourly_weather)
model, features = train_model(features_df)
forecast_df = forecast_future(model, features_df, hourly_weather)

# ==============================
# UI
# ==============================
view_days = st.slider("Forecast Days", 1, 14, 7)

forecast_view = forecast_df.head(view_days*24)

st.subheader("📈 Forecasted Demand")
st.line_chart(forecast_view.set_index('datetime')['predicted_cars'])

# Daily aggregation
forecast_view['date'] = forecast_view['datetime'].dt.date
daily = forecast_view.groupby('date')['predicted_cars'].sum().reset_index()

st.subheader("📊 Daily Demand")
st.bar_chart(daily.set_index('date'))

# Insights
st.subheader("💡 Insights")
avg_demand = forecast_view['predicted_cars'].mean()
peak = forecast_view['predicted_cars'].max()
low = forecast_view['predicted_cars'].min()

st.write(f"Average hourly demand: {avg_demand:.1f}")
st.write(f"Peak hourly demand: {peak:.1f}")
st.write(f"Low hourly demand: {low:.1f}")

high_days = daily[daily['predicted_cars'] > daily['predicted_cars'].quantile(0.75)]
low_days = daily[daily['predicted_cars'] < daily['predicted_cars'].quantile(0.25)]

st.write("🔥 High demand days:")
st.dataframe(high_days)

st.write("❄️ Low demand days:")
st.dataframe(low_days)

# Hourly drilldown
selected_date = st.selectbox("Select Date", sorted(forecast_view['date'].unique()))

subset = forecast_view[forecast_view['date'] == selected_date]

st.subheader(f"Hourly Trend for {selected_date}")
st.line_chart(subset.set_index('datetime')['predicted_cars'])
