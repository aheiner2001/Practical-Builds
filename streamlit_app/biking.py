import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from datetime import date, timedelta
import requests
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Bike Rental Predictor", page_icon="🚲", layout="centered")
st.title("🚲 Bike Rental Demand Predictor")
st.write("Enter ride conditions below to get predictions for every hour of the day — plus a live 7-day forecast.")

# ---------------------------------------------------
# Helper functions
# ---------------------------------------------------
def hour_bin(x):
    if x in [0, 1, 2, 3, 4, 5]:          return 0
    elif x in [7, 8]:                     return 1
    elif x in [11, 12, 13, 14, 15, 16]:   return 2
    elif x in [17, 18, 19]:               return 3
    else:                                 return 4

def temp_bin(x):
    if x < 0:          return 1
    elif 10 <= x < 36: return 2
    else:              return 3

def get_season(month):
    if month in [3, 4, 5]:    return 1
    elif month in [6, 7, 8]:  return 2
    elif month in [9, 10, 11]:return 3
    else:                     return 4

def weathercode_to_sit(code):
    if code == 0:                         return 1   # Clear
    elif code in [1,2,3,45,48]:           return 2   # Partly cloudy / fog
    elif code in [51,53,55,61,63,80,81]:  return 3   # Light rain/drizzle
    else:                                 return 4   # Heavy rain/snow/storm

def engineer_features(df):
    df = df.copy()
    df['dteday'] = pd.to_datetime(df['dteday'])
    df['dateTime'] = df['dteday'].apply(lambda x: x.toordinal()) * 24 + df['hr']
    df['daylight']   = np.sin(df['hr'] / 24 * np.pi * 2)
    df['month']      = df['dteday'].dt.month
    df['day']        = df['dteday'].dt.day
    df['month_sin']  = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos']  = np.cos(2 * np.pi * df['month'] / 12)
    df['day_sin']    = np.sin(2 * np.pi * df['day'] / 31)
    df['day_cos']    = np.cos(2 * np.pi * df['day'] / 31)
    df['hr_sin']     = np.sin(2 * np.pi * df['hr'] / 24)
    df['hr_cos']     = np.cos(2 * np.pi * df['hr'] / 24)
    df['possible_worker'] = np.where(
        (df['hr'] >= 7.5) & (df['hr'] <= 17.5) & (df['workingday'] == 1), 1, 0
    )
    b, c = 17.625, 243.04
    hum_safe = df['hum'].clip(lower=1)
    gamma = np.log(hum_safe / 100) + (b * df['temp_c']) / (c + df['temp_c'])
    df['dew_point']  = (c * gamma) / (b - gamma)
    df['hour_bin']   = df['hr'].apply(hour_bin)
    df['tempt_bin']  = df['temp_c'].apply(temp_bin)
    df['prime_conditions'] = (
        df['hour_bin'].isin([1, 2, 3]) & (df['tempt_bin'] == 2)
    ).astype(int)
    return df

FEATURE_COLS = [
    'dateTime', 'season', 'holiday', 'workingday', 'weathersit',
    'temp_c', 'feels_like_c', 'hum', 'daylight', 'windspeed',
    'month_sin', 'month_cos', 'day_sin', 'day_cos',
    'hr_sin', 'hr_cos', 'hour_bin', 'prime_conditions',
    'possible_worker', 'dew_point'
]

DATA_URL = "https://raw.githubusercontent.com/byui-cse/cse450-course/master/data/bikes.csv"

def build_day_rows(date_str, temp_c, feels_like_c, hum, windspeed,
                   season, weathersit, workingday, holiday):
    rows = []
    for hr in range(24):
        rows.append({
            'dteday': date_str, 'hr': hr,
            'temp_c': temp_c, 'feels_like_c': feels_like_c,
            'hum': hum, 'windspeed': windspeed,
            'season': season, 'weathersit': weathersit,
            'workingday': workingday, 'holiday': holiday,
        })
    return pd.DataFrame(rows)

