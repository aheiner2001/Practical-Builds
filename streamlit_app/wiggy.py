"""
WiggyWash 3-Week Weather & Events Dashboard
No ML model – pure weather + calendar intelligence
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import date, timedelta

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="WiggyWash Weather Intel",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Barlow+Condensed:wght@300;400;600;700&family=Barlow:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    background-color: #080b12;
    color: #dde3ee;
    font-family: 'Barlow', sans-serif;
}

h1, h2, h3 {
    font-family: 'Bebas Neue', sans-serif;
    letter-spacing: 2px;
}

/* ── Header ── */
.header-banner {
    background: linear-gradient(160deg, #0d1526 0%, #08111f 60%, #040810 100%);
    border-bottom: 2px solid #00d4ff;
    padding: 30px 44px 20px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
}
.header-banner::before {
    content: '';
    position: absolute;
    top: -40px; right: -40px;
    width: 220px; height: 220px;
    background: radial-gradient(circle, rgba(0,212,255,0.08) 0%, transparent 70%);
    pointer-events: none;
}
.header-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 3.4rem;
    letter-spacing: 5px;
    color: #ffffff;
    margin: 0;
    line-height: 1;
}
.header-sub {
    color: #00d4ff;
    font-size: 0.78rem;
    letter-spacing: 4px;
    text-transform: uppercase;
    margin-top: 6px;
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 400;
}

/* ── Week label ── */
.week-label {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.5rem;
    letter-spacing: 4px;
    color: #00d4ff;
    border-left: 4px solid #00d4ff;
    padding-left: 12px;
    margin: 28px 0 14px;
    display: flex;
    align-items: center;
    gap: 12px;
}
.week-dates {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 0.85rem;
    color: #4a5a72;
    letter-spacing: 2px;
    font-weight: 400;
}

/* ── Day card ── */
.day-card {
    background: linear-gradient(180deg, #111827 0%, #0c1320 100%);
    border: 1px solid #1e2a3e;
    border-radius: 12px;
    padding: 16px 12px 14px;
    text-align: center;
    position: relative;
    transition: border-color 0.2s, transform 0.15s;
    min-height: 260px;
}
.day-card:hover { transform: translateY(-3px); border-color: #2a3f5f; }
.day-card.today-card { border-color: #00d4ff; box-shadow: 0 0 16px rgba(0,212,255,0.12); }
.day-card.weekend-card { opacity: 0.55; }

.day-name { font-family:'Bebas Neue',sans-serif; font-size:1.1rem; letter-spacing:3px; color:#8899bb; }
.day-date { font-size: 0.68rem; color:#3d4f68; margin-bottom:10px; font-family:'Barlow Condensed',sans-serif; letter-spacing:2px; }

/* Weather big icon */
.weather-icon { font-size: 2.2rem; line-height: 1; margin: 4px 0; }

/* Temps */
.temp-row { font-family:'Barlow Condensed',sans-serif; font-size:1.05rem; font-weight:600; color:#e0e8f5; margin: 4px 0 2px; }
.temp-hi { color: #ff8c42; }
.temp-lo { color: #5bb8ff; }
.temp-sep { color: #2a3a52; margin: 0 3px; }

/* Weather condition */
.weather-cond { font-size:0.68rem; color:#4a5a72; letter-spacing:1px; font-family:'Barlow Condensed',sans-serif; margin-bottom:8px; text-transform:uppercase; }

/* Detail pills */
.detail-grid { display:flex; flex-wrap:wrap; gap:4px; justify-content:center; margin: 6px 0; }
.detail-pill {
    background: #0d1520;
    border: 1px solid #1a2535;
    border-radius: 20px;
    padding: 2px 8px;
    font-size: 0.62rem;
    color: #5a7090;
    font-family: 'Barlow Condensed', sans-serif;
    letter-spacing: 0.5px;
    white-space: nowrap;
}
.detail-pill.wind-high { border-color: #ff6b35; color: #ff8c55; }
.detail-pill.uv-high   { border-color: #ffd700; color: #ffd700; }
.detail-pill.snow-day  { border-color: #7ab8ff; color: #7ab8ff; }
.detail-pill.rain-day  { border-color: #5b9bd5; color: #5b9bd5; }

/* Event badges */
.event-stack { display:flex; flex-direction:column; gap:3px; margin-top:8px; }
.event-badge {
    border-radius: 5px;
    padding: 3px 7px;
    font-size: 0.6rem;
    font-weight: 700;
    font-family: 'Barlow Condensed', sans-serif;
    letter-spacing: 1px;
    text-transform: uppercase;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.ev-holiday   { background: #2d1a3e; color: #c084fc; border: 1px solid #7e3fbe; }
.ev-payday    { background: #1a2e1a; color: #4ade80; border: 1px solid #22863a; }
.ev-school    { background: #1a2535; color: #60a5fa; border: 1px solid #2563eb; }
.ev-seasonal  { background: #2e1e10; color: #fb923c; border: 1px solid #c2410c; }
.ev-other     { background: #1e1e2e; color: #a5b4fc; border: 1px solid #4338ca; }

/* Sunday closed */
.closed-label {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 0.7rem;
    color: #2a3545;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 8px;
}

/* ── Summary metrics ── */
.metrics-strip {
    display: flex;
    gap: 12px;
    margin-bottom: 28px;
    flex-wrap: wrap;
}
.metric-card {
    flex: 1;
    min-width: 130px;
    background: linear-gradient(160deg, #0f1928 0%, #0a1220 100%);
    border: 1px solid #1a2535;
    border-radius: 12px;
    padding: 18px 16px 14px;
    text-align: center;
}
.metric-icon { font-size: 1.4rem; margin-bottom: 4px; }
.metric-val { font-family:'Bebas Neue',sans-serif; font-size:1.9rem; color:#00d4ff; line-height:1; }
.metric-lbl { font-size:0.62rem; color:#3a4d66; letter-spacing:2px; text-transform:uppercase; margin-top:4px; font-family:'Barlow Condensed',sans-serif; }

/* ── Alert bar ── */
.alert-bar {
    background: linear-gradient(90deg, #1a0a00, #2a1200);
    border: 1px solid #8b3a00;
    border-radius: 8px;
    padding: 10px 18px;
    margin-bottom: 20px;
    font-size: 0.8rem;
    color: #fb923c;
    font-family: 'Barlow Condensed', sans-serif;
    letter-spacing: 1px;
}

.today-tag {
    position: absolute;
    top: 8px; right: 8px;
    background: #00d4ff;
    color: #000;
    font-family: 'Bebas Neue', sans-serif;
    font-size: 0.6rem;
    letter-spacing: 2px;
    padding: 1px 6px;
    border-radius: 4px;
}

div[data-testid="stSpinner"] > div { border-top-color: #00d4ff !important; }

/* Legend row */
.legend-row {
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
    margin: 12px 0 24px;
    font-size: 0.72rem;
    color: #3a4d66;
    font-family: 'Barlow Condensed', sans-serif;
    letter-spacing: 1px;
}
.legend-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 5px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
LAT, LON = 40.161802, -111.634824
TZ = "America/Denver"

# ─────────────────────────────────────────────
# CALENDAR EVENTS
# ─────────────────────────────────────────────
def get_events(dt: pd.Timestamp) -> list[tuple[str, str]]:
    """Return list of (label, css_class) for a given date."""
    events = []
    m, d, dow = dt.month, dt.day, dt.dayofweek
    y = dt.year

    # Federal holidays (exact dates, observance-adjusted)
    holidays = {
        (1,1):  ("New Year's Day", "ev-holiday"),
        (7,4):  ("Independence Day", "ev-holiday"),
        (12,25):("Christmas Day", "ev-holiday"),
        (12,24):("Christmas Eve", "ev-holiday"),
        (12,31):("New Year's Eve", "ev-other"),
        (11,11):("Veterans Day", "ev-holiday"),
    }
    # Floating holidays
    # MLK Day = 3rd Monday of Jan
    mlk = _nth_weekday(y, 1, 0, 3)
    presidents = _nth_weekday(y, 2, 0, 3)
    memorial = _last_weekday(y, 5, 0)
    juneteenth_obs = pd.Timestamp(y, 6, 19)
    labor = _nth_weekday(y, 9, 0, 1)
    columbus = _nth_weekday(y, 10, 0, 2)
    thanksgiving = _nth_weekday(y, 11, 3, 4)
    black_friday = thanksgiving + timedelta(days=1)

    float_holidays = {
        mlk: ("MLK Day", "ev-holiday"),
        presidents: ("Presidents' Day", "ev-holiday"),
        memorial: ("Memorial Day", "ev-holiday"),
        juneteenth_obs: ("Juneteenth", "ev-holiday"),
        labor: ("Labor Day", "ev-holiday"),
        columbus: ("Columbus Day", "ev-holiday"),
        thanksgiving: ("Thanksgiving 🦃", "ev-holiday"),
        black_friday: ("Black Friday 🛍️", "ev-seasonal"),
    }

    key = (m, d)
    if key in holidays:
        events.append(holidays[key])

    dt_date = dt.date()
    for fh_ts, fh_val in float_holidays.items():
        if isinstance(fh_ts, pd.Timestamp):
            if fh_ts.date() == dt_date:
                events.append(fh_val)
        else:
            if fh_ts == dt_date:
                events.append(fh_val)

    # Payday (1st and 15th)
    if d in (1, 15):
        events.append(("💵 Payday", "ev-payday"))
    # Day before payday
    elif d in (14, 31) or (d == 28 and m == 2):
        events.append(("Pre-Payday", "ev-payday"))

    # School seasons (Utah approximate)
    # Back to school: late Aug
    if m == 8 and 20 <= d <= 31:
        events.append(("🎒 Back to School", "ev-school"))
    # Spring break: ~3rd week March
    if m == 3 and 15 <= d <= 22:
        events.append(("🏖️ Spring Break", "ev-school"))
    # Last week of school (~late May)
    if m == 5 and 22 <= d <= 31:
        events.append(("🎓 End of School", "ev-school"))
    # Summer start
    if m == 6 and 1 <= d <= 7:
        events.append(("☀️ Summer Start", "ev-seasonal"))

    # Seasonal / wash-relevant
    # Post-winter-storm season (March = ideal wash time)
    if m == 3 and d <= 15:
        events.append(("🧼 Post-Winter Rush", "ev-seasonal"))
    # Fall leaf/mud season
    if m == 10 and 15 <= d <= 31:
        events.append(("🍂 Fall Season", "ev-seasonal"))
    # Pre-holiday road trips
    if m == 12 and 20 <= d <= 23:
        events.append(("🚗 Holiday Travel", "ev-seasonal"))

    # Week of Thanksgiving travel
    if _nth_weekday(y, 11, 3, 4).date() - timedelta(days=5) <= dt_date <= _nth_weekday(y, 11, 3, 4).date() - timedelta(days=1):
        events.append(("🚗 Thanksgiving Travel", "ev-seasonal"))

    return events


def _nth_weekday(year, month, weekday, n):
    """nth occurrence of weekday (0=Mon) in given month."""
    first = date(year, month, 1)
    delta = (weekday - first.weekday()) % 7
    return pd.Timestamp(first + timedelta(days=delta + 7*(n-1)))

def _last_weekday(year, month, weekday):
    """Last occurrence of weekday in given month."""
    if month == 12:
        last = date(year+1, 1, 1) - timedelta(days=1)
    else:
        last = date(year, month+1, 1) - timedelta(days=1)
    delta = (last.weekday() - weekday) % 7
    return pd.Timestamp(last - timedelta(days=delta))


# ─────────────────────────────────────────────
# WEATHER CODE → INFO
# ─────────────────────────────────────────────
def weather_info(code):
    c = int(code)
    if c == 0:   return "☀️", "Clear"
    if c == 1:   return "🌤️", "Mostly Clear"
    if c == 2:   return "⛅", "Partly Cloudy"
    if c == 3:   return "☁️", "Overcast"
    if c in (45,48): return "🌫️", "Fog"
    if c in (51,53,55): return "🌦️", "Drizzle"
    if c in (61,63,65): return "🌧️", "Rain"
    if c in (71,73,75): return "❄️", "Snow"
    if c == 77:  return "🌨️", "Snow Grains"
    if c in (80,81,82): return "⛈️", "Showers"
    if c in (85,86): return "🌨️", "Snow Showers"
    if c in (95,96,99): return "⛈️", "Thunderstorm"
    return "🌡️", "Unknown"


# ─────────────────────────────────────────────
# DATA FETCH
# ─────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=3600)
def fetch_weather():
    today = pd.Timestamp.today().normalize()
    end   = today + pd.Timedelta(days=15)  # Open-Meteo allows max ~16 days ahead

    # Core fields first — always supported
    core_fields = [
        'temperature_2m_max','temperature_2m_min',
        'precipitation_sum','wind_speed_10m_max',
        'wind_gusts_10m_max','weather_code','snowfall_sum',
        'uv_index_max','precipitation_probability_max',
    ]
    params = {
        'latitude': LAT, 'longitude': LON,
        'start_date': today.strftime('%Y-%m-%d'),
        'end_date':   end.strftime('%Y-%m-%d'),
        'daily': core_fields,
        'timezone': TZ,
        'temperature_unit': 'fahrenheit',
        'precipitation_unit': 'inch',
        'wind_speed_unit': 'mph',
    }
    r = requests.get('https://api.open-meteo.com/v1/forecast', params=params, timeout=15)
    resp = r.json()

    if 'daily' not in resp:
        error_msg = resp.get('reason', resp.get('error', str(resp)))
        raise RuntimeError(f"Open-Meteo API error: {error_msg}")

    w = resp['daily']
    n = len(w['time'])

    # Try sunshine_duration as a second optional request
    sunshine_hrs = [0] * n
    try:
        r2 = requests.get('https://api.open-meteo.com/v1/forecast', params={
            **params, 'daily': ['sunshine_duration']
        }, timeout=10)
        r2_data = r2.json()
        if 'daily' in r2_data and 'sunshine_duration' in r2_data['daily']:
            sunshine_hrs = [x/3600 if x else 0 for x in r2_data['daily']['sunshine_duration']]
    except Exception:
        pass  # sunshine is purely cosmetic, skip silently

    df = pd.DataFrame({
        'date':         pd.to_datetime(w['time']),
        'temp_high_f':  w['temperature_2m_max'],
        'temp_low_f':   w['temperature_2m_min'],
        'precip_in':    w['precipitation_sum'],
        'wind_mph':     w['wind_speed_10m_max'],
        'gust_mph':     w.get('wind_gusts_10m_max',              [None]*n),
        'weather_code': w['weather_code'],
        'snow_in':      w['snowfall_sum'],
        'uv_index':     w.get('uv_index_max',                    [0]*n),
        'precip_pct':   w.get('precipitation_probability_max',   [0]*n),
        'sunshine_hrs': sunshine_hrs,
    })
    return df

# ─────────────────────────────────────────────
# DUST / AIR QUALITY PROXY via Open-Meteo AQI
# ─────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=3600)
def fetch_air_quality():
    today = pd.Timestamp.today().normalize()
    end   = today + pd.Timedelta(days=6)  # AQI forecast only ~7 days
    params = {
        'latitude': LAT, 'longitude': LON,
        'hourly': ['pm10','dust'],
        'timezone': TZ,
        'start_date': today.strftime('%Y-%m-%d'),
        'end_date':   end.strftime('%Y-%m-%d'),
    }
    try:
        r = requests.get('https://air-quality-api.open-meteo.com/v1/air-quality',
                         params=params, timeout=10)
        data = r.json()
        hourly = data.get('hourly', {})
        times  = pd.to_datetime(hourly.get('time', []))
        pm10   = hourly.get('pm10', [])
        dust   = hourly.get('dust', [])
        if not len(times):
            return pd.DataFrame()
        aqi_df = pd.DataFrame({'datetime': times, 'pm10': pm10, 'dust': dust})
        aqi_df['date'] = aqi_df['datetime'].dt.normalize()
        daily_aqi = aqi_df.groupby('date').agg(
            pm10_max=('pm10','max'), dust_max=('dust','max')
        ).reset_index()
        return daily_aqi
    except Exception:
        return pd.DataFrame()


# ─────────────────────────────────────────────
# WASH SCORE
# ─────────────────────────────────────────────
def wash_score(row):
    """Simple 0-100 heuristic: how good is this day for car washing business."""
    score = 50
    # Temperature: ideal 50-85°F
    hi = row['temp_high_f']
    if hi >= 75: score += 20
    elif hi >= 60: score += 12
    elif hi >= 45: score += 4
    elif hi < 32: score -= 25
    # Precip probability
    pp = row.get('precip_pct', 0) or 0
    score -= int(pp * 0.3)
    # Snow
    if (row.get('snow_in') or 0) > 0.1: score -= 20
    # UV (sunny = people want clean car)
    uv = row.get('uv_index', 0) or 0
    if uv >= 7: score += 10
    elif uv >= 4: score += 5
    # Wind (too windy = dirt blows back)
    wind = row.get('wind_mph', 0) or 0
    if wind >= 30: score -= 15
    elif wind >= 20: score -= 7
    # Payday boost
    if row['date'].day in (1, 15): score += 8
    # Clamp
    return max(0, min(100, score))


def score_color(s):
    if s >= 70: return "#2ed573"
    if s >= 45: return "#ffa502"
    return "#ff4757"


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="header-banner">
  <p class="header-title">🚗 WiggyWash</p>
  <p class="header-sub">16-Day Weather Intelligence &nbsp;·&nbsp; Provo, UT &nbsp;·&nbsp; Live Forecast</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FETCH DATA
# ─────────────────────────────────────────────
with st.spinner("🌤️ Fetching 3-week weather forecast…"):
    weather_df = fetch_weather()

with st.spinner("🌬️ Fetching air quality data…"):
    aqi_df = fetch_air_quality()

# Merge AQI if available
if not aqi_df.empty:
    weather_df = weather_df.merge(aqi_df, on='date', how='left')
else:
    weather_df['pm10_max'] = None
    weather_df['dust_max'] = None

# Compute wash scores
weather_df['wash_score'] = weather_df.apply(wash_score, axis=1)
weather_df['day_num'] = weather_df['date'].dt.dayofweek
weather_df['day_name'] = weather_df['date'].dt.day_name()

# Limit to available days (up to 16)
weather_df = weather_df.head(16).reset_index(drop=True)

# ─────────────────────────────────────────────
# SUMMARY METRICS
# ─────────────────────────────────────────────
today_ts = pd.Timestamp.today().normalize()
open_days = weather_df[weather_df['day_num'] != 6]  # exclude Sundays
best_day  = open_days.loc[open_days['wash_score'].idxmax()]
avg_score = open_days['wash_score'].mean()
rain_days = (open_days['precip_pct'] >= 40).sum()
hot_days  = (open_days['temp_high_f'] >= 75).sum()
wind_days = (open_days['wind_mph'] >= 20).sum()

# Alerts
alerts = []
for _, row in open_days.iterrows():
    if (row['wind_mph'] or 0) >= 35:
        alerts.append(f"⚠️ High winds {int(row['wind_mph'])} mph on {row['day_name'][:3]} {row['date'].strftime('%-m/%-d')}")
    if (row.get('dust_max') or 0) >= 200:
        alerts.append(f"🌪️ High dust event on {row['day_name'][:3]} {row['date'].strftime('%-m/%-d')} — cars will re-soil quickly")
    if (row['snow_in'] or 0) >= 1:
        alerts.append(f"❄️ Significant snow {row['snow_in']:.1f}\" on {row['day_name'][:3]} {row['date'].strftime('%-m/%-d')} — post-storm rush likely next day")

if alerts:
    for a in alerts[:3]:
        st.markdown(f'<div class="alert-bar">{a}</div>', unsafe_allow_html=True)

st.markdown(f"""
<div class="metrics-strip">
  <div class="metric-card">
    <div class="metric-icon">🗓️</div>
    <div class="metric-val">{len(weather_df)}</div>
    <div class="metric-lbl">Days Forecasted</div>
  </div>
  <div class="metric-card">
    <div class="metric-icon">⭐</div>
    <div class="metric-val">{int(avg_score)}</div>
    <div class="metric-lbl">Avg Wash Score</div>
  </div>
  <div class="metric-card">
    <div class="metric-icon">🌧️</div>
    <div class="metric-val">{rain_days}</div>
    <div class="metric-lbl">Rainy Days (40%+)</div>
  </div>
  <div class="metric-card">
    <div class="metric-icon">🌡️</div>
    <div class="metric-val">{hot_days}</div>
    <div class="metric-lbl">Warm Days (75°F+)</div>
  </div>
  <div class="metric-card">
    <div class="metric-icon">💨</div>
    <div class="metric-val">{wind_days}</div>
    <div class="metric-lbl">Windy Days (20+ mph)</div>
  </div>
  <div class="metric-card">
    <div class="metric-icon">🏆</div>
    <div class="metric-val">{best_day['day_name'][:3].upper()}<br><span style="font-size:1.2rem">{best_day['date'].strftime('%-m/%-d')}</span></div>
    <div class="metric-lbl">Best Wash Day</div>
  </div>
