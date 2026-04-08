# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import re
import requests
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor

# =========================================================
# 1. LOAD + CLEAN DATA
# =========================================================

def clean_and_tag_dates(url):
    df = pd.read_csv(url, header=None)

    location = df.iloc[3, 0] if "Location" in str(df.iloc[3, 0]) else "UT0032"

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
        df_clean[col] = pd.to_numeric(
            df_clean[col].astype(str).str.replace(',', ''),
            errors='coerce'
        ).fillna(0)

    return df_clean


urls = [
    'https://raw.githubusercontent.com/aheiner2001/Machine-Learning/refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data%20(3).csv',
    'https://raw.githubusercontent.com/aheiner2001/Machine-Learning/refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data.csv',
    'https://raw.githubusercontent.com/aheiner2001/Machine-Learning/refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data%20(4).csv',
    'https://raw.githubusercontent.com/aheiner2001/Machine-Learning/refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data%20(5).csv',
    'https://raw.githubusercontent.com/aheiner2001/Machine-Learning/refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data%20(6).csv'
]

df = pd.concat([clean_and_tag_dates(url) for url in urls], ignore_index=True)

# =========================================================
# 2. COLUMN STANDARDIZATION
# =========================================================

df = df.rename(columns={
    'Time Interval': 'time_interval',
    '# Cars (Total)': 'cars_total',
    'Date': 'day'
})

# Keep only needed columns safely
df = df[['time_interval', 'cars_total', 'day']].copy()

# =========================================================
# 3. FEATURE ENGINEERING (TIME)
# =========================================================

def parse_hour(interval_str):
    try:
        parts = str(interval_str).split(' - ')
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


df['hour_of_day'] = df['time_interval'].apply(parse_hour)
df['date'] = pd.to_datetime(df['day'], errors='coerce')

df['hour_sin'] = np.sin(2 * np.pi * df['hour_of_day'] / 24)
df['hour_cos'] = np.cos(2 * np.pi * df['hour_of_day'] / 24)
df['day_num'] = df['date'].dt.dayofweek

df['car_count'] = pd.to_numeric(df['cars_total'], errors='coerce').fillna(0)

# =========================================================
# 4. WEATHER
# =========================================================

params = {
    'latitude': 40.1618,
    'longitude': -111.6348,
    'start_date': df['date'].min().strftime('%Y-%m-%d'),
    'end_date': df['date'].max().strftime('%Y-%m-%d'),
    'hourly': ['temperature_2m', 'precipitation', 'wind_speed_10m', 'weather_code'],
    'daily': ['temperature_2m_max', 'precipitation_sum', 'wind_speed_10m_max'],
    'timezone': 'America/Denver'
}

response = requests.get('https://archive-api.open-meteo.com/v1/archive', params=params)
w_data = response.json()

hourly_weather = pd.DataFrame({
    'datetime': pd.to_datetime(w_data['hourly']['time']),
    'hour_temp': w_data['hourly']['temperature_2m'],
    'hour_precip': w_data['hourly']['precipitation'],
    'hour_wind': w_data['hourly']['wind_speed_10m']
})

df['datetime'] = df['date'] + pd.to_timedelta(df['hour_of_day'], unit='h')
df = pd.merge(df, hourly_weather, on='datetime', how='left')

# =========================================================
# 5. FEATURE ENGINEERING (SAFE + COMPLETE)
# =========================================================

df['is_monday'] = (df['day_num'] == 0).astype(int)
df['grocery_peak'] = ((df['day_num'] == 5) & df['hour_of_day'].between(10, 14)).astype(int)
df['commuter'] = ((df['day_num'] < 5) & (df['hour_of_day'] == 17)).astype(int)

df['month'] = df['date'].dt.month
df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)

# =========================================================
# 6. FINAL FEATURE SET (DYNAMIC + SAFE)
# =========================================================

features = [
    'hour_of_day','hour_sin','hour_cos','day_num',
    'hour_temp','hour_precip','hour_wind',
    'is_monday','grocery_peak','commuter',
    'month_sin','month_cos'
]

# ✅ Only keep features that actually exist
features = [f for f in features if f in df.columns]

df_model = df.dropna(subset=features + ['car_count']).copy()

X = df_model[features]
y = np.log1p(df_model['car_count'])

# =========================================================
# 7. TRAIN MODEL
# =========================================================

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = GradientBoostingRegressor(
    n_estimators=300,
    learning_rate=0.05,
    max_depth=4,
    random_state=42
)

model.fit(X_train, y_train)

# =========================================================
# 8. EVALUATION
# =========================================================

preds = np.expm1(model.predict(X_test))
actuals = np.expm1(y_test)

print("MAE:", mean_absolute_error(actuals, preds))
print("RMSE:", np.sqrt(mean_squared_error(actuals, preds)))
print("R2:", r2_score(actuals, preds))

# =========================================================
# 9. FEATURE IMPORTANCE
# =========================================================

plt.figure()
pd.Series(model.feature_importances_, index=features).sort_values().plot(kind='barh')
plt.title("Feature Importance")
plt.show()