# ---------------------------------------------------
# Train model once (cached)
# ---------------------------------------------------
@st.cache_resource
def train_model():
    df = pd.read_csv(DATA_URL)
    df_eng = engineer_features(df)
    X = df_eng[FEATURE_COLS]
    y = df['casual'] + df['registered']
    X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=20)
    model = GradientBoostingRegressor(
        n_estimators=500, learning_rate=0.05, max_depth=6,
        min_samples_split=6, min_samples_leaf=3,
        subsample=0.8, max_features=0.8, random_state=42
    )
    model.fit(X_train, y_train)
    return model

with st.spinner("Training model on bike data... (only happens once)"):
    model = train_model()

st.success("Model ready!")
st.divider()

# ---------------------------------------------------
# Fetch 7-day hourly forecast from Open-Meteo (free, no API key)
# Washington D.C. — Capital Bikeshare's city
# ---------------------------------------------------
@st.cache_data(ttl=3600)
def fetch_forecast():
    today = date.today()
    end   = today + timedelta(days=6)
    url = (
        "https://api.open-meteo.com/v1/forecast"
        "?latitude=38.9072&longitude=-77.0369"
        "&hourly=temperature_2m,apparent_temperature,"
        "relativehumidity_2m,windspeed_10m,weathercode"
        "&temperature_unit=celsius"
        "&windspeed_unit=kmh"
        f"&start_date={today}&end_date={end}"
        "&timezone=America%2FNew_York"
    )
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json(), str(today)
    except Exception as e:
        return None, str(today)

# ---------------------------------------------------
# Section 1 — Manual full-day prediction
# ---------------------------------------------------
st.subheader("📅 Select a Day to Forecast")

col1, col2 = st.columns(2)
with col1:
    date_input   = st.date_input("Date", value=pd.Timestamp("2012-06-15"))
    temp_c       = st.number_input("Temperature (°C)", -10.0, 45.0, 20.0, step=0.5)
    feels_like_c = st.number_input("Feels-Like Temp (°C)", -10.0, 45.0, 18.0, step=0.5)
    hum          = st.number_input("Humidity (%)", 0, 100, 60)

with col2:
    windspeed  = st.number_input("Wind Speed (km/h)", 0.0, 70.0, 15.0, step=0.5)
    season     = st.selectbox("Season", [1, 2, 3, 4],
                              format_func=lambda x: {1:"Spring",2:"Summer",3:"Fall",4:"Winter"}[x])
    weathersit = st.selectbox("Weather Situation", [1, 2, 3, 4],
                              format_func=lambda x: {
                                  1:"Clear / Few Clouds",
                                  2:"Mist / Cloudy",
                                  3:"Light Rain / Snow",
                                  4:"Heavy Rain / Ice"}[x])
    workingday = st.selectbox("Working Day?", [0, 1], format_func=lambda x: "Yes" if x else "No")
    holiday    = st.selectbox("Holiday?",     [0, 1], format_func=lambda x: "Yes" if x else "No")

if st.button("Predict Full Day", type="primary"):
    rows  = build_day_rows(str(date_input), temp_c, feels_like_c, hum,
                           windspeed, season, weathersit, workingday, holiday)
    eng   = engineer_features(rows)
    preds = np.maximum(0, np.round(model.predict(eng[FEATURE_COLS]))).astype(int)

    result_df = pd.DataFrame({
        'Hour': [f"{h:02d}:00" for h in range(24)],
        'Predicted Rentals': preds,
    })

    st.divider()
    st.subheader(f"Hourly Predictions — {date_input.strftime('%A, %B %d %Y')}")

    ca, cb, cc = st.columns(3)
    ca.metric("Total Rentals (day)", f"{preds.sum():,}")
    cb.metric("Peak Hour",           f"{preds.argmax():02d}:00")
    cc.metric("Peak Rentals",        f"{preds.max():,}")

    st.bar_chart(result_df.set_index('Hour'), use_container_width=True)
    st.dataframe(result_df, use_container_width=True, hide_index=True)

    if preds.sum() > 8000:
        st.success("High demand day — make sure bikes are fully stocked!")
    elif preds.sum() > 3000:
        st.info("Moderate demand expected across the day.")
    else:
        st.warning("Low demand expected today.")

