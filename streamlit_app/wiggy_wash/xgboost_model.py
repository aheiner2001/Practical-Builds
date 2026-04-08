"""
WiggyWash — 14-Day Car Volume Forecast
Streamlit App — Full ML Pipeline + Open-Meteo Weather
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="WiggyWash Forecast",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=IBM+Plex+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
}

/* Dark industrial background */
.stApp {
    background-color: #0d0f14;
    color: #e8e4dc;
}

/* Remove default padding */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}

/* Header */
.main-header {
    background: linear-gradient(135deg, #1a1f2e 0%, #0d1117 100%);
    border: 1px solid #2a3040;
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.main-header::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -10%;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(0,200,255,0.06) 0%, transparent 70%);
    border-radius: 50%;
}
.main-header h1 {
    font-size: 2.8rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    margin: 0;
    background: linear-gradient(90deg, #00c8ff, #7b61ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.main-header p {
    color: #8892a4;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.85rem;
    margin: 0.5rem 0 0 0;
    letter-spacing: 0.05em;
}

/* Metric cards */
.metric-card {
    background: #141820;
    border: 1px solid #252d3d;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    text-align: center;
    transition: border-color 0.2s;
}
.metric-card:hover { border-color: #00c8ff44; }
.metric-card .value {
    font-size: 2.2rem;
    font-weight: 800;
    color: #00c8ff;
    line-height: 1;
}
.metric-card .label {
    font-size: 0.75rem;
    color: #5a6478;
    font-family: 'IBM Plex Mono', monospace;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-top: 0.4rem;
}

/* Day cards */
.day-card {
    background: #141820;
    border: 1px solid #252d3d;
    border-radius: 14px;
    padding: 1rem 1.25rem;
    cursor: pointer;
    transition: all 0.2s ease;
    text-align: left;
}
.day-card:hover {
    border-color: #00c8ff66;
    background: #1a2030;
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0,200,255,0.08);
}
.day-card.selected {
    border-color: #00c8ff;
    background: #0d1825;
    box-shadow: 0 0 20px rgba(0,200,255,0.15);
}
.day-card .day-name {
    font-size: 0.7rem;
    font-family: 'IBM Plex Mono', monospace;
    color: #5a6478;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}
.day-card .day-date {
    font-size: 1.1rem;
    font-weight: 700;
    color: #e8e4dc;
    margin: 0.15rem 0;
}
.day-card .day-cars {
    font-size: 1.6rem;
    font-weight: 800;
    color: #00c8ff;
}
.day-card .day-bar {
    height: 4px;
    border-radius: 2px;
    margin-top: 0.5rem;
    background: linear-gradient(90deg, #00c8ff, #7b61ff);
}

/* Section headers */
.section-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #e8e4dc;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    border-left: 3px solid #00c8ff;
    padding-left: 0.75rem;
    margin-bottom: 1rem;
}

/* Staffing badges */
.badge-low { background: #1a3a2a; color: #4ade80; border: 1px solid #4ade8044; }
.badge-medium { background: #3a2a1a; color: #fbbf24; border: 1px solid #fbbf2444; }
.badge-high { background: #3a1a1a; color: #f87171; border: 1px solid #f8717144; }
.badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-family: 'IBM Plex Mono', monospace;
    font-weight: 500;
}

/* Alerts */
.alert-box {
    background: #1a2030;
    border-left: 3px solid #fbbf24;
    border-radius: 0 8px 8px 0;
    padding: 0.75rem 1rem;
    margin: 0.5rem 0;
    font-size: 0.85rem;
    color: #d4b483;
}

/* Override Streamlit button */
div[data-testid="column"] button {
    background: #141820 !important;
    border: 1px solid #252d3d !important;
    color: #e8e4dc !important;
    border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    width: 100% !important;
    padding: 0.6rem !important;
    transition: all 0.2s !important;
}
div[data-testid="column"] button:hover {
    border-color: #00c8ff88 !important;
    background: #1a2030 !important;
}

/* Info row */
.info-pill {
    display: inline-block;
    background: #1a2030;
    border: 1px solid #252d3d;
    border-radius: 20px;
    padding: 0.3rem 0.9rem;
    font-size: 0.78rem;
    font-family: 'IBM Plex Mono', monospace;
    color: #8892a4;
    margin-right: 0.5rem;
}
.info-pill span { color: #00c8ff; font-weight: 600; }

/* Hide Streamlit branding */
#MainMenu, footer, header { visibility: hidden; }

/* Plotly transparent bg */
.js-plotly-plot .plotly { background: transparent !important; }

/* Number inputs */
.stNumberInput input {
    background: #141820 !important;
    border: 1px solid #252d3d !important;
    color: #e8e4dc !important;
    border-radius: 8px !important;
    font-family: 'IBM Plex Mono', monospace !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# TRAINING DATA URLS
# ─────────────────────────────────────────────
TRAINING_URLS = [
    'https://raw.githubusercontent.com/aheiner2001/Machine-Learning/refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data%20(3).csv',
    'https://raw.githubusercontent.com/aheiner2001/Machine-Learning/refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data.csv',
    'https://raw.githubusercontent.com/aheiner2001/Machine-Learning/refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data%20(4).csv',
    'https://raw.githubusercontent.com/aheiner2001/Machine-Learning/refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data%20(5).csv',
    'https://raw.githubusercontent.com/aheiner2001/Machine-Learning/refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data%20(6).csv',
]

LAT, LON = 40.1618, -111.6348  # Orem, UT


# ─────────────────────────────────────────────
# DATA LOADING & CLEANING
# ─────────────────────────────────────────────
import re

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
        df_clean[col] = pd.to_numeric(df_clean[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    return df_clean


def parse_hour(interval_str):
    try:
        parts = str(interval_str).strip().split(' - ')
        start_time = parts[0].strip()
        ampm = parts[1].strip().split()[-1]
        hour = int(start_time.split(':')[0])
        if ampm.lower() == 'pm' and hour != 12: hour += 12
        elif ampm.lower() == 'am' and hour == 12: hour = 0
        return hour
    except:
        return np.nan


def get_weather_cat(code):
    if code in [0, 1, 2, 3]: return 'clear'
    if code in [51, 53, 55, 61, 63, 65]: return 'rain'
    if code in [71, 73, 75, 85, 86]: return 'snow'
    return 'other'


def add_features(df):
    """Apply full feature engineering pipeline."""
    df = df.copy()

    df['hour_sin'] = np.sin(2 * np.pi * df['hour_of_day'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour_of_day'] / 24)
    df['day_num']  = df['date'].dt.dayofweek
    df['month_sin'] = np.sin(2 * np.pi * df['date'].dt.month / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['date'].dt.month / 12)

    holidays = pd.to_datetime([
        '2024-01-01','2024-01-15','2024-02-19','2024-05-27','2024-06-19','2024-07-04',
        '2024-09-02','2024-10-14','2024-11-11','2024-11-28','2024-12-25',
        '2025-01-01','2025-01-20','2025-02-17','2025-05-26','2025-06-19','2025-07-04',
        '2025-09-01','2025-10-13','2025-11-11','2025-11-27','2025-12-25',
        '2026-01-01','2026-01-19','2026-02-16','2026-05-25','2026-06-19','2026-07-03',
        '2026-09-07','2026-10-12','2026-11-11','2026-11-26','2026-12-25',
    ])
    days_after_holidays = holidays + pd.to_timedelta(1, unit='D')

    df['is_holiday'] = df['date'].isin(holidays).astype(int)
    df['is_day_after_holiday'] = df['date'].isin(days_after_holidays).astype(int)

    m, d = df['date'].dt.month, df['date'].dt.day
    df['is_christmas_week']     = ((m == 12) & (d >= 23)).astype(int)
    df['is_christmas_season']   = ((m == 12) & (d >= 15)).astype(int)
    df['is_new_years_week']     = ((m == 1)  & (d <= 7)).astype(int)
    df['is_holiday_week']       = ((df['is_christmas_week'] == 1) | (df['is_new_years_week'] == 1)).astype(int)
    df['is_pre_christmas_rush'] = ((m == 12) & (d >= 15) & (d <= 22)).astype(int)
    df['is_post_christmas_slow']= (((m == 12) & (d >= 26)) | ((m == 1) & (d <= 3))).astype(int)
    df['is_early_december']     = ((m == 12) & (d <= 14)).astype(int)
    df['is_post_thanksgiving']  = ((m == 11) & (d >= 28) & (d <= 30)).astype(int)
    df['days_left_in_month']    = df['date'].dt.days_in_month - df['date'].dt.day

    df['is_summer_break'] = (
        (df['date'].dt.month == 6) |
        (df['date'].dt.month == 7) |
        ((df['date'].dt.month == 5) & (df['date'].dt.day >= 27)) |
        ((df['date'].dt.month == 8) & (df['date'].dt.day <= 18))
    ).astype(int)

    df['is_university_in_session'] = (
        (df['date'].dt.month == 8)  & (df['date'].dt.day >= 18)  |
        df['date'].dt.month.isin([9, 10, 11]) |
        (df['date'].dt.month == 12) & (df['date'].dt.day <= 13) |
        (df['date'].dt.month == 1)  & (df['date'].dt.day >= 13)  |
        df['date'].dt.month.isin([2, 3, 4])
    ).astype(int)

    df['is_university_winter_break'] = (
        ((df['date'].dt.month == 12) & (df['date'].dt.day >= 14)) |
        ((df['date'].dt.month == 1)  & (df['date'].dt.day <= 12))
    ).astype(int)

    df['is_spring_break_university'] = (
        (df['date'].dt.month == 3) &
        (df['date'].dt.day >= 16) &
        (df['date'].dt.day <= 22)
    ).astype(int)

    df['is_finals_week'] = (
        ((df['date'].dt.month == 12) & (df['date'].dt.day >= 8)  & (df['date'].dt.day <= 13)) |
        ((df['date'].dt.month == 4)  & (df['date'].dt.day >= 22) & (df['date'].dt.day <= 30))
    ).astype(int)

    df['is_thanksgiving'] = (
        (df['date'].dt.month == 11) &
        (df['date'].dt.day >= 22) &
        (df['date'].dt.day <= 28) &
        (df['date'].dt.weekday == 3)
    ).astype(int)

    df['is_thanksgiving_saturday'] = (
        (df['date'].dt.month == 11) &
        (df['date'].dt.day >= 24) &
        (df['date'].dt.day <= 30) &
        (df['date'].dt.weekday == 5)
    ).astype(int)

    df['is_pioneer_day'] = ((df['date'].dt.month == 7) & (df['date'].dt.day == 24)).astype(int)

    df['is_back_to_school'] = (
        (df['date'].dt.month == 8) &
        (df['date'].dt.day >= 12) &
        (df['date'].dt.day <= 31)
    ).astype(int)

    df['is_spring_break_k12'] = (
        (df['date'].dt.month == 3) &
        (df['date'].dt.day >= 17) &
        (df['date'].dt.day <= 28)
    ).astype(int)

    df['is_fall_break_k12'] = (
        (df['date'].dt.month == 10) &
        (df['date'].dt.day >= 13) &
        (df['date'].dt.day <= 18)
    ).astype(int)

    df['is_university_thanksgiving_break'] = (
        (df['date'].dt.month == 11) &
        (df['date'].dt.day >= 24) &
        (df['date'].dt.day <= 30)
    ).astype(int)

    df['post_valentines_day'] = (
        (df['date'].dt.month == 2) &
        (df['date'].dt.day >= 14) &
        (df['date'].dt.day <= 21)
    ).astype(int)

    df['weather_cat'] = df['weather_code'].apply(get_weather_cat)

    df['is_rainy_day'] = (df['day_precip_sum'] > 0.05).astype(int)
    day_groups = df['is_rainy_day'].cumsum()
    df['days_since_last_rain'] = df.groupby(day_groups).cumcount()
    df.loc[df['is_rainy_day'] == 1, 'days_since_last_rain'] = 0

    df['precip_yesterday']  = df['day_precip_sum'].shift(1)
    df['precip_2days_ago']  = df['day_precip_sum'].shift(2)
    df['precip_3days_ago']  = df['day_precip_sum'].shift(3)
    df['precip_last_7days'] = df['day_precip_sum'].rolling(7).sum().shift(1)

    df['wind_yesterday']    = df['day_wind_max'].shift(1)
    df['wind_2days_ago']    = df['day_wind_max'].shift(2)
    df['wind_3days_ago']    = df['day_wind_max'].shift(3)
    df['rolling_7day_wind'] = df['day_wind_max'].rolling(7).mean().shift(1).round(1)
    df['rolling_3day_wind'] = df['day_wind_max'].rolling(3).mean().shift(1).round(1)

    df['rolling_7day_temp'] = df['day_temp_max'].rolling(window=7).mean().shift(1)

    month_mean = df.groupby(df['date'].dt.month)['hour_temp'].transform('mean')
    df['temp_anomaly'] = df['hour_temp'] - month_mean

    df['grocery_peak'] = ((df['day_num'] == 5) & (df['hour_of_day'].between(10, 14))).astype(int)
    df['commuter'] = ((df['day_num'] < 5) & (df['hour_of_day'] == 17)).astype(int)
    df['is_monday'] = (df['day_num'] == 0).astype(int)
    df['is_recovery_day'] = ((df['days_since_last_rain'] == 1) & (df['hour_temp'] > 32)).astype(int)
    df['pioneer_weekend'] = ((df['date'].dt.month == 7) & (df['date'].dt.day.between(24, 27))).astype(int)
    df['is_christmas_eve'] = ((df['date'].dt.month == 12) & (df['date'].dt.day == 24)).astype(int)
    df['is_heavy_holiday_shopping'] = ((df['date'].dt.month == 12) & (df['date'].dt.day.between(15, 23))).astype(int)
    df['is_january_reset'] = ((df['date'].dt.month == 1) & (df['date'].dt.day.between(5, 12)) & (df['day_num'].isin([4, 5]))).astype(int)
    df['is_pay_day'] = (df['date'].dt.day.isin([1, 15])).astype(int)
    df['is_upsell_weather'] = ((df['hour_temp'] > 60) & (df['hour_precip'] == 0)).astype(int)
    df['is_peak_holiday_shopping'] = ((df['date'].dt.month == 12) & (df['date'].dt.day.between(15, 23))).astype(int)
    df['is_first_thaw'] = ((df['date'].dt.month == 2) & (df['temp_anomaly'] > 15)).astype(int)
    df['is_jan_back_to_school'] = ((df['date'].dt.month == 1) & (df['date'].dt.day.between(5, 12))).astype(int)

    # hour_pct_of_day — safe cross-sectional calc
    day_hour_mean = df.groupby(['day_num', 'hour_of_day'])['car_count'].transform('mean')
    day_mean = df.groupby(['day_num'])['car_count'].transform('mean')
    df['hour_pct_of_day'] = (day_hour_mean / day_mean.replace(0, np.nan)).fillna(0)

    return df


FEATURES = [
    'hour_of_day', 'hour_sin', 'hour_cos', 'day_num',
    'hour_temp', 'hour_precip', 'hour_wind',
    'precip_yesterday', 'precip_last_7days',
    'days_since_last_rain',
    'is_holiday', 'is_day_after_holiday',
    'is_summer_break', 'is_university_in_session',
    'is_pre_christmas_rush', 'days_left_in_month',
    'month_sin', 'month_cos',
    'grocery_peak', 'commuter', 'is_monday', 'is_recovery_day',
    'pioneer_weekend', 'is_christmas_eve',
    'hour_pct_of_day', 'is_peak_holiday_shopping',
    'is_first_thaw', 'is_jan_back_to_school', 'is_pay_day',
    'weather_cat',
]


# ─────────────────────────────────────────────
# WEATHER FETCHING
# ─────────────────────────────────────────────
def fetch_historical_weather(start_date, end_date):
    params = {
        'latitude': LAT, 'longitude': LON,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'hourly': ['temperature_2m', 'precipitation', 'wind_speed_10m', 'weather_code'],
        'daily': ['temperature_2m_max', 'temperature_2m_min', 'precipitation_sum', 'wind_speed_10m_max'],
        'timezone': 'America/Denver',
        'temperature_unit': 'fahrenheit',
        'precipitation_unit': 'inch',
        'wind_speed_unit': 'mph'
    }
    r = requests.get('https://archive-api.open-meteo.com/v1/archive', params=params, timeout=30)
    return r.json()


def fetch_forecast_weather(start_date, end_date):
    params = {
        'latitude': LAT, 'longitude': LON,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'hourly': ['temperature_2m', 'precipitation', 'wind_speed_10m', 'weather_code'],
        'daily': ['temperature_2m_max', 'temperature_2m_min', 'precipitation_sum', 'wind_speed_10m_max'],
        'timezone': 'America/Denver',
        'temperature_unit': 'fahrenheit',
        'precipitation_unit': 'inch',
        'wind_speed_unit': 'mph'
    }
    r = requests.get('https://api.open-meteo.com/v1/forecast', params=params, timeout=30)
    return r.json()


def parse_weather(w_data):
    hourly = pd.DataFrame({
        'datetime': pd.to_datetime(w_data['hourly']['time']),
        'hour_temp': w_data['hourly']['temperature_2m'],
        'hour_precip': w_data['hourly']['precipitation'],
        'hour_wind': w_data['hourly']['wind_speed_10m'],
        'weather_code': w_data['hourly']['weather_code'],
    })
    daily = pd.DataFrame({
        'date': pd.to_datetime(w_data['daily']['time']),
        'day_temp_max': w_data['daily']['temperature_2m_max'],
        'day_precip_sum': w_data['daily']['precipitation_sum'],
        'day_wind_max': w_data['daily']['wind_speed_10m_max'],
    })
    return hourly, daily


# ─────────────────────────────────────────────
# MODEL TRAINING
# ─────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def train_model():
    from sklearn.ensemble import GradientBoostingRegressor

    # Load training data
    dfs = []
    for url in TRAINING_URLS:
        try:
            dfs.append(clean_and_tag_dates(url))
        except Exception as e:
            st.warning(f"Could not load training file: {e}")
    if not dfs:
        return None, None

    raw = pd.concat(dfs, ignore_index=True)

    # Basic prep
    col_map = {'Time Interval': 'time_interval', '# Cars (Total)': 'cars_total',
                '$ Sales (Total)': 'sales_total', 'Date': 'day'}
    raw = raw.rename(columns=col_map)
    raw['hour_of_day'] = raw['time_interval'].apply(parse_hour)
    raw['date'] = pd.to_datetime(raw['day'], errors='coerce')
    raw['datetime'] = raw['date'] + pd.to_timedelta(raw['hour_of_day'], unit='h')
    raw['car_count'] = pd.to_numeric(raw['cars_total'], errors='coerce').fillna(0)

    # Historical weather
    start_d = raw['date'].min()
    end_d   = raw['date'].max()
    w_data  = fetch_historical_weather(start_d, end_d)
    hourly_w, daily_w = parse_weather(w_data)

    raw = pd.merge(raw, hourly_w, on='datetime', how='left')
    raw = pd.merge(raw, daily_w, on='date', how='left')
    raw = raw.sort_values(['date', 'hour_of_day']).reset_index(drop=True)

    # Feature engineering
    raw = add_features(raw)

    # Filter
    df_model = raw[(raw['car_count'] > 2) & (raw['day_num'] != 6)].copy()
    df_model['car_count_smoothed'] = df_model['car_count'].rolling(window=2, min_periods=1).mean()
    df_model = df_model.dropna(subset=[f for f in FEATURES if f != 'weather_cat'])

    y = np.log1p(df_model['car_count_smoothed'])
    X = pd.get_dummies(df_model[FEATURES], drop_first=True)
    feature_cols = X.columns.tolist()

    max_date = df_model['date'].max()
    weights  = np.exp(-0.005 * (max_date - df_model['date']).dt.days)

    model = GradientBoostingRegressor(
        n_estimators=800, learning_rate=0.03, max_depth=6,
        min_samples_split=10, min_samples_leaf=5,
        subsample=0.7, random_state=42
    )
    model.fit(X, y, sample_weight=weights)

    return model, feature_cols


# ─────────────────────────────────────────────
# FORECAST GENERATION
# ─────────────────────────────────────────────
def generate_forecast(model, feature_cols, start_date, num_days=14):
    end_date   = start_date + timedelta(days=num_days - 1)
    # Fetch a few extra days before for lag features
    lag_start  = start_date - timedelta(days=10)

    try:
        # Combine archive + forecast
        today = datetime.now().date()
        if lag_start.date() < today:
            hist_end = min(start_date - timedelta(days=1), datetime.now() - timedelta(days=1))
            w_hist   = fetch_historical_weather(lag_start, hist_end)
            h_hist, d_hist = parse_weather(w_hist)
        else:
            h_hist, d_hist = pd.DataFrame(), pd.DataFrame()

        w_fore = fetch_forecast_weather(start_date, end_date)
        h_fore, d_fore = parse_weather(w_fore)

        hourly_w = pd.concat([h_hist, h_fore], ignore_index=True).drop_duplicates('datetime')
        daily_w  = pd.concat([d_hist, d_fore], ignore_index=True).drop_duplicates('date')
    except Exception as e:
        st.error(f"Weather fetch failed: {e}")
        return None

    # Build hourly rows for forecast window
    rows = []
    df = df[df['date'].dt.dayofweek != 6]
    for day_offset in range(num_days):
        d = start_date + timedelta(days=day_offset)
        for h in range(7, 21):  # 7am–8pm
            rows.append({'date': pd.Timestamp(d), 'hour_of_day': h,
                         'datetime': pd.Timestamp(d) + pd.to_timedelta(h, unit='h'),
                         'car_count': 0})
    df = df[df['date'].dt.dayofweek != 6]

    df = pd.DataFrame(rows)
    df = pd.merge(df, hourly_w, on='datetime', how='left')
    df = pd.merge(df, daily_w, on='date', how='left')

    # Fill NaN weather with reasonable defaults
    df['hour_temp']   = df['hour_temp'].fillna(60)
    df['hour_precip'] = df['hour_precip'].fillna(0)
    df['hour_wind']   = df['hour_wind'].fillna(10)
    df['weather_code']= df['weather_code'].fillna(0)
    df['day_temp_max']= df['day_temp_max'].fillna(65)
    df['day_precip_sum'] = df['day_precip_sum'].fillna(0)
    df['day_wind_max']   = df['day_wind_max'].fillna(12)

    df = df.sort_values(['date', 'hour_of_day']).reset_index(drop=True)
    df = add_features(df)
    df = df.fillna(0)

    # Predict
    X = pd.get_dummies(df[FEATURES], drop_first=True)
    X = X.reindex(columns=feature_cols, fill_value=0)
    preds = np.expm1(model.predict(X))
    preds = np.maximum(preds, 0)
    df['predicted_cars'] = preds.round(1)

    return df


# ─────────────────────────────────────────────
# STAFFING LOGIC
# ─────────────────────────────────────────────
def staffing_rec(cars_per_hour):
    if cars_per_hour < 8:
        return "🟢 Light", "badge badge-low", 1
    elif cars_per_hour < 15:
        return "🟡 Moderate", "badge badge-medium", 2
    elif cars_per_hour < 22:
        return "🟠 Busy", "badge badge-medium", 3
    else:
        return "🔴 Heavy", "badge badge-high", 4


def weather_note(row):
    notes = []
    if row.get('hour_precip', 0) > 0.1:
        notes.append("🌧 Active precipitation — expect lower traffic")
    if row.get('hour_temp', 70) < 32:
        notes.append("🧊 Freezing temps — possible slow period")
    if row.get('is_recovery_day', 0) == 1:
        notes.append("💧 Day after rain — expect surge in traffic")
    if row.get('is_holiday', 0) == 1:
        notes.append("🏖 Holiday — adjusted forecast applied")
    if row.get('is_day_after_holiday', 0) == 1:
        notes.append("📅 Day after holiday — possible rebound traffic")
    if row.get('days_since_last_rain', 0) >= 5:
        notes.append("☀️ Cars are getting dirty — above-average demand likely")
    return notes


# ─────────────────────────────────────────────
# PLOTLY THEME
# ─────────────────────────────────────────────
PLOT_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='IBM Plex Mono', color='#8892a4', size=11),
    margin=dict(l=10, r=10, t=30, b=10),
    xaxis=dict(gridcolor='#1e2535', linecolor='#252d3d', tickfont=dict(size=10)),
    yaxis=dict(gridcolor='#1e2535', linecolor='#252d3d', tickfont=dict(size=10)),
)


def hourly_bar_chart(day_df, selected_date):
    hours = day_df['hour_of_day'].tolist()
    cars  = day_df['predicted_cars'].tolist()

    colors = []
    for c in cars:
        if c < 8:   colors.append('#4ade80')
        elif c < 15: colors.append('#fbbf24')
        elif c < 22: colors.append('#fb923c')
        else:        colors.append('#f87171')

    hour_labels = []
    for h in hours:
        if h == 0: hour_labels.append('12am')
        elif h < 12: hour_labels.append(f'{h}am')
        elif h == 12: hour_labels.append('12pm')
        else: hour_labels.append(f'{h-12}pm')

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=hour_labels,
        y=cars,
        marker_color=colors,
        marker_line_width=0,
        text=[f'{int(c)}' for c in cars],
        textposition='outside',
        textfont=dict(color='#e8e4dc', size=10, family='IBM Plex Mono'),
        hovertemplate='<b>%{x}</b><br>%{y:.0f} cars<extra></extra>',
    ))

    fig.update_layout(
        **PLOT_LAYOUT,
        title=dict(text=f'Hourly Car Volume — {selected_date.strftime("%A, %b %d")}',
                   font=dict(color='#e8e4dc', size=14, family='Syne'), x=0.01, xanchor='left'),
        yaxis_title='Cars / Hour',
        bargap=0.25,
        showlegend=False,
        height=300,
    )
    return fig


def weekly_overview_chart(forecast_df):
    daily = forecast_df.groupby('date')['predicted_cars'].sum().reset_index()
    daily['day_label'] = pd.to_datetime(daily['date']).dt.strftime('%a\n%b %d')

    max_v = daily['predicted_cars'].max()

    colors = []
    for v in daily['predicted_cars']:
        ratio = v / max_v if max_v > 0 else 0
        if ratio > 0.75:   colors.append('#f87171')
        elif ratio > 0.5:  colors.append('#fb923c')
        elif ratio > 0.25: colors.append('#00c8ff')
        else:              colors.append('#4ade80')

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=daily['day_label'],
        y=daily['predicted_cars'],
        marker_color=colors,
        marker_line_width=0,
        text=[f'{int(v)}' for v in daily['predicted_cars']],
        textposition='outside',
        textfont=dict(color='#e8e4dc', size=10, family='IBM Plex Mono'),
        hovertemplate='<b>%{x}</b><br>%{y:.0f} cars total<extra></extra>',
    ))
    fig.update_layout(
        **PLOT_LAYOUT,
        title=dict(text='14-Day Volume Overview',
                   font=dict(color='#e8e4dc', size=14, family='Syne'), x=0.01, xanchor='left'),
        yaxis_title='Total Cars',
        bargap=0.3,
        showlegend=False,
        height=280,
    )
    return fig


def temp_vs_cars_scatter(day_df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=day_df['hour_temp'],
        y=day_df['predicted_cars'],
        mode='markers+text',
        marker=dict(
            color=day_df['predicted_cars'],
            colorscale=[[0, '#4ade80'], [0.5, '#fbbf24'], [1, '#f87171']],
            size=12, line=dict(width=0)),
        text=[f"{h-12 if h > 12 else h}{'pm' if h >= 12 else 'am'}" for h in day_df['hour_of_day']],
        textposition='top center',
        textfont=dict(color='#8892a4', size=9, family='IBM Plex Mono'),
        hovertemplate='<b>%{x:.0f}°F</b> → %{y:.0f} cars<extra></extra>',
    ))
    fig.update_layout(
        **PLOT_LAYOUT,
        title=dict(text='Temp vs Car Volume', font=dict(color='#e8e4dc', size=13, family='Syne'),
                   x=0.01, xanchor='left'),
        xaxis_title='Temperature (°F)',
        yaxis_title='Cars',
        height=260,
        showlegend=False,
    )
    return fig


def heatmap_chart(forecast_df):
    days   = sorted(forecast_df['date'].unique())
    hours  = list(range(7, 21))
    matrix = np.zeros((len(hours), len(days)))

    for di, d in enumerate(days):
        for hi, h in enumerate(hours):
            mask = (forecast_df['date'] == d) & (forecast_df['hour_of_day'] == h)
            vals = forecast_df.loc[mask, 'predicted_cars']
            if len(vals): matrix[hi, di] = vals.values[0]

    day_labels = [pd.Timestamp(d).strftime('%a %m/%d') for d in days]
    hour_labels = []
    for h in hours:
        if h < 12: hour_labels.append(f'{h}am')
        elif h == 12: hour_labels.append('12pm')
        else: hour_labels.append(f'{h-12}pm')

    fig = go.Figure(go.Heatmap(
        z=matrix, x=day_labels, y=hour_labels,
        colorscale=[[0,'#0d1117'],[0.25,'#1a3a2a'],[0.5,'#fbbf2480'],[0.75,'#fb923c'],[1,'#f87171']],
        hoverongaps=False,
        hovertemplate='<b>%{x} %{y}</b><br>%{z:.0f} cars<extra></extra>',
        showscale=True,
        colorbar=dict(
            tickfont=dict(color='#5a6478', family='IBM Plex Mono', size=10),
            outlinecolor='#252d3d', outlinewidth=1,
        )
    ))
    fig.update_layout(
        **PLOT_LAYOUT,
        title=dict(text='Traffic Heatmap — All 14 Days',
                   font=dict(color='#e8e4dc', size=14, family='Syne'), x=0.01, xanchor='left'),
        height=420,
        xaxis=dict(tickangle=-45, gridcolor='#1e2535', tickfont=dict(size=9)),
        yaxis=dict(autorange='reversed', gridcolor='#1e2535', tickfont=dict(size=9)),
    )
    return fig


# ─────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🚗 WiggyWash Forecast</h1>
        <p>LOCATION: UT0032 &nbsp;|&nbsp; MODEL: GRADIENT BOOSTING &nbsp;|&nbsp; WEATHER: OPEN-METEO LIVE</p>
    </div>
    """, unsafe_allow_html=True)

    # Controls
    col_date, col_days, col_btn = st.columns([2, 1, 1])
    with col_date:
        start_date = st.date_input(
            "Forecast Start Date",
            value=datetime.now().date(),
            label_visibility="visible",
            help="Pick the start of your 14-day forecast window"
        )
    with col_days:
        num_days = st.number_input("Days", min_value=3, max_value=14, value=14, step=1)
    with col_btn:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        run_btn = st.button("⚡ Run Forecast", use_container_width=True, type="primary")

    # State
    if 'forecast_df' not in st.session_state:
        st.session_state.forecast_df = None
    if 'selected_day' not in st.session_state:
        st.session_state.selected_day = None

    # Train + Forecast
    if run_btn or st.session_state.forecast_df is None:
        with st.spinner("Training model on historical data…"):
            model, feature_cols = train_model()

        if model is None:
            st.error("Could not load training data. Check network access.")
            return

        with st.spinner("Fetching 14-day weather forecast…"):
            start_dt = datetime(start_date.year, start_date.month, start_date.day)
            forecast_df = generate_forecast(model, feature_cols, start_dt, num_days=num_days)

        if forecast_df is None:
            st.error("Forecast generation failed.")
            return

        st.session_state.forecast_df = forecast_df
        st.session_state.selected_day = forecast_df['date'].min()

    forecast_df = st.session_state.forecast_df
    if forecast_df is None:
        return

    # ── Summary KPIs ──
    total_cars  = forecast_df['predicted_cars'].sum()
    peak_day    = forecast_df.groupby('date')['predicted_cars'].sum().idxmax()
    peak_hour_r = forecast_df.loc[forecast_df['predicted_cars'].idxmax()]
    avg_daily   = forecast_df.groupby('date')['predicted_cars'].sum().mean()

    ph = int(peak_hour_r['hour_of_day'])
    peak_hour_label = f"{ph-12 if ph > 12 else ph}{'pm' if ph >= 12 else 'am'}"

    k1, k2, k3, k4 = st.columns(4)
    metrics = [
        (f"{int(total_cars):,}", "Total Forecasted Cars"),
        (f"{int(avg_daily)}", "Avg Cars / Day"),
        (pd.Timestamp(peak_day).strftime("%a %b %d"), "Busiest Day"),
        (peak_hour_label, "Peak Hour"),
    ]
    for col, (val, label) in zip([k1, k2, k3, k4], metrics):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="value">{val}</div>
                <div class="label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    # ── Weekly Bar Chart ──
    st.plotly_chart(weekly_overview_chart(forecast_df), use_container_width=True)

    # ── Day Selector ──
    st.markdown('<div class="section-title">Select a Day for Hourly Detail</div>', unsafe_allow_html=True)

    days   = sorted(forecast_df['date'].unique())
    daily  = forecast_df.groupby('date')['predicted_cars'].sum()
    max_dc = daily.max()

    # Paginate: show 7 days at a time
    page = st.session_state.get('day_page', 0)
    chunk_size = 7
    pages = [days[i:i+chunk_size] for i in range(0, len(days), chunk_size)]
    if page >= len(pages): page = 0

    if len(pages) > 1:
        pcol1, _, pcol2 = st.columns([1, 6, 1])
        with pcol1:
            if st.button("◀ Prev", disabled=(page == 0)):
                st.session_state.day_page = page - 1
                st.rerun()
        with pcol2:
            if st.button("Next ▶", disabled=(page == len(pages)-1)):
                st.session_state.day_page = page + 1
                st.rerun()

    visible_days = pages[page] if pages else days

    cols = st.columns(len(visible_days))
    for i, d in enumerate(visible_days):
        with cols[i]:
            ts = pd.Timestamp(d)
            day_cars = daily.get(d, 0)
            bar_w    = int(100 * day_cars / max_dc) if max_dc > 0 else 0
            is_sel   = (st.session_state.selected_day == d)
            card_cls = "day-card selected" if is_sel else "day-card"

            st.markdown(f"""
            <div class="{card_cls}" id="card_{i}">
                <div class="day-name">{ts.strftime('%A')}</div>
                <div class="day-date">{ts.strftime('%b %d')}</div>
                <div class="day-cars">{int(day_cars)}</div>
                <div class="day-bar" style="width:{bar_w}%"></div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("View", key=f"day_btn_{i}", use_container_width=True):
                st.session_state.selected_day = d
                st.rerun()

    # ── Hourly Detail ──
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    selected_day = st.session_state.selected_day
    if selected_day is not None:
        day_df = forecast_df[forecast_df['date'] == selected_day].copy()
        sel_ts = pd.Timestamp(selected_day)

        st.markdown(f'<div class="section-title">Hourly Breakdown — {sel_ts.strftime("%A, %B %d, %Y")}</div>',
                    unsafe_allow_html=True)

        # Alerts
        day_row = day_df.iloc[0] if len(day_df) else {}
        alerts  = weather_note(day_row) if len(day_df) else []
        if alerts:
            for a in alerts:
                st.markdown(f'<div class="alert-box">{a}</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        # Main hourly bar
        st.plotly_chart(hourly_bar_chart(day_df, sel_ts), use_container_width=True)

        # Staffing table + scatter
        left, right = st.columns([3, 2])

        with left:
            st.markdown('<div class="section-title" style="font-size:0.85rem">Staffing Guide</div>',
                        unsafe_allow_html=True)

            hour_rows = []
            for _, row in day_df.iterrows():
                h = int(row['hour_of_day'])
                lbl = f"{h-12 if h > 12 else h}{'pm' if h >= 12 else 'am'}"
                cars = row['predicted_cars']
                status, badge_cls, staff = staffing_rec(cars)
                hour_rows.append({
                    'Hour': lbl,
                    'Predicted Cars': int(cars),
                    'Status': status,
                    'Recommended Staff': staff,
                })

            staff_df = pd.DataFrame(hour_rows)

            # Color the dataframe
            def color_status(val):
                if '🟢' in str(val): return 'color: #4ade80'
                if '🟡' in str(val): return 'color: #fbbf24'
                if '🟠' in str(val): return 'color: #fb923c'
                if '🔴' in str(val): return 'color: #f87171'
                return ''

            styled = staff_df.style.applymap(color_status, subset=['Status'])
            st.dataframe(styled, use_container_width=True, hide_index=True, height=380)

        with right:
            st.plotly_chart(temp_vs_cars_scatter(day_df), use_container_width=True)

            # Mini weather summary
            avg_temp = day_df['hour_temp'].mean()
            max_wind = day_df['hour_wind'].max()
            total_p  = day_df['hour_precip'].sum()
            wcat     = day_df['weather_cat'].mode()[0] if len(day_df) else 'clear'

            wcat_icon = {'clear': '☀️', 'rain': '🌧', 'snow': '❄️', 'other': '🌥'}.get(wcat, '🌥')

            st.markdown(f"""
            <div style="background:#141820;border:1px solid #252d3d;border-radius:12px;padding:1rem 1.25rem;margin-top:0.5rem;">
                <div style="font-size:0.7rem;color:#5a6478;font-family:'IBM Plex Mono';letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.75rem">Weather Summary</div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;">
                    <div><div style="font-size:1.4rem;font-weight:800;color:#00c8ff">{avg_temp:.0f}°F</div><div style="font-size:0.7rem;color:#5a6478;font-family:'IBM Plex Mono'">AVG TEMP</div></div>
                    <div><div style="font-size:1.4rem;font-weight:800;color:#7b61ff">{max_wind:.0f} mph</div><div style="font-size:0.7rem;color:#5a6478;font-family:'IBM Plex Mono'">MAX WIND</div></div>
                    <div><div style="font-size:1.4rem;font-weight:800;color:#4ade80">{total_p:.2f}"</div><div style="font-size:0.7rem;color:#5a6478;font-family:'IBM Plex Mono'">PRECIP</div></div>
                    <div><div style="font-size:1.8rem">{wcat_icon}</div><div style="font-size:0.7rem;color:#5a6478;font-family:'IBM Plex Mono'">{wcat.upper()}</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Full Heatmap ──
    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    st.plotly_chart(heatmap_chart(forecast_df), use_container_width=True)

    # ── Raw Data Toggle ──
    with st.expander("📋 Raw Forecast Data"):
        show_df = forecast_df[['date', 'hour_of_day', 'predicted_cars',
                                'hour_temp', 'hour_precip', 'hour_wind', 'weather_cat']].copy()
        show_df['date'] = show_df['date'].astype(str)
        show_df.columns = ['Date', 'Hour', 'Predicted Cars', 'Temp (°F)', 'Precip (in)', 'Wind (mph)', 'Conditions']
        st.dataframe(show_df, use_container_width=True, hide_index=True)

    # Footer
    st.markdown("""
    <div style="margin-top:3rem;padding-top:1.5rem;border-top:1px solid #1e2535;text-align:center;
    font-family:'IBM Plex Mono';font-size:0.72rem;color:#2e3848;letter-spacing:0.08em;">
        WIGGYWASH INTELLIGENCE PLATFORM &nbsp;|&nbsp; POWERED BY OPEN-METEO + GRADIENT BOOSTING
    </div>
    """, unsafe_allow_html=True)


if __name__ == '__main__':
    main()