</div>
""", unsafe_allow_html=True)

# Legend
st.markdown("""
<div class="legend-row">
  <span><span class="legend-dot" style="background:#2ed573"></span>High wash score (70+)</span>
  <span><span class="legend-dot" style="background:#ffa502"></span>Moderate (45–69)</span>
  <span><span class="legend-dot" style="background:#ff4757"></span>Low (&lt;45)</span>
  <span style="color:#c084fc">■ Holiday &nbsp;</span>
  <span style="color:#4ade80">■ Payday &nbsp;</span>
  <span style="color:#60a5fa">■ School &nbsp;</span>
  <span style="color:#fb923c">■ Seasonal &nbsp;</span>
  <span style="color:#2a3a52">Sundays = Closed</span>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DAY CARD RENDERER
# ─────────────────────────────────────────────
def render_week(week_df, label, date_range_str):
    st.markdown(
        f'<div class="week-label">{label} <span class="week-dates">{date_range_str}</span></div>',
        unsafe_allow_html=True
    )
    cols = st.columns(len(week_df))
    for i, (_, row) in enumerate(week_df.iterrows()):
        is_today  = row['date'].date() == today_ts.date()
        is_sunday = row['day_num'] == 6

        icon, cond = weather_info(row['weather_code'])
        events     = get_events(row['date'])
        sc         = int(row['wash_score'])
        sc_col     = score_color(sc)

        # Detail pills
        pills = []
        wind = row.get('wind_mph') or 0
        gust = row.get('gust_mph') or 0
        uv   = row.get('uv_index') or 0
        pp   = row.get('precip_pct') or 0
        snow = row.get('snow_in') or 0
        pm10 = row.get('pm10_max') or 0
        dust = row.get('dust_max') or 0
        sun_hrs = row.get('sunshine_hrs') or 0

        wind_cls = "wind-high" if wind >= 25 else ""
        pills.append(f'<span class="detail-pill {wind_cls}">💨 {int(wind)} mph</span>')
        if gust and gust > wind + 5:
            pills.append(f'<span class="detail-pill {wind_cls}">Gusts {int(gust)}</span>')
        if uv and uv > 0:
            uv_cls = "uv-high" if uv >= 8 else ""
            pills.append(f'<span class="detail-pill {uv_cls}">☀️ UV {uv:.0f}</span>')
        if pp and pp > 10:
            rain_cls = "rain-day" if pp >= 40 else ""
            pills.append(f'<span class="detail-pill {rain_cls}">🌧️ {int(pp)}%</span>')
        if snow > 0.1:
            pills.append(f'<span class="detail-pill snow-day">❄️ {snow:.1f}″</span>')
        if sun_hrs > 1:
            pills.append(f'<span class="detail-pill">🌤 {sun_hrs:.0f}h sun</span>')
        if pm10 and pm10 > 50:
            dust_cls = "wind-high" if pm10 >= 150 else ""
            pills.append(f'<span class="detail-pill {dust_cls}">🌫 PM10 {int(pm10)}</span>')
        if dust and dust > 100:
            pills.append(f'<span class="detail-pill wind-high">🪨 Dust {int(dust)}</span>')

        # Event badges HTML
        event_html = ""
        if events:
            badges = "".join(
                f'<div class="event-badge {cls}">{name}</div>'
                for name, cls in events[:4]
            )
            event_html = f'<div class="event-stack">{badges}</div>'

        # Wash score bar
        score_bar_width = sc
        score_bg = f"background: linear-gradient(90deg, {sc_col}33 0%, transparent 100%); border-left: 3px solid {sc_col};"

        today_tag = '<div class="today-tag">TODAY</div>' if is_today else ""
        card_cls  = "today-card" if is_today else ("weekend-card" if is_sunday else "")

        pills_html = "".join(pills)

        if is_sunday:
            inner = f"""
            <div class="weather-icon">{icon}</div>
            <div class="temp-row">
              <span class="temp-hi">{int(row['temp_high_f'])}°</span>
              <span class="temp-sep">/</span>
              <span class="temp-lo">{int(row['temp_low_f'])}°</span>
            </div>
            <div class="weather-cond">{cond}</div>
            <div class="closed-label">CLOSED SUNDAY</div>
            """
        else:
            inner = f"""
            <div class="weather-icon">{icon}</div>
            <div class="temp-row">
              <span class="temp-hi">{int(row['temp_high_f'])}°</span>
              <span class="temp-sep">/</span>
              <span class="temp-lo">{int(row['temp_low_f'])}°</span>
            </div>
            <div class="weather-cond">{cond}</div>
            <div class="detail-grid">{pills_html}</div>
            <div style="margin: 8px 0 4px; border-radius: 4px; overflow: hidden; height: 18px; {score_bg} display:flex; align-items:center; padding: 0 8px;">
              <span style="font-family:'Barlow Condensed',sans-serif; font-size:0.65rem; color:{sc_col}; letter-spacing:1px; font-weight:600;">WASH SCORE {sc}</span>
            </div>
            {event_html}
            """

        with cols[i]:
            st.markdown(f"""
            <div class="day-card {card_cls}">
              {today_tag}
              <div class="day-name">{row['day_name'][:3].upper()}</div>
              <div class="day-date">{row['date'].strftime('%-m/%-d/%y')}</div>
              {inner}
            </div>
            """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SPLIT INTO 3 WEEKS
# ─────────────────────────────────────────────
week1 = weather_df.iloc[0:7]
week2 = weather_df.iloc[7:14]
week3 = weather_df.iloc[14:]

def week_range(df):
    if df.empty:
        return ""
    return f"{df.iloc[0]['date'].strftime('%-m/%-d')} - {df.iloc[-1]['date'].strftime('%-m/%-d')}"

render_week(week1, "WEEK 1", week_range(week1))
render_week(week2, "WEEK 2", week_range(week2))
if not week3.empty:
    render_week(week3, "WEEK 3", week_range(week3))

# ─────────────────────────────────────────────
# CHARTS
# ─────────────────────────────────────────────
st.markdown('<br>', unsafe_allow_html=True)
st.markdown('<div class="week-label">📊 FORECAST CHARTS</div>', unsafe_allow_html=True)

chart_df = open_days.copy()
xlabels  = chart_df['date'].dt.strftime('%-m/%-d\n%a').tolist()
xs       = range(len(chart_df))

fig, axes = plt.subplots(3, 1, figsize=(16, 11), facecolor='#080b12')
fig.subplots_adjust(hspace=0.55)

# -- Chart 1: Wash Score --
ax = axes[0]
ax.set_facecolor('#0d1420')
colors = [score_color(s) for s in chart_df['wash_score']]
bars = ax.bar(xs, chart_df['wash_score'], color=colors, width=0.6, zorder=3, alpha=0.9)
ax.axhline(70, color='#2ed573', lw=1, ls='--', alpha=0.35)
ax.axhline(45, color='#ffa502', lw=1, ls='--', alpha=0.35)
for bar, val in zip(bars, chart_df['wash_score']):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, str(int(val)),
            ha='center', va='bottom', color='#8899bb', fontsize=7.5, fontweight='bold')
