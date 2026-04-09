import streamlit as st
import pandas as pd
import numpy as np
import requests
import pickle
import datetime
import os
import pickle
import joblib
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="CarWash Intelligence",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg:      #0d0f12;
    --surface: #161a1f;
    --surface2:#1e2329;
    --border:  #2a2f38;
    --accent:  #00e5ff;
    --accent2: #ff6b35;
    --text:    #e8eaed;
    --muted:   #8a9099;
    --green:   #00c896;
    --yellow:  #ffd24c;
    --red:     #ff4d6d;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] * { color: var(--text) !important; }
h1, h2, h3 { font-family: 'Bebas Neue', sans-serif !important; letter-spacing: 0.04em; }

.metric-card {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-top: 3px solid var(--accent);
    border-radius: 8px;
    padding: 20px 24px;
    margin-bottom: 12px;
}
.metric-card.warn   { border-top-color: var(--yellow); }
.metric-card.danger { border-top-color: var(--red); }
.metric-card.good   { border-top-color: var(--green); }

.metric-value {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.8rem;
    color: var(--accent);
    line-height: 1;
}
.metric-value.warn   { color: var(--yellow); }
.metric-value.good   { color: var(--green); }
.metric-value.danger { color: var(--red); }
.metric-label {
    font-size: 0.72rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-top: 4px;
}
.metric-sub { font-size: 0.82rem; color: var(--muted); margin-top: 6px; }

.hour-pill {
    display: inline-block;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 8px 12px;
    margin: 4px;
    text-align: center;
    min-width: 80px;
}
.hour-pill .hp-time { font-size: 0.68rem; color: var(--muted); }
.hour-pill .hp-val  { font-family: 'DM Mono', monospace; font-size: 1.1rem; font-weight: 500; }

.section-header {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.4rem;
    color: var(--accent);
    letter-spacing: 0.06em;
    border-bottom: 1px solid var(--border);
    padding-bottom: 8px;
    margin: 24px 0 16px;
}

[data-testid="stSelectbox"] > div,
[data-testid="stDateInput"] > div {
    background: var(--surface2) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
}
div[data-testid="stButton"] > button {
    background: var(--accent) !important;
    color: #000 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 6px !important;
}
.stSpinner > div { border-top-color: var(--accent) !important; }
.stAlert { background: var(--surface2) !important; border-color: var(--border) !important; }
footer { display: none !important; }
#MainMenu { display: none !important; }
header  { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────
HOLIDAYS = pd.to_datetime([
    '2025-01-01','2025-01-20','2025-02-17','2025-05-26','2025-06-19','2025-07-04',
    '2025-09-01','2025-10-13','2025-11-11','2025-11-27','2025-12-25',
    '2026-01-01','2026-01-19','2026-02-16','2026-05-25','2026-06-19','2026-07-03',
    '2026-09-07','2026-10-12','2026-11-11','2026-11-26','2026-12-25',
])
DAYS_AFTER_HOLIDAYS = HOLIDAYS + pd.to_timedelta(1, unit='D')

WMO_CATS = {
    range(0,  3):  'clear',
    range(3,  9):  'cloudy',
    range(10, 30): 'drizzle',
    range(30, 40): 'fog',
    range(40, 60): 'drizzle',
    range(60, 70): 'rain',
    range(70, 80): 'snow',
    range(80, 90): 'showers',
    range(90, 100):'storm',
}

HOUR_PCT = {
    0:0.01, 1:0.00, 2:0.00, 3:0.00, 4:0.00, 5:0.01,
    6:0.03, 7:0.05, 8:0.07, 9:0.08, 10:0.09, 11:0.09,
    12:0.08,13:0.08,14:0.08,15:0.08,16:0.08,17:0.09,
    18:0.07,19:0.05,20:0.03,21:0.02,22:0.01,23:0.01,
}

PLOT_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='DM Sans', color='#8a9099', size=12),
    xaxis=dict(gridcolor='#2a2f38', zerolinecolor='#2a2f38'),
    yaxis=dict(gridcolor='#2a2f38', zerolinecolor='#2a2f38'),
    margin=dict(l=0, r=0, t=30, b=0),
)

# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
def get_weather_cat(code):
    """Map WMO weather code integer to a category string."""
    try:
        if pd.isna(code):
            return 'clear'
    except (TypeError, ValueError):
        pass
    code = int(code)
    for rng, cat in WMO_CATS.items():
        if code in rng:
            return cat
    return 'clear'

def weather_emoji(cat):
    return {
        'clear':'☀️','cloudy':'☁️','drizzle':'🌦️','fog':'🌫️',
        'rain':'🌧️','snow':'❄️','showers':'🌨️','storm':'⛈️',
    }.get(cat, '🌤️')

