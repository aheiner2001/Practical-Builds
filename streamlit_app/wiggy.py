"""
WiggyWash 2-Week Car Count Forecast
Streamlit App
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor

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
# CUSTOM CSS  – dark industrial theme
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    background-color: #0d0f14;
    color: #e8e4dc;
    font-family: 'DM Sans', sans-serif;
}

h1, h2, h3 {
    font-family: 'Bebas Neue', sans-serif;
    letter-spacing: 2px;
}

.header-banner {
    background: linear-gradient(135deg, #1a1f2e 0%, #0d1117 100%);
    border-bottom: 3px solid #00c6ff;
    padding: 28px 40px 18px;
    margin-bottom: 32px;
}
.header-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 3.2rem;
    letter-spacing: 4px;
    color: #ffffff;
    margin: 0;
    line-height: 1;
}
.header-sub {
    color: #00c6ff;
    font-size: 0.85rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-top: 4px;
}

.week-label {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.6rem;
    letter-spacing: 3px;
    color: #00c6ff;
    border-left: 4px solid #00c6ff;
    padding-left: 12px;
    margin: 20px 0 12px;
}

.day-card {
    background: #151820;
    border: 1px solid #252a38;
    border-radius: 10px;
    padding: 18px 16px 14px;
    text-align: center;
    position: relative;
    transition: transform 0.15s;
}
.day-card:hover { transform: translateY(-2px); }

.day-name  { font-family:'Bebas Neue',sans-serif; font-size:1.15rem; letter-spacing:2px; color:#8899bb; }
.day-date  { font-size: 0.72rem; color:#555e74; margin-bottom:8px; }
.day-count { font-family:'Bebas Neue',sans-serif; font-size:2.6rem; color:#ffffff; line-height:1; }
.day-unit  { font-size:0.7rem; color:#556; letter-spacing:1px; }
.day-weather { font-size:0.75rem; color:#6a7a9b; margin-top:6px; }

.badge-high { background:#ff4757; color:#fff; border-radius:4px; padding:2px 7px; font-size:0.65rem; font-weight:600; }
.badge-med  { background:#ffa502; color:#000; border-radius:4px; padding:2px 7px; font-size:0.65rem; font-weight:600; }
.badge-low  { background:#2ed573; color:#000; border-radius:4px; padding:2px 7px; font-size:0.65rem; font-weight:600; }

.metric-row {
    display: flex;
    gap: 16px;
    margin-bottom: 24px;
}
.metric-box {
    flex: 1;
    background: #151820;
    border: 1px solid #252a38;
    border-radius: 10px;
    padding: 16px 20px;
    text-align: center;
}
.metric-val { font-family:'Bebas Neue',sans-serif; font-size:2rem; color:#00c6ff; }
.metric-lbl { font-size:0.7rem; color:#556; letter-spacing:2px; text-transform:uppercase; }

div[data-testid="stSpinner"] > div { border-top-color: #00c6ff !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="header-banner">
  <p class="header-title">🚗 WiggyWash</p>
  <p class="header-sub">2-Week Car Count Forecast &nbsp;·&nbsp; Powered by XGBoost + Live Weather</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HELPER: feature engineering (mirrors the notebook)
# ─────────────────────────────────────────────
HOLIDAYS = pd.to_datetime([
    '2025-01-01','2025-01-20','2025-02-17','2025-05-26','2025-06-19','2025-07-04',
    '2025-09-01','2025-10-13','2025-11-11','2025-11-27','2025-12-25',
    '2026-01-01','2026-01-19','2026-02-16','2026-05-25','2026-06-19','2026-07-03',
    '2026-09-07','2026-10-12','2026-11-11','2026-11-26','2026-12-25',
])

def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df['day_num']  = df['date'].dt.dayofweek
    df['day_name'] = df['date'].dt.day_name()
    df['is_payday'] = df['date'].dt.day.isin([1,15]).astype(int)
    df['is_monday'] = (df['date'].dt.dayofweek == 0).astype(int)

    df['month_sin'] = np.sin(2*np.pi*df['date'].dt.month/12)
    df['month_cos'] = np.cos(2*np.pi*df['date'].dt.month/12)
    week_num = df['date'].dt.isocalendar().week.astype(int)
    df['week_sin']  = np.sin(2*np.pi*week_num/52)
    df['week_cos']  = np.cos(2*np.pi*week_num/52)

    days_after = HOLIDAYS + pd.to_timedelta(1,'D')
    df['is_holiday']           = df['date'].isin(HOLIDAYS).astype(int)
    df['is_day_after_holiday'] = df['date'].isin(days_after).astype(int)

    m, d = df['date'].dt.month, df['date'].dt.day
    df['is_pre_christmas_rush']  = ((m==12)&(d>=15)&(d<=22)).astype(int)
    df['is_post_christmas_slow'] = (((m==12)&(d>=26))|((m==1)&(d<=3))).astype(int)
    df['is_early_december']      = ((m==12)&(d<=14)).astype(int)
    df['is_post_thanksgiving']   = ((m==11)&(d>=28)&(d<=30)).astype(int)
    df['days_left_in_month']     = df['date'].dt.days_in_month - d

    df['temp_avg_f']      = (df['temp_high_f'] + df['temp_low_f']) / 2
    df['precip_yesterday']  = df['precip_inches'].shift(1).fillna(0)
    df['rolling_3day_wind'] = df['wind_max_mph'].rolling(3).mean().shift(1).fillna(df['wind_max_mph'].mean())

    def get_weather_cat(code):
        if code in [0,1,2,3]: return 'clear_cloudy'
        if code in [51,53,55,61,63,65,80,81,82]: return 'rain'
        if code in [71,73,75,77,85,86]: return 'snow'
        return 'other'
    df['weather_cat'] = df['weather_code'].apply(get_weather_cat)
    return df

FEATURES = [
    'month_sin','month_cos','week_sin','week_cos','day_num',
    'is_payday','is_monday','days_left_in_month','is_holiday',
    'is_day_after_holiday','is_pre_christmas_rush','is_post_christmas_slow',
    'is_early_december','is_post_thanksgiving','temp_avg_f',
    'precip_yesterday','rolling_3day_wind',
]

LAT, LON = 40.161802, -111.634824

# ─────────────────────────────────────────────
# CACHING: load & train
# ─────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_and_train():
    url = ('https://raw.githubusercontent.com/aheiner2001/Machine-Learning/'
           'refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data%20(2).csv')
    df = pd.read_csv(url)
    df = df.rename(columns={'Text7':'date_raw','Text40':'car_count','Text48':'gross_revenue',
                             'Text41':'net_revenue','Text42':'membership_count'})
    for col in ['gross_revenue','net_revenue','car_count']:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str).str.replace(r'[$,]','',regex=True)
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['date'] = pd.to_datetime(df['date_raw'].str.split(' - ').str[0], format='%m/%d/%Y')
    df = df.sort_values('date').reset_index(drop=True)

    # Historical weather
    params = {
        'latitude': LAT, 'longitude': LON,
        'start_date': df['date'].min().strftime('%Y-%m-%d'),
        'end_date':   df['date'].max().strftime('%Y-%m-%d'),
        'daily': ['temperature_2m_max','temperature_2m_min','precipitation_sum',
                  'wind_speed_10m_max','weather_code','snowfall_sum'],
        'timezone': 'America/Denver',
        'temperature_unit': 'fahrenheit',
        'precipitation_unit': 'inch',
        'wind_speed_unit': 'mph',
    }
    r = requests.get('https://archive-api.open-meteo.com/v1/archive', params=params)
    w = r.json()['daily']
    weather_df = pd.DataFrame({
        'date': pd.to_datetime(w['time']),
        'temp_high_f': w['temperature_2m_max'],
        'temp_low_f':  w['temperature_2m_min'],
        'precip_inches': w['precipitation_sum'],
        'wind_max_mph':  w['wind_speed_10m_max'],
        'weather_code':  w['weather_code'],
        'snow_inches':   w['snowfall_sum'],
    })
    df = pd.merge(df, weather_df, on='date', how='left')
    df = add_features(df)

    df_model = df[(df['car_count'] > 5) & (df['day_num'] != 6)].dropna(subset=['car_count']).copy()
    X = pd.get_dummies(df_model[FEATURES + ['weather_cat']], drop_first=True)
    y = np.log1p(df_model['car_count'])
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = XGBRegressor(n_estimators=300, learning_rate=0.04, max_depth=6,
                         subsample=0.8, colsample_bytree=0.8, random_state=42)
    model.fit(X_train, y_train)
    return model, X.columns.tolist()

@st.cache_data(show_spinner=False)
def fetch_forecast():
    today = pd.Timestamp.today().normalize()
    end   = today + pd.Timedelta(days=14)
    params = {
        'latitude': LAT, 'longitude': LON,
        'start_date': today.strftime('%Y-%m-%d'),
        'end_date':   end.strftime('%Y-%m-%d'),
        'daily': ['temperature_2m_max','temperature_2m_min','precipitation_sum',
                  'wind_speed_10m_max','weather_code','snowfall_sum'],
        'timezone': 'America/Denver',
        'temperature_unit': 'fahrenheit',
        'precipitation_unit': 'inch',
        'wind_speed_unit': 'mph',
    }
    r = requests.get('https://api.open-meteo.com/v1/forecast', params=params)
    w = r.json()['daily']
    return pd.DataFrame({
        'date': pd.to_datetime(w['time']),
        'temp_high_f': w['temperature_2m_max'],
        'temp_low_f':  w['temperature_2m_min'],
        'precip_inches': w['precipitation_sum'],
        'wind_max_mph':  w['wind_speed_10m_max'],
        'weather_code':  w['weather_code'],
        'snow_inches':   w['snowfall_sum'],
    })

def predict_forecast(model, model_cols, fcast_df):
    fcast_df = add_features(fcast_df)
    # Keep only Mon–Sat (exclude Sunday=6)
    fcast_df = fcast_df[fcast_df['day_num'] != 6].copy()
    X_raw = pd.get_dummies(fcast_df[FEATURES + ['weather_cat']], drop_first=True)
    X_raw = X_raw.reindex(columns=model_cols, fill_value=0)
    preds = np.expm1(model.predict(X_raw))
    fcast_df['predicted_cars'] = preds.round(0).astype(int)
    return fcast_df.reset_index(drop=True)

# ─────────────────────────────────────────────
# BADGE HELPER
# ─────────────────────────────────────────────
def staffing_badge(cars):
    if cars >= 200:
        return '<span class="badge-high">HIGH DEMAND</span>'
    elif cars >= 140:
        return '<span class="badge-med">MODERATE</span>'
    else:
        return '<span class="badge-low">NORMAL</span>'

WEATHER_EMOJI = {
    'clear_cloudy': '☀️', 'rain': '🌧️', 'snow': '❄️', 'other': '🌫️'
}

def weather_label(row):
    cat  = row.get('weather_cat','other')
    hi   = row.get('temp_high_f', float('nan'))
    lo   = row.get('temp_low_f',  float('nan'))
    icon = WEATHER_EMOJI.get(cat, '🌫️')
    return f"{icon} {hi:.0f}°F / {lo:.0f}°F"

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
with st.spinner("🔧 Training model on historical data…"):
    model, model_cols = load_and_train()

with st.spinner("🌤️ Fetching 2-week weather forecast…"):
    fcast_raw = fetch_forecast()

results = predict_forecast(model, model_cols, fcast_raw)

# Split into 2 weeks
week1 = results[results['date'] < results['date'].min() + pd.Timedelta(days=7)]
week2 = results[results['date'] >= results['date'].min() + pd.Timedelta(days=7)]

# ─────── Summary metrics ───────────────────
total_w1 = week1['predicted_cars'].sum()
total_w2 = week2['predicted_cars'].sum()
peak_day  = results.loc[results['predicted_cars'].idxmax()]
avg_daily = results['predicted_cars'].mean()

st.markdown(f"""
<div class="metric-row">
  <div class="metric-box"><div class="metric-val">{total_w1:,}</div><div class="metric-lbl">Week 1 Total Cars</div></div>
  <div class="metric-box"><div class="metric-val">{total_w2:,}</div><div class="metric-lbl">Week 2 Total Cars</div></div>
  <div class="metric-box"><div class="metric-val">{int(avg_daily)}</div><div class="metric-lbl">Avg Cars / Day</div></div>
  <div class="metric-box"><div class="metric-val">{peak_day['predicted_cars']}</div>
    <div class="metric-lbl">Peak Day ({peak_day['day_name'][:3]} {peak_day['date'].strftime('%-m/%-d')})</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────── Day cards renderer ────────────────