ax.set_xticks(list(xs)); ax.set_xticklabels(xlabels, fontsize=8, color='#556677')
ax.set_ylabel('Wash Score', color='#8899bb', fontsize=9)
ax.set_ylim(0, 115)
ax.set_title('Wash Score (Weather + Calendar Factors)', color='#00d4ff', fontsize=11,
             fontfamily='DejaVu Sans', loc='left', pad=8)
ax.tick_params(colors='#3a4d66')
for sp in ax.spines.values(): sp.set_edgecolor('#1a2535')
ax.grid(axis='y', color='#1a2535', lw=0.6, zorder=0)

# Week separators
for sep in [len(week1[week1['day_num']!=6])-0.5, len(week1[week1['day_num']!=6])+len(week2[week2['day_num']!=6])-0.5]:
    if 0 < sep < len(chart_df):
        ax.axvline(sep, color='#00d4ff', lw=1, ls=':', alpha=0.4)

# -- Chart 2: Temperature band + Precip % --
ax2 = axes[1]
ax2.set_facecolor('#0d1420')
x_arr = np.array(list(xs))
hi = chart_df['temp_high_f'].values
lo = chart_df['temp_low_f'].values
ax2.fill_between(x_arr, lo, hi, alpha=0.25, color='#ff8c42', zorder=2)
ax2.plot(x_arr, hi, color='#ff8c42', lw=2, marker='o', ms=4, zorder=3, label='High °F')
ax2.plot(x_arr, lo, color='#5bb8ff', lw=2, marker='o', ms=4, zorder=3, label='Low °F')
ax2.axhline(32, color='#5bb8ff', lw=1, ls='--', alpha=0.3, label='Freezing')
ax2.axhline(75, color='#ff8c42', lw=1, ls='--', alpha=0.3, label='Ideal High (75°)')