def get_model_feature_names(model):
    """
    FIX: Safely extract feature names from a raw model OR a sklearn Pipeline.
    Returns a list of str, or None if unavailable.
    """
    if hasattr(model, 'feature_names_in_'):
        return list(model.feature_names_in_)
    # Walk sklearn Pipeline named_steps (last step first)
    if hasattr(model, 'named_steps'):
        for step in reversed(list(model.named_steps.values())):
            if hasattr(step, 'feature_names_in_'):
                return list(step.feature_names_in_)
            if hasattr(step, 'get_booster'):
                try:
                    return list(step.get_booster().feature_names)
                except Exception:
                    pass
    return None

# ─────────────────────────────────────────
# WEATHER FETCH
# FIX: Archive API has a ~2-day data lag — use it only for history.
#      Today and all future dates must use the forecast API.
# ─────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_weather_archive(start_date: str, end_date: str):
    params = {
        'latitude': 40.1618, 'longitude': -111.6348,
        'start_date': start_date, 'end_date': end_date,
        'hourly': ['temperature_2m','precipitation','wind_speed_10m','weather_code'],
        'daily':  ['temperature_2m_max','temperature_2m_min','precipitation_sum','wind_speed_10m_max'],
        'timezone': 'America/Denver',
        'temperature_unit': 'fahrenheit',
        'precipitation_unit': 'inch',
        'wind_speed_unit': 'mph',
    }
    r = requests.get('https://archive-api.open-meteo.com/v1/archive', params=params, timeout=20)
    r.raise_for_status()
    return r.json()

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_weather_forecast(start_date: str, end_date: str):
    params = {
        'latitude': 40.1618, 'longitude': -111.6348,
        'start_date': start_date, 'end_date': end_date,
        'hourly': ['temperature_2m','precipitation','wind_speed_10m','weather_code'],
        'daily':  ['temperature_2m_max','temperature_2m_min','precipitation_sum','wind_speed_10m_max'],
        'timezone': 'America/Denver',
        'temperature_unit': 'fahrenheit',
        'precipitation_unit': 'inch',
        'wind_speed_unit': 'mph',
        'forecast_days': 16,
    }
    r = requests.get('https://api.open-meteo.com/v1/forecast', params=params, timeout=20)
    r.raise_for_status()
    return r.json()

def parse_weather_json(w: dict):
    """
    Parse Open-Meteo JSON into (hourly_df, daily_df).
    FIX: Both archive and forecast APIs return the key 'time' (not 'date').
         We always rename it explicitly so downstream merges work correctly.
    """
    hourly = pd.DataFrame({
        'datetime':    pd.to_datetime(w['hourly']['time']),
        'hour_temp':   w['hourly']['temperature_2m'],
        'hour_precip': w['hourly']['precipitation'],
        'hour_wind':   w['hourly']['wind_speed_10m'],
        'weather_code':w['hourly']['weather_code'],
    })
    hourly['date'] = hourly['datetime'].dt.normalize()   # FIX: derive 'date' from 'datetime'

    daily = pd.DataFrame({
        'date':          pd.to_datetime(w['daily']['time']).normalize(),  # FIX: rename 'time' → 'date'
        'day_temp_max':  w['daily']['temperature_2m_max'],
        'day_precip_sum':w['daily']['precipitation_sum'],
        'day_wind_max':  w['daily']['wind_speed_10m_max'],
    })

    # FIX: use .ffill()/.bfill() instead of deprecated fillna(method=...)
    daily['day_precip_sum'] = daily['day_precip_sum'].fillna(0.0)
    daily['day_temp_max']   = daily['day_temp_max'].ffill().bfill().fillna(50.0)
    daily['day_wind_max']   = daily['day_wind_max'].ffill().bfill().fillna(5.0)

    hourly['hour_precip']  = hourly['hour_precip'].fillna(0.0)
    hourly['hour_temp']    = hourly['hour_temp'].ffill().bfill().fillna(50.0)
    hourly['hour_wind']    = hourly['hour_wind'].ffill().bfill().fillna(5.0)
    hourly['weather_code'] = hourly['weather_code'].ffill().bfill().fillna(0)

    return hourly, daily

@st.cache_resource(show_spinner=False)

def load_model():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(BASE_DIR, "pipeline.pkl")

    return joblib.load(model_path)