# ---------------------------------------------------
# Section 2 — Live 7-day forecast (always today → today+6)
# ---------------------------------------------------
st.divider()

forecast_data, fetch_date = fetch_forecast()
today_str = str(date.today())
end_str   = str(date.today() + timedelta(days=6))

st.subheader("📡 Live 7-Day Forecast")
st.caption(
    f"Real weather from Open-Meteo for Washington D.C. · "
    f"{pd.Timestamp(today_str).strftime('%b %d')} → {pd.Timestamp(end_str).strftime('%b %d, %Y')} · "
    f"Auto-refreshes every hour"
)

if forecast_data is None:
    st.error("Could not fetch forecast. Check your internet connection.")
else:
    hourly     = forecast_data['hourly']
    times      = pd.to_datetime(hourly['time'])
    temp_vals  = hourly['temperature_2m']
    feels_vals = hourly['apparent_temperature']
    hum_vals   = hourly['relativehumidity_2m']
    wind_vals  = hourly['windspeed_10m']
    wcode_vals = hourly['weathercode']

    fc_rows = []
    for i, t in enumerate(times):
        dow = t.weekday()  # 0=Mon … 6=Sun
        fc_rows.append({
            'dteday':       str(t.date()),
            'hr':           t.hour,
            'temp_c':       temp_vals[i],
            'feels_like_c': feels_vals[i],
            'hum':          hum_vals[i],
            'windspeed':    wind_vals[i],
            'season':       get_season(t.month),
            'weathersit':   weathercode_to_sit(wcode_vals[i]),
            'workingday':   1 if dow < 5 else 0,
            'holiday':      0,
        })

    fc_df   = pd.DataFrame(fc_rows)
    fc_eng  = engineer_features(fc_df)
    fc_preds = np.maximum(0, np.round(model.predict(fc_eng[FEATURE_COLS]))).astype(int)
    fc_df['predicted_rentals'] = fc_preds

    # Aggregate by day
    daily = (
        fc_df.groupby('dteday')
        .agg(
            total_rentals  = ('predicted_rentals', 'sum'),
            peak_rentals   = ('predicted_rentals', 'max'),
            avg_temp       = ('temp_c', 'mean'),
            avg_hum        = ('hum', 'mean'),
            weathersit     = ('weathersit', lambda x: x.mode()[0]),
        )
        .reset_index()
    )
    daily['date'] = pd.to_datetime(daily['dteday'])

    # Only keep today → today+6 (exact 7 days)
    today_ts = pd.Timestamp(today_str)
    daily = daily[daily['date'] >= today_ts].head(7).copy()

    daily['Day']               = daily['date'].dt.strftime('%a %b %d')
    daily['Avg Temp (°C)']     = daily['avg_temp'].round(1)
    daily['Avg Humidity']      = daily['avg_hum'].round(0).astype(int).astype(str) + '%'
    daily['Weather']           = daily['weathersit'].map(
        {1:"☀️ Clear", 2:"🌥️ Cloudy", 3:"🌧️ Rain", 4:"⛈️ Heavy"}
    )
    daily['Total Rentals']     = daily['total_rentals']
    daily['Peak Hr Rentals']   = daily['peak_rentals']

    # Summary
    best  = daily.loc[daily['Total Rentals'].idxmax()]
    worst = daily.loc[daily['Total Rentals'].idxmin()]
    m1, m2, m3 = st.columns(3)
    m1.metric("Best Day",    best['Day'],  f"{best['Total Rentals']:,} rentals")
    m2.metric("Worst Day",   worst['Day'], f"{worst['Total Rentals']:,} rentals")
    m3.metric("7-Day Total", f"{daily['Total Rentals'].sum():,} bikes")

    st.bar_chart(daily.set_index('Day')['Total Rentals'], use_container_width=True)

    display_cols = ['Day','Weather','Avg Temp (°C)','Avg Humidity','Total Rentals','Peak Hr Rentals']
    st.dataframe(daily[display_cols], use_container_width=True, hide_index=True)