ax2b = ax2.twinx()
ax2b.bar(x_arr, chart_df['precip_pct'].fillna(0), color='#3a7bd5', alpha=0.3, width=0.5, zorder=1)
ax2b.set_ylabel('Precip Prob %', color='#3a7bd5', fontsize=8)
ax2b.tick_params(colors='#3a7bd5', labelsize=7)
ax2b.set_ylim(0, 160)
ax2b.spines['right'].set_edgecolor('#1a2535')

ax2.set_xticks(list(xs)); ax2.set_xticklabels(xlabels, fontsize=8, color='#556677')
ax2.set_ylabel('Temperature °F', color='#8899bb', fontsize=9)
ax2.set_title('Temperature Range & Rain Probability', color='#00d4ff', fontsize=11,
              fontfamily='DejaVu Sans', loc='left', pad=8)
ax2.tick_params(colors='#3a4d66')
for sp in ax2.spines.values(): sp.set_edgecolor('#1a2535')
ax2.grid(axis='y', color='#1a2535', lw=0.6, zorder=0)
ax2.legend(loc='upper right', fontsize=7, framealpha=0.1, labelcolor='#8899bb', edgecolor='#1a2535')

# -- Chart 3: Wind + UV + (Dust if available) --
ax3 = axes[2]
ax3.set_facecolor('#0d1420')

