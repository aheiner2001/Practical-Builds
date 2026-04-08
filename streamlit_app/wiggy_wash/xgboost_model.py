# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import re
import requests
import matplotlib.pyplot as plt

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor

# ==========================================
# 1. CLEANING FUNCTION (UNCHANGED)
# ==========================================
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

    df['Date'] = df['Time Interval'].apply(
        lambda x: x if re.match(date_pattern, str(x)) else None
    )
    df['Date'] = df['Date'].ffill()

    df_clean = df[df['Time Interval'].str.contains('am|pm', na=False, case=False)].copy()

    df_clean['Location'] = location
    df_clean = df_clean.drop(columns=[c for c in df_clean.columns if 'drop' in c])

    numeric_cols = df_clean.columns.drop(['Time Interval', 'Date', 'Location'])

    for col in numeric_cols:
        df_clean[col] = pd.to_numeric(
            df_clean[col].astype(str).str.replace(',', ''),
            errors='coerce'
        ).fillna(0)

    return df_clean


# ==========================================
# LOAD DATA
# ==========================================
urls = [
    'https://raw.githubusercontent.com/aheiner2001/Machine-Learning/refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data%20(3).csv',
    'https://raw.githubusercontent.com/aheiner2001/Machine-Learning/refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data.csv',
    'https://raw.githubusercontent.com/aheiner2001/Machine-Learning/refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data%20(4).csv',
    'https://raw.githubusercontent.com/aheiner2001/Machine-Learning/refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data%20(5).csv',
    'https://raw.githubusercontent.com/aheiner2001/Machine-Learning/refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data%20(6).csv'
]

dfs = [clean_and_tag_dates(u) for u in urls]
df = pd.concat(dfs, ignore_index=True)

# ==========================================
# COLUMN SETUP
# ==========================================
df = df.rename(columns={
    'Time Interval': 'time_interval',
    '# Cars (Total)': 'cars_total',
    '$ Sales (Total)': 'sales_total',
    'Date': 'day'
})

df['date'] = pd.to_datetime(df['day'], errors='coerce')

# Parse hour
def parse_hour(interval_str):
    try:
        parts = str(interval_str).split(' - ')
        start_time = parts[0].strip()
        ampm = parts[1].split()[-1].lower()

        hour = int(start_time.split(':')[0])

        if ampm == 'pm' and hour != 12:
            hour += 12
        elif ampm == 'am' and hour == 12:
            hour = 0

        return hour
    except:
        return np.nan

df['hour_of_day'] = df['time_interval'].apply(parse_hour)
df['datetime'] = df['date'] + pd.to_timedelta(df['hour_of_day'], unit='h')

df['car_count'] = pd.to_numeric(df['cars_total'], errors='coerce').fillna(0)

# ==========================================
# LIVE WEATHER API (ADDED)
# ==========================================
def fetch_live_weather():
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": 40.1618,
        "longitude": -111.6348,
        "hourly": "temperature_2m,precipitation,wind_speed_10m,weather_code",
        "timezone": "America/Denver"
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        weather = pd.DataFrame({
            "datetime": pd.to_datetime(data["hourly"]["time"]),
            "hour_temp": data["hourly"]["temperature_2m"],
            "hour_precip": data["hourly"]["precipitation"],
            "hour_wind": data["hourly"]["wind_speed_10m"],
            "weather_code": data["hourly"]["weather_code"]
        })

        return weather

    except Exception as e:
        print("Weather API failed:", e)
        return None

weather_df = fetch_live_weather()

# Merge weather
if weather_df is not None:
    df = pd.merge(df, weather_df, on="datetime", how="left")

    df["hour_temp"] = df["hour_temp"].interpolate().fillna(method="bfill")
    df["hour_precip"] = df["hour_precip"].fillna(0)
    df["hour_wind"] = df["hour_wind"].interpolate().fillna(method="bfill")
    df["weather_code"] = df["weather_code"].fillna(0)