# ─────────────────────────────────────────
# FEATURE ENGINEERING
# ─────────────────────────────────────────
def build_features(df_day: pd.DataFrame, df_hist_daily: pd.DataFrame) -> pd.DataFrame:
    """
    Build all model features for a single day (24 hourly rows).
    df_day        — 24 rows: hour_of_day, date, datetime, hour_temp,
                    hour_precip, hour_wind, weather_code, day_temp_max,
                    day_precip_sum, day_wind_max
    df_hist_daily — historical daily weather for lag calculations
    """
    d = df_day.copy()
    d['date'] = pd.to_datetime(d['date'])       # ensure Timestamp, not object
    date = pd.Timestamp(d['date'].iloc[0])

    # ── Cyclical time ──
    d['hour_sin']  = np.sin(2 * np.pi * d['hour_of_day'] / 24)
    d['hour_cos']  = np.cos(2 * np.pi * d['hour_of_day'] / 24)
    d['day_num']   = date.dayofweek
    d['month_sin'] = np.sin(2 * np.pi * date.month / 12)
    d['month_cos'] = np.cos(2 * np.pi * date.month / 12)

    # ── Daily lag helper ──
    def lag_daily(col, days):
        target = date - pd.Timedelta(days=days)
        rows = df_hist_daily[df_hist_daily['date'] == target]
        return float(rows[col].iloc[0]) if len(rows) else 0.0

    d['precip_yesterday'] = lag_daily('day_precip_sum', 1)
    d['precip_2days_ago'] = lag_daily('day_precip_sum', 2)
    d['precip_3days_ago'] = lag_daily('day_precip_sum', 3)
    d['wind_yesterday']   = lag_daily('day_wind_max', 1)
    d['wind_2days_ago']   = lag_daily('day_wind_max', 2)
    d['wind_3days_ago']   = lag_daily('day_wind_max', 3)

    # ── Rolling windows ──
    recent7 = df_hist_daily.tail(7)
    recent3 = df_hist_daily.tail(3)
    d['precip_last_7days'] = float(recent7['day_precip_sum'].sum())  if len(recent7) else 0.0
    d['rolling_7day_wind'] = round(float(recent7['day_wind_max'].mean()), 1) if len(recent7) else 0.0
    d['rolling_3day_wind'] = round(float(recent3['day_wind_max'].mean()), 1) if len(recent3) else 0.0
    d['rolling_7day_temp'] = round(float(recent7['day_temp_max'].mean()), 1) if len(recent7) else 60.0

    # ── Days since last rain ──
    rain_days = df_hist_daily[df_hist_daily['day_precip_sum'] > 0.05]['date']
    d['days_since_last_rain'] = int((date - rain_days.max()).days) if len(rain_days) else 30

    # ── Temp anomaly ──
    month_hist = df_hist_daily[df_hist_daily['date'].dt.month == date.month]
    month_mean = float(month_hist['day_temp_max'].mean()) if len(month_hist) else float(d['hour_temp'].mean())
    d['temp_anomaly'] = d['hour_temp'] - month_mean

    # ── Holiday flags ──
    ts = date
    d['is_holiday']           = int(ts in HOLIDAYS)
    d['is_day_after_holiday'] = int(ts in DAYS_AFTER_HOLIDAYS)

    m, dy, dw = date.month, date.day, date.weekday()

    d['is_christmas_week']               = int(m == 12 and dy >= 23)
    d['is_christmas_season']             = int(m == 12 and dy >= 15)
    d['is_new_years_week']               = int(m == 1  and dy <= 7)
    d['is_holiday_week']                 = int((m == 12 and dy >= 23) or (m == 1 and dy <= 7))
    d['is_pre_christmas_rush']           = int(m == 12 and 15 <= dy <= 22)
    d['is_post_christmas_slow']          = int((m == 12 and dy >= 26) or (m == 1 and dy <= 3))
    d['is_early_december']               = int(m == 12 and dy <= 14)
    d['is_post_thanksgiving']            = int(m == 11 and 28 <= dy <= 30)
    d['days_left_in_month']              = ts.days_in_month - dy
    d['is_thanksgiving']                 = int(m == 11 and 22 <= dy <= 28 and dw == 3)
    d['is_thanksgiving_saturday']        = int(m == 11 and 24 <= dy <= 30 and dw == 5)
    d['is_pioneer_day']                  = int(m == 7  and dy == 24)
    d['is_back_to_school']               = int(m == 8  and 12 <= dy <= 31)
    d['post_valentines_day']             = int(m == 2  and 14 <= dy <= 21)
    d['is_summer_break']                 = int(m in [6,7] or (m==5 and dy>=27) or (m==8 and dy<=18))
    d['is_spring_break_k12']             = int(m == 3  and 17 <= dy <= 28)
    d['is_fall_break_k12']               = int(m == 10 and 13 <= dy <= 18)
    d['is_university_in_session']        = int(
        (m==8 and dy>=18) or m in [9,10,11] or (m==12 and dy<=13) or
        (m==1 and dy>=13) or m in [2,3,4]
    )
    d['is_university_winter_break']      = int((m==12 and dy>=14) or (m==1 and dy<=12))
    d['is_spring_break_university']      = int(m==3 and 16<=dy<=22)
    d['is_finals_week']                  = int((m==12 and 8<=dy<=13) or (m==4 and 22<=dy<=30))
    d['is_university_thanksgiving_break']= int(m==11 and 24<=dy<=30)
    d['is_heavy_holiday_shopping']       = int(m==12 and 15<=dy<=23)
    d['is_january_reset']                = int(m==1 and 5<=dy<=12 and dw in [4,5])
    d['is_pay_day']                      = int(dy in [1,15])
    d['pioneer_weekend']                 = int(m==7 and 24<=dy<=27)
    d['is_christmas_eve']                = int(m==12 and dy==24)
    d['is_peak_holiday_shopping']        = int(m==12 and 15<=dy<=23)
    d['is_jan_back_to_school']           = int(m==1 and 5<=dy<=12)

    # FIX: is_first_thaw must be a Series, not a bare int, to assign to a column
    d['is_first_thaw'] = (d['temp_anomaly'] > 15).astype(int) if m == 2 else 0

    # ── Hourly interaction features ──
    d['is_upsell_weather'] = ((d['hour_temp'] > 60) & (d['hour_precip'] == 0)).astype(int)
    d['is_recovery_day']   = ((d['days_since_last_rain'] == 1) & (d['hour_temp'] > 32)).astype(int)
    d['grocery_peak']      = ((d['day_num'] == 5) & (d['hour_of_day'].between(10, 14))).astype(int)
    d['commuter']          = ((d['day_num'] < 5)  & (d['hour_of_day'] == 17)).astype(int)
    d['is_monday']         = int(d['day_num'].iloc[0] == 0)

    d['weather_cat']       = d['weather_code'].apply(get_weather_cat)
    d['hour_pct_of_day']   = d['hour_of_day'].map(HOUR_PCT).fillna(0.04)

    return d