def render_week(week_df, label):
    st.markdown(f'<div class="week-label">{label}</div>', unsafe_allow_html=True)
    cols = st.columns(len(week_df))
    for i, (_, row) in enumerate(week_df.iterrows()):
        with cols[i]:
            badge = staffing_badge(row['predicted_cars'])
            st.markdown(f"""
            <div class="day-card">
              <div class="day-name">{row['day_name'][:3].upper()}</div>
              <div class="day-date">{row['date'].strftime('%-m/%-d')}</div>
              <div class="day-count">{row['predicted_cars']}</div>
              <div class="day-unit">CARS</div>
              <div style="margin:8px 0 4px">{badge}</div>
              <div class="day-weather">{weather_label(row)}</div>
            </div>
            """, unsafe_allow_html=True)

render_week(week1, "WEEK 1")
render_week(week2, "WEEK 2")

# ─────────────────────────────────────────────
# CHART
# ─────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="week-label">STAFFING OUTLOOK</div>', unsafe_allow_html=True)

fig, ax = plt.subplots(figsize=(14, 4))
fig.patch.set_facecolor('#0d0f14')
ax.set_facecolor('#151820')

dates     = results['date'].dt.strftime('%-m/%-d\n%a')
cars      = results['predicted_cars'].values
bar_colors = ['#ff4757' if c >= 200 else '#ffa502' if c >= 140 else '#2ed573' for c in cars]