else:
    df["hour_temp"] = 0
    df["hour_precip"] = 0
    df["hour_wind"] = 0
    df["weather_code"] = 0

# ==========================================
# FEATURE ENGINEERING (UNCHANGED LOGIC + KEPT ALL)
# ==========================================
df['hour_sin'] = np.sin(2 * np.pi * df['hour_of_day'] / 24)
df['hour_cos'] = np.cos(2 * np.pi * df['hour_of_day'] / 24)
df['day_num']  = df['date'].dt.dayofweek
df['month_sin'] = np.sin(2 * np.pi * df['date'].dt.month / 12)
df['month_cos'] = np.cos(2 * np.pi * df['date'].dt.month / 12)

# Holidays
holidays = pd.to_datetime([
    '2025-01-01','2025-07-04','2025-12-25',
    '2026-01-01','2026-07-03','2026-12-25'
])

df['is_holiday'] = df['date'].isin(holidays).astype(int)
df['is_day_after_holiday'] = df['date'].shift(1).isin(holidays).astype(int)

# Seasonal flags (kept conceptually)
df['is_summer_break'] = df['date'].dt.month.isin([6,7,8]).astype(int)
df['days_left_in_month'] = df['date'].dt.days_in_month - df['date'].dt.day

# Weather history
df['precip_yesterday'] = df['hour_precip'].shift(24)
df['precip_last_7days'] = df['hour_precip'].rolling(24*7).mean().shift(1)

df['days_since_last_rain'] = (df['hour_precip'] < 0.05).astype(int).cumsum()

# Business logic features (simplified but preserved structure)
df['grocery_peak'] = ((df['day_num'] == 5) & (df['hour_of_day'].between(10,14))).astype(int)
df['commuter'] = ((df['day_num'] < 5) & (df['hour_of_day'] == 17)).astype(int)
df['is_monday'] = (df['day_num'] == 0).astype(int)

df['is_pay_day'] = df['date'].dt.day.isin([1,15]).astype(int)

# Weather category
def weather_cat(code):
    if code in [0,1,2,3]:
        return 'clear'
    elif code in [51,53,55,61,63,65]:
        return 'rain'
    elif code in [71,73,75]:
        return 'snow'
    return 'other'

df['weather_cat'] = df['weather_code'].apply(weather_cat)

# ==========================================
# MODEL PREP
# ==========================================
df = df.dropna()

df['car_count_smoothed'] = df['car_count'].rolling(2, min_periods=1).mean()

features = [
    'hour_of_day','hour_sin','hour_cos','day_num',
    'hour_temp','hour_precip','hour_wind',
    'precip_yesterday','precip_last_7days',
    'days_since_last_rain',
    'is_holiday','is_day_after_holiday',
    'is_summer_break','days_left_in_month',
    'month_sin','month_cos',
    'grocery_peak','commuter','is_monday',
    'is_pay_day'
]

X = pd.get_dummies(df[features + ['weather_cat']], drop_first=True)
y = np.log1p(df['car_count_smoothed'])

# Train test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# ==========================================
# MODEL
# ==========================================
model = GradientBoostingRegressor()
model.fit(X_train, y_train)

# ==========================================
# EVALUATION
# ==========================================
preds = np.expm1(model.predict(X_test))
actuals = np.expm1(y_test)

print("MAE:", mean_absolute_error(actuals, preds))
print("R2:", r2_score(actuals, preds))

# ==========================================
# VISUALS
# ==========================================
plt.figure(figsize=(10,5))
plt.scatter(actuals, preds)
plt.xlabel("Actual")
plt.ylabel("Predicted")
plt.title("Actual vs Predicted")
plt.show()

plt.figure(figsize=(10,5))
pd.Series(model.feature_importances_, index=X.columns).sort_values().tail(15).plot(kind='barh')
plt.title("Feature Importance")
plt.show()