wind_vals = chart_df['wind_mph'].fillna(0).values
gust_vals = chart_df['gust_mph'].fillna(0).values
uv_vals   = chart_df['uv_index'].fillna(0).values

bar_width = 0.35
ax3.bar(x_arr - bar_width/2, wind_vals, width=bar_width, color='#a78bfa', alpha=0.8, label='Wind Speed (mph)', zorder=3)
ax3.bar(x_arr + bar_width/2, gust_vals, width=bar_width, color='#f472b6', alpha=0.5, label='Gust Speed (mph)', zorder=3)
ax3.axhline(20, color='#a78bfa', lw=0.8, ls='--', alpha=0.3)
ax3.axhline(35, color='#ff4757', lw=0.8, ls='--', alpha=0.3)

ax3b = ax3.twinx()
ax3b.plot(x_arr, uv_vals, color='#ffd700', lw=2, marker='D', ms=4, zorder=4, label='UV Index')
ax3b.axhline(8, color='#ffd700', lw=0.8, ls='--', alpha=0.3)
ax3b.set_ylabel('UV Index', color='#ffd700', fontsize=8)
ax3b.tick_params(colors='#ffd700', labelsize=7)
ax3b.set_ylim(0, 18)
ax3b.spines['right'].set_edgecolor('#1a2535')