def predict_day(model, df_day_feat: pd.DataFrame) -> np.ndarray:
    """Run model inference. Handles raw estimators and sklearn Pipelines."""
    FEATURE_COLS = [
        'hour_of_day','hour_sin','hour_cos','day_num','month_sin','month_cos',
        'hour_temp','hour_precip','hour_wind','day_temp_max','day_precip_sum','day_wind_max',
        'precip_yesterday','precip_2days_ago','precip_3days_ago','precip_last_7days',
        'wind_yesterday','wind_2days_ago','wind_3days_ago','rolling_7day_wind','rolling_3day_wind',
        'days_since_last_rain','rolling_7day_temp','temp_anomaly',
        'is_holiday','is_day_after_holiday','is_christmas_week','is_christmas_season',
        'is_new_years_week','is_holiday_week','is_pre_christmas_rush','is_post_christmas_slow',
        'is_early_december','is_post_thanksgiving','days_left_in_month',
        'is_thanksgiving','is_thanksgiving_saturday','is_pioneer_day','is_back_to_school',
        'post_valentines_day','is_summer_break','is_spring_break_k12','is_fall_break_k12',
        'is_university_in_session','is_university_winter_break','is_spring_break_university',
        'is_finals_week','is_university_thanksgiving_break','is_heavy_holiday_shopping',
        'is_january_reset','is_pay_day','is_upsell_weather','is_peak_holiday_shopping',
        'is_first_thaw','is_jan_back_to_school','pioneer_weekend','is_christmas_eve',
        'is_recovery_day','grocery_peak','commuter','is_monday','hour_pct_of_day',
        'weather_cat',
    ]
    available = [c for c in FEATURE_COLS if c in df_day_feat.columns]
    X = pd.get_dummies(df_day_feat[available], drop_first=True)

    # FIX: walk into Pipeline named_steps to find feature names
    known = get_model_feature_names(model)
    if known:
        for c in known:
            if c not in X.columns:
                X[c] = 0
        X = X[[c for c in known if c in X.columns]]

    raw = model.predict(X)

    # Invert log1p transform applied during training
    try:
        preds = np.expm1(raw)
    except Exception:
        preds = np.array(raw, dtype=float)

    return np.maximum(preds, 0).round(0)