bars = ax.bar(dates, cars, color=bar_colors, width=0.6, zorder=3)
ax.axhline(200, color='#ff4757', lw=1, ls='--', alpha=0.5, label='High demand threshold (200)')
ax.axhline(140, color='#ffa502', lw=1, ls='--', alpha=0.5, label='Moderate threshold (140)')

# Week separator
if len(week1) > 0 and len(week2) > 0:
    sep = len(week1) - 0.5
    ax.axvline(sep, color='#00c6ff', lw=1.5, ls=':', alpha=0.7)
    ax.text(sep + 0.05, ax.get_ylim()[1]*0.97, 'Week 2 →', color='#00c6ff',
            fontsize=8, va='top', ha='left')

for bar, val in zip(bars, cars):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, str(val),
            ha='center', va='bottom', color='#e8e4dc', fontsize=9, fontweight='bold')

ax.set_ylabel('Predicted Cars', color='#8899bb', fontsize=10)
ax.tick_params(colors='#8899bb', labelsize=9)
for spine in ax.spines.values():
    spine.set_edgecolor('#252a38')
ax.yaxis.set_tick_params(color='#252a38')
ax.set_ylim(0, max(cars)*1.18)
ax.grid(axis='y', color='#252a38', lw=0.7, zorder=0)

legend_patches = [
    mpatches.Patch(color='#ff4757', label='High demand (200+)'),
    mpatches.Patch(color='#ffa502', label='Moderate (140–199)'),
    mpatches.Patch(color='#2ed573', label='Normal (<140)'),
]
ax.legend(handles=legend_patches, loc='upper right', framealpha=0.15,
          labelcolor='#8899bb', fontsize=8, edgecolor='#252a38')

plt.tight_layout()
st.pyplot(fig)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("""
<hr style="border-color:#252a38;margin-top:32px;">
<p style="text-align:center;color:#353d52;font-size:0.72rem;letter-spacing:2px;">
  WIGGYWASH INTELLIGENCE · XGBOOST MODEL · OPEN-METEO LIVE FORECAST
</p>
""", unsafe_allow_html=True)