# Dust overlay if available
if not aqi_df.empty and 'pm10_max' in chart_df.columns:
    pm10_vals = chart_df['pm10_max'].fillna(0).values
    ax3b2 = ax3.twinx()
    ax3b2.spines['right'].set_position(('outward', 50))
    ax3b2.plot(x_arr, pm10_vals, color='#94a3b8', lw=1.5, ls=':', marker='s', ms=3, alpha=0.7, zorder=4, label='PM10 (µg/m³)')
    ax3b2.set_ylabel('PM10 µg/m³', color='#94a3b8', fontsize=7)
    ax3b2.tick_params(colors='#94a3b8', labelsize=6)
    ax3b2.set_ylim(0, 400)
    ax3b2.spines['right'].set_edgecolor('#1a2535')

ax3.set_xticks(list(xs)); ax3.set_xticklabels(xlabels, fontsize=8, color='#556677')
ax3.set_ylabel('Wind Speed (mph)', color='#8899bb', fontsize=9)
ax3.set_title('Wind, Gusts, UV Index & Dust (PM10)', color='#00d4ff', fontsize=11,
              fontfamily='DejaVu Sans', loc='left', pad=8)
ax3.tick_params(colors='#3a4d66')
for sp in ax3.spines.values(): sp.set_edgecolor('#1a2535')
ax3.grid(axis='y', color='#1a2535', lw=0.6, zorder=0)
lines1, labels1 = ax3.get_legend_handles_labels()
lines2, labels2 = ax3b.get_legend_handles_labels()
ax3.legend(lines1+lines2, labels1+labels2, loc='upper right', fontsize=7,
           framealpha=0.1, labelcolor='#8899bb', edgecolor='#1a2535')