# ─────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("<h1 style='font-size:1.6rem;color:#00e5ff;'>🚗 CarWash Intel</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#8a9099;font-size:0.8rem;margin-top:-8px;'>ML-Powered Volume Forecaster</p>", unsafe_allow_html=True)
    st.divider()

    view_mode = st.radio(
        "VIEW MODE",
        ["📅 Day Overview", "📆 7-Day Forecast", "🕐 Hourly Deep Dive"],
        label_visibility="visible",
    )
    st.divider()

    today = datetime.date.today()
    if view_mode in ["📅 Day Overview", "🕐 Hourly Deep Dive"]:
        selected_date = st.date_input(
            "SELECT DATE",
            value=today,
            min_value=today - datetime.timedelta(days=30),
            max_value=today + datetime.timedelta(days=14),
        )
    else:
        selected_date = today

    st.divider()
    run_btn = st.button("🔮 RUN FORECAST", use_container_width=True)
    st.markdown(
        "<p style='color:#8a9099;font-size:0.72rem;margin-top:8px;'>"
        "Weather: Open-Meteo API<br>Location: Rexburg, ID (40.16°N)</p>",
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────
# MAIN HEADER
# ─────────────────────────────────────────
st.markdown("<h1 style='font-size:2.4rem;margin-bottom:0;'>CARWASH INTELLIGENCE</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#8a9099;margin-top:-4px;margin-bottom:24px;'>Volume Forecast · Rexburg, ID</p>", unsafe_allow_html=True)

if not run_btn:
    st.markdown("""
    <div style='background:#161a1f;border:1px solid #2a2f38;border-radius:12px;padding:40px;text-align:center;'>
        <div style='font-size:3rem;margin-bottom:12px;'>🚗</div>
        <div style='font-family:Bebas Neue,sans-serif;font-size:1.8rem;color:#00e5ff;'>READY TO FORECAST</div>
        <div style='color:#8a9099;margin-top:8px;'>Select a date and click RUN FORECAST to see predictions powered by your ML model.</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────
# LOAD MODEL
# ─────────────────────────────────────────
try:
    model = load_model()
except FileNotFoundError:
    st.error("❌ **pipeline.pkl not found.** Place it in the same directory as this app.")
    st.stop()
except Exception as e:
    st.error(f"❌ Failed to load model: {e}")
    st.stop()

# ─────────────────────────────────────────
# FETCH WEATHER
# FIX: Archive API lags ~2 days — use 3-day buffer.
#      Today and future always use the forecast API.
# ─────────────────────────────────────────
with st.spinner("Fetching weather data..."):
    try:
        arch_end   = today - datetime.timedelta(days=3)
        arch_start = today - datetime.timedelta(days=33)

        w_arch = fetch_weather_archive(
            arch_start.strftime('%Y-%m-%d'),
            arch_end.strftime('%Y-%m-%d'),
        )
        hist_hourly, df_hist_daily = parse_weather_json(w_arch)

        # Forecast API: covers today → today+14
        w_fcast = fetch_weather_forecast(
            today.strftime('%Y-%m-%d'),
            (today + datetime.timedelta(days=14)).strftime('%Y-%m-%d'),
        )
        fcast_hourly, fcast_daily = parse_weather_json(w_fcast)

        if view_mode == "📆 7-Day Forecast":
            target_dates = [today + datetime.timedelta(days=i) for i in range(7)]
        else:
            target_dates = [selected_date]

    except requests.HTTPError as e:
        st.error(f"❌ Weather API HTTP error {e.response.status_code}: {e.response.text[:300]}")
        st.stop()
    except Exception as e:
        st.error(f"❌ Weather API error: {e}")
        st.stop()

# ─────────────────────────────────────────
# BUILD PREDICTIONS
# ─────────────────────────────────────────
all_day_results = []

for tdate in target_dates:
    td = pd.Timestamp(tdate)

    hours = pd.DataFrame({
        'hour_of_day': range(24),
        'date':        td,
        'datetime':    [td + pd.Timedelta(hours=h) for h in range(24)],
    })

    # FIX: past dates use archive hourly; today/future use forecast hourly
    if tdate < today:
        src_hourly = hist_hourly
        src_daily  = df_hist_daily
    else:
        src_hourly = fcast_hourly
        src_daily  = fcast_daily

    hours = hours.merge(
        src_hourly[['datetime','hour_temp','hour_precip','hour_wind','weather_code']],
        on='datetime', how='left',
    )

    daily_row = src_daily[src_daily['date'] == td]
    if len(daily_row):
        hours['day_temp_max']   = float(daily_row['day_temp_max'].iloc[0])
        hours['day_precip_sum'] = float(daily_row['day_precip_sum'].iloc[0])
        hours['day_wind_max']   = float(daily_row['day_wind_max'].iloc[0])
    else:
        hours['day_temp_max']   = hours['hour_temp'].max()
        hours['day_precip_sum'] = hours['hour_precip'].sum()
        hours['day_wind_max']   = hours['hour_wind'].max()

    # FIX: only ffill/bfill numeric columns to avoid dtype warnings on date/datetime cols
    num_cols = hours.select_dtypes(include=[np.number]).columns
    hours[num_cols] = hours[num_cols].ffill().bfill().fillna(0.0)

    feat  = build_features(hours, df_hist_daily)
    preds = predict_day(model, feat)
    feat['predicted_cars'] = preds
    all_day_results.append(feat)

results_df = pd.concat(all_day_results, ignore_index=True)

# ═══════════════════════════════════════════════
# VIEW: DAY OVERVIEW
# ═══════════════════════════════════════════════
if view_mode == "📅 Day Overview":
    day_df = results_df[results_df['date'] == pd.Timestamp(selected_date)].copy()
    if day_df.empty:
        st.warning("No prediction data for the selected date.")
        st.stop()

    total_cars   = int(day_df['predicted_cars'].sum())
    peak_idx     = day_df['predicted_cars'].idxmax()
    peak_hour    = int(day_df.loc[peak_idx, 'hour_of_day'])
    peak_vol     = int(day_df['predicted_cars'].max())
    avg_temp     = float(day_df['hour_temp'].mean())
    precip_total = float(day_df['hour_precip'].sum())

    # FIX: guard against empty mode result
    mode_vals = day_df['weather_code'].mode()
    wx_cat = get_weather_cat(mode_vals.iloc[0]) if len(mode_vals) else 'clear'

    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        rating = "good" if total_cars > 200 else ("warn" if total_cars > 100 else "danger")
        st.markdown(f"""<div class='metric-card {rating}'>
            <div class='metric-value {rating}'>{total_cars}</div>
            <div class='metric-label'>Total Cars Today</div>
            <div class='metric-sub'>{selected_date.strftime('%A, %b %d')}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class='metric-card'>
            <div class='metric-value'>{peak_hour:02d}:00</div>
            <div class='metric-label'>Peak Hour</div>
            <div class='metric-sub'>{peak_vol} cars expected</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        t_cls = "danger" if avg_temp < 32 else ("warn" if avg_temp < 50 else "good")
        st.markdown(f"""<div class='metric-card {t_cls}'>
            <div class='metric-value {t_cls}'>{avg_temp:.0f}°</div>
            <div class='metric-label'>Avg Temperature (°F)</div>
            <div class='metric-sub'>High {day_df['day_temp_max'].iloc[0]:.0f}°F</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        w_cls = "danger" if precip_total > 0.1 else ("warn" if precip_total > 0 else "good")
        st.markdown(f"""<div class='metric-card {w_cls}'>
            <div class='metric-value {w_cls}'>{weather_emoji(wx_cat)}</div>
            <div class='metric-label'>Conditions</div>
            <div class='metric-sub'>{wx_cat.capitalize()} · {precip_total:.2f}" precip</div>
        </div>""", unsafe_allow_html=True)

    # Hourly bar chart
    st.markdown("<div class='section-header'>HOURLY VOLUME FORECAST</div>", unsafe_allow_html=True)
    avg_cars   = float(day_df['predicted_cars'].mean())
    bar_colors = ['#ff4d6d' if h == peak_hour else '#00e5ff' for h in day_df['hour_of_day']]

    fig = go.Figure(go.Bar(
        x=day_df['hour_of_day'],
        y=day_df['predicted_cars'],
        marker_color=bar_colors,
        hovertemplate='<b>%{x}:00</b><br>%{y:.0f} cars<extra></extra>',
        text=day_df['predicted_cars'].astype(int),
        textposition='outside',
        textfont=dict(size=10, color='#8a9099'),
    ))
    fig.add_shape(
        type='line', x0=-0.5, x1=23.5,
        y0=avg_cars, y1=avg_cars,
        line=dict(color='#ffd24c', dash='dot', width=1.5),
    )
    fig.add_annotation(
        x=22, y=avg_cars + max(avg_cars * 0.05, 0.5),
        text=f"avg {avg_cars:.1f}",
        font=dict(color='#ffd24c', size=10), showarrow=False,
    )
    fig.update_layout(
        **PLOT_LAYOUT, height=340,
        xaxis_title='Hour of Day', yaxis_title='Predicted Cars',
        xaxis=dict(tickmode='linear', dtick=1, gridcolor='#2a2f38', zerolinecolor='#2a2f38'),
        yaxis=dict(gridcolor='#2a2f38', zerolinecolor='#2a2f38'),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Temp / Precip overlay
    st.markdown("<div class='section-header'>TEMPERATURE & PRECIPITATION</div>", unsafe_allow_html=True)
    fig2 = make_subplots(specs=[[{"secondary_y": True}]])
    fig2.add_trace(go.Scatter(
        x=day_df['hour_of_day'], y=day_df['hour_temp'],
        name='Temp (°F)', line=dict(color='#ff6b35', width=2),
        fill='tozeroy', fillcolor='rgba(255,107,53,0.08)',
    ), secondary_y=False)
    fig2.add_trace(go.Bar(
        x=day_df['hour_of_day'], y=day_df['hour_precip'],
        name='Precip (in)', marker_color='rgba(0,229,255,0.4)',
    ), secondary_y=True)
    fig2.update_layout(
        **PLOT_LAYOUT, height=220, showlegend=True,
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='#8a9099')),
    )
    fig2.update_yaxes(title_text="Temp °F",   secondary_y=False, gridcolor='#2a2f38', zerolinecolor='#2a2f38')
    fig2.update_yaxes(title_text="Precip in", secondary_y=True,  gridcolor='#2a2f38', zerolinecolor='#2a2f38')
    st.plotly_chart(fig2, use_container_width=True)

    # Staffing guide
    st.markdown("<div class='section-header'>STAFFING GUIDE</div>", unsafe_allow_html=True)
    sc1, sc2, sc3 = st.columns(3)
    morning   = int(day_df[day_df['hour_of_day'].between(6,  11)]['predicted_cars'].sum())
    afternoon = int(day_df[day_df['hour_of_day'].between(12, 17)]['predicted_cars'].sum())
    evening   = int(day_df[day_df['hour_of_day'].between(18, 21)]['predicted_cars'].sum())

    for col, label, vol, icon in [
        (sc1, 'Morning Shift (6–11am)',   morning,   '🌅'),
        (sc2, 'Afternoon Shift (12–5pm)', afternoon, '☀️'),
        (sc3, 'Evening Shift (6–9pm)',    evening,   '🌆'),
    ]:
        staff = max(1, round(vol / 40))
        cls   = "good" if vol > 60 else ("warn" if vol > 30 else "")
        with col:
            st.markdown(f"""<div class='metric-card {cls}'>
                <div style='font-size:1.4rem'>{icon}</div>
                <div class='metric-value {cls}' style='font-size:2rem;'>{vol}</div>
                <div class='metric-label'>{label}</div>
                <div class='metric-sub'>Suggested staff: <b style='color:#00e5ff'>{staff}</b></div>
            </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════
# VIEW: 7-DAY FORECAST
# ═══════════════════════════════════════════════
elif view_mode == "📆 7-Day Forecast":
    st.markdown("<div class='section-header'>7-DAY VOLUME FORECAST</div>", unsafe_allow_html=True)

    # FIX: compute peak_hour separately — idxmax in groupby agg returns the
    #      global DataFrame index, not hour_of_day. We look it up explicitly.
    def get_peak_hour(date_val):
        sub = results_df[results_df['date'] == date_val]
        if sub.empty:
            return 12
        return int(sub.loc[sub['predicted_cars'].idxmax(), 'hour_of_day'])

    daily_summary = (
        results_df.groupby('date')
        .agg(
            total_cars=('predicted_cars', 'sum'),
            peak_cars =('predicted_cars', 'max'),
            avg_temp  =('hour_temp',      'mean'),
            max_temp  =('day_temp_max',   'first'),
            precip    =('hour_precip',    'sum'),
            weather_code=('weather_code', 'first'),
        )
        .reset_index()
    )
    daily_summary['peak_hour'] = daily_summary['date'].apply(get_peak_hour)
    daily_summary['wx_cat']    = daily_summary['weather_code'].apply(get_weather_cat)

    # Bar chart
    q75        = daily_summary['total_cars'].quantile(0.75)
    bar_colors = []
    for _, row in daily_summary.iterrows():
        if row['precip'] > 0.05:
            bar_colors.append('#4dabf7')
        elif row['total_cars'] >= q75:
            bar_colors.append('#00c896')
        else:
            bar_colors.append('#00e5ff')

    fig = go.Figure(go.Bar(
        x=daily_summary['date'].dt.strftime('%a %b %d'),
        y=daily_summary['total_cars'],
        marker_color=bar_colors,
        text=daily_summary['total_cars'].astype(int),
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Total: %{y:.0f} cars<extra></extra>',
    ))
    fig.update_layout(
        **PLOT_LAYOUT, height=300, yaxis_title='Total Cars',
        xaxis=dict(gridcolor='#2a2f38', zerolinecolor='#2a2f38'),
        yaxis=dict(gridcolor='#2a2f38', zerolinecolor='#2a2f38'),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Day cards
    q33 = daily_summary['total_cars'].quantile(0.33)
    q66 = daily_summary['total_cars'].quantile(0.66)
    cols = st.columns(7)
    for i, (_, row) in enumerate(daily_summary.iterrows()):
        with cols[i % 7]:
            vol = int(row['total_cars'])
            cls = "good" if vol >= q66 else ("warn" if vol >= q33 else "danger")
            st.markdown(f"""<div class='metric-card {cls}' style='padding:14px;text-align:center;'>
                <div style='font-size:1.4rem'>{weather_emoji(row['wx_cat'])}</div>
                <div style='font-family:Bebas Neue;font-size:1rem;color:#8a9099;'>
                    {row['date'].strftime('%a')} {row['date'].strftime('%d')}
                </div>
                <div class='metric-value {cls}' style='font-size:1.8rem;'>{vol}</div>
                <div class='metric-label'>cars</div>
                <div class='metric-sub'>{row['max_temp']:.0f}°F</div>
            </div>""", unsafe_allow_html=True)

    # Heatmap
    st.markdown("<div class='section-header'>HOURLY HEATMAP (ALL 7 DAYS)</div>", unsafe_allow_html=True)
    pivot = results_df.pivot_table(
        index='hour_of_day', columns='date',
        values='predicted_cars', aggfunc='sum',
    )
    pivot.columns = [c.strftime('%a %b %d') for c in pivot.columns]

    fig_heat = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=[f"{h:02d}:00" for h in pivot.index],
        colorscale=[[0,'#0d0f12'],[0.3,'#003d4d'],[0.7,'#007a99'],[1,'#00e5ff']],
        hovertemplate='<b>%{x}</b><br>%{y}<br>%{z:.0f} cars<extra></extra>',
        colorbar=dict(tickfont=dict(color='#8a9099'), outlinewidth=0),
    ))
    fig_heat.update_layout(
        **PLOT_LAYOUT, height=500,
        yaxis=dict(autorange='reversed', gridcolor='#2a2f38'),
        xaxis=dict(gridcolor='#2a2f38'),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    # Summary table
    st.markdown("<div class='section-header'>DAILY SUMMARY TABLE</div>", unsafe_allow_html=True)
    tbl = daily_summary[['date','total_cars','peak_cars','peak_hour','avg_temp','precip','wx_cat']].copy()
    tbl['date']       = tbl['date'].dt.strftime('%A, %b %d')
    tbl['precip']     = tbl['precip'].round(2).astype(str) + '"'
    tbl['avg_temp']   = tbl['avg_temp'].round(1).astype(str) + '°F'
    tbl['peak_hour']  = tbl['peak_hour'].apply(lambda h: f"{int(h):02d}:00")
    tbl['total_cars'] = tbl['total_cars'].astype(int)
    tbl['peak_cars']  = tbl['peak_cars'].astype(int)
    tbl.columns = ['Date','Total Cars','Peak Cars','Peak Hour','Avg Temp','Precip','Conditions']
    st.dataframe(tbl, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════
# VIEW: HOURLY DEEP DIVE
# ═══════════════════════════════════════════════
elif view_mode == "🕐 Hourly Deep Dive":
    day_df = results_df[results_df['date'] == pd.Timestamp(selected_date)].copy()
    if day_df.empty:
        st.warning("No prediction data for the selected date.")
        st.stop()

    st.markdown(
        f"<div class='section-header'>HOUR-BY-HOUR · "
        f"{pd.Timestamp(selected_date).strftime('%A %B %d, %Y')}</div>",
        unsafe_allow_html=True,
    )

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.65, 0.35], vertical_spacing=0.06,
    )
    fig.add_trace(go.Scatter(
        x=day_df['hour_of_day'], y=day_df['predicted_cars'],
        mode='lines+markers+text',
        line=dict(color='#00e5ff', width=3),
        marker=dict(size=8, color='#00e5ff', line=dict(color='#0d0f12', width=2)),
        text=day_df['predicted_cars'].astype(int),
        textposition='top center', textfont=dict(size=9, color='#00e5ff'),
        name='Predicted Cars', fill='tozeroy',
        fillcolor='rgba(0,229,255,0.07)',
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=day_df['hour_of_day'], y=day_df['hour_temp'],
        mode='lines', line=dict(color='#ff6b35', width=2, dash='dot'),
        name='Temp (°F)',
    ), row=2, col=1)
    fig.add_trace(go.Bar(
        x=day_df['hour_of_day'], y=day_df['hour_precip'],
        marker_color='rgba(0,229,255,0.4)', name='Precip (in)',
    ), row=2, col=1)
    fig.update_layout(
        **PLOT_LAYOUT, height=520, showlegend=True,
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='#8a9099')),
        xaxis2=dict(title='Hour', tickmode='linear', dtick=1,
                    gridcolor='#2a2f38', zerolinecolor='#2a2f38'),
        yaxis=dict(title='Cars', gridcolor='#2a2f38', zerolinecolor='#2a2f38'),
        yaxis2=dict(gridcolor='#2a2f38', zerolinecolor='#2a2f38'),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Hour pills
    st.markdown("<div class='section-header'>ALL HOURS AT A GLANCE</div>", unsafe_allow_html=True)
    max_cars   = int(day_df['predicted_cars'].max())
    pills_html = ""
    for _, row in day_df.iterrows():
        h     = int(row['hour_of_day'])
        v     = int(row['predicted_cars'])
        ampm  = f"{h % 12 or 12}{'am' if h < 12 else 'pm'}"
        color = (
            "#00e5ff" if v == max_cars else
            "#ff6b35" if float(row['hour_precip']) > 0 else
            "#e8eaed"
        )
        pills_html += (
            f"<span class='hour-pill'>"
            f"<div class='hp-time'>{ampm}</div>"
            f"<div class='hp-val' style='color:{color};'>{v}</div>"
            f"</span>"
        )
    st.markdown(f"<div>{pills_html}</div>", unsafe_allow_html=True)

    # Feature snapshot
    st.markdown("<div class='section-header'>FEATURE SNAPSHOT (NOON)</div>", unsafe_allow_html=True)
    noon_rows = day_df[day_df['hour_of_day'] == 12]
    noon = noon_rows.iloc[0] if len(noon_rows) else day_df.iloc[min(12, len(day_df)-1)]

    insight_map = {
        'hour_temp':                    'Temp (°F)',
        'hour_precip':                  'Precip (in)',
        'hour_wind':                    'Wind (mph)',
        'day_temp_max':                 'Day High (°F)',
        'day_precip_sum':               'Day Precip (in)',
        'days_since_last_rain':         'Days Since Rain',
        'rolling_7day_temp':            '7-Day Avg Temp',
        'temp_anomaly':                 'Temp Anomaly',
        'is_university_in_session':     'University In Session',
        'is_holiday':                   'Holiday',
        'is_summer_break':              'Summer Break',
        'is_finals_week':               'Finals Week',
        'weather_cat':                  'Weather Category',
    }
    rows_data = []
    for col, label in insight_map.items():
        if col in noon.index:
            val = noon[col]
            if isinstance(val, float):
                val = round(val, 3)
            rows_data.append({'Feature': label, 'Value': val})
    st.dataframe(pd.DataFrame(rows_data), use_container_width=True, hide_index=True)

# ─────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────
st.divider()
st.markdown(
    "<p style='text-align:center;color:#3a4050;font-size:0.72rem;'>"
    "CarWash Intelligence · ML model: pipeline.pkl · "
    "Weather: Open-Meteo Archive + Forecast APIs · Built with Streamlit"
    "</p>",
    unsafe_allow_html=True,
)