plt.tight_layout()
st.pyplot(fig)

# ─────────────────────────────────────────────
# UPCOMING EVENTS TABLE
# ─────────────────────────────────────────────
st.markdown('<br>', unsafe_allow_html=True)
st.markdown('<div class="week-label">📅 UPCOMING CALENDAR EVENTS</div>', unsafe_allow_html=True)

all_events = []
for _, row in weather_df.iterrows():
    evs = get_events(row['date'])
    for name, cls in evs:
        all_events.append({
            'Date': row['date'].strftime('%A, %b %-d'),
            'Event': name,
            'Temp Hi': f"{int(row['temp_high_f'])}°F",
            'Wash Score': int(row['wash_score']),
        })

if all_events:
    ev_df = pd.DataFrame(all_events)
    st.dataframe(
        ev_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Wash Score": st.column_config.ProgressColumn(
                "Wash Score", min_value=0, max_value=100, format="%d"
            )
        }
    )
else:
    st.write("No notable events in the next 3 weeks.")

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("""
<hr style="border-color:#1a2535;margin-top:36px;">
<p style="text-align:center;color:#252f42;font-size:0.68rem;letter-spacing:3px;font-family:'Barlow Condensed',sans-serif;">
  WIGGYWASH WEATHER INTEL &nbsp;·&nbsp; OPEN-METEO LIVE FORECAST &nbsp;·&nbsp; PROVO, UT (40.16°N 111.63°W)
</p>
""", unsafe_allow_html=True)
