import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
import requests
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Bike Rental Predictor", page_icon="🚲", layout="centered")
st.title("🚲 Bike Rental Demand Predictor")
st.write("Enter ride conditions below to get predictions for every hour of the day — plus a 7-day forecast.")

# ---------------------------------------------------
# Helper functions
# ---------------------------------------------------
def hour_bin(x):
    if x in [0, 1, 2, 3, 4, 5]:         return 0
    elif x in [7, 8]:                    return 1
    elif x in [11, 12, 13, 14, 15, 16]:  return 2
    elif x in [17, 18, 19]:              return 3
    else:                                return 4

def temp_bin(x):
    if x < 0:          return 1
    elif 10 <= x < 36: return 2
    else:              return 3

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

def get_season(month):
    if month in [3, 4, 5]:   return 1
    elif month in [6, 7, 8]: return 2
    elif month in [9,10,11]: return 3
    else:                    return 4

def weathercode_to_sit(wmo_code):
    """Map Open-Meteo WMO weather codes to bikeshare weathersit (1-4)."""
    if wmo_code == 0:                          return 1   # Clear
    elif wmo_code in [1, 2, 3, 45, 48]:       return 2   # Partly cloudy / fog
    elif wmo_code in [51,53,55,61,63,80,81]:  return 3   # Light rain/drizzle
    else:                                      return 4   # Heavy rain/snow/storm

def build_day_rows(date_str, temp_c, feels_like_c, hum, windspeed,
                   season, weathersit, workingday, holiday):
    """Build 24 rows (one per hour) for a given day."""
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
# Fetch 7-day forecast from Open-Meteo (free, no key)
# ---------------------------------------------------
@st.cache_data(ttl=3600)
def fetch_forecast(lat=38.9072, lon=-77.0369):
    """Fetch 7-day hourly forecast from Open-Meteo. Defaults to Washington DC."""
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&hourly=temperature_2m,apparent_temperature,relativehumidity_2m,"
        "windspeed_10m,weathercode"
        "&temperature_unit=celsius"
        "&windspeed_unit=kmh"
        "&forecast_days=7"
        "&timezone=America%2FNew_York"
    )
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

# ---------------------------------------------------
# User Inputs
# ---------------------------------------------------
st.subheader("Select a Day to Forecast")

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

# ---------------------------------------------------
# Full-day prediction
# ---------------------------------------------------
if st.button("Predict Full Day", type="primary"):
    rows    = build_day_rows(str(date_input), temp_c, feels_like_c, hum,
                             windspeed, season, weathersit, workingday, holiday)
    eng     = engineer_features(rows)
    preds   = np.maximum(0, np.round(model.predict(eng[FEATURE_COLS]))).astype(int)

    result_df = pd.DataFrame({
        'Hour': [f"{h:02d}:00" for h in range(24)],
        'Predicted Rentals': preds,
    })

    st.divider()
    st.subheader(f"Hourly Predictions — {date_input.strftime('%A, %B %d %Y')}")

    col3, col4, col5 = st.columns(3)
    col3.metric("Total Rentals (day)",  f"{preds.sum():,}")
    col4.metric("Peak Hour",            f"{preds.argmax():02d}:00")
    col5.metric("Peak Rentals",         f"{preds.max():,}")

    st.bar_chart(result_df.set_index('Hour'), use_container_width=True)
    st.dataframe(result_df, use_container_width=True, hide_index=True)

    if preds.sum() > 8000:
        st.success("High demand day — make sure bikes are fully stocked!")
    elif preds.sum() > 3000:
        st.info("Moderate demand expected across the day.")
    else:
        st.warning("Low demand expected today.")

# ---------------------------------------------------
# 7-Day Real Weather Forecast
# ---------------------------------------------------
st.divider()
st.subheader("📡 Next 7 Days — Live Weather Forecast")
st.caption("Weather auto-fetched for Washington D.C. (Capital Bikeshare's home city) via Open-Meteo.")

forecast_data = fetch_forecast()

if forecast_data is None:
    st.error("Could not fetch forecast data. Check your internet connection.")
else:
    hourly      = forecast_data['hourly']
    times       = pd.to_datetime(hourly['time'])
    temp_vals   = hourly['temperature_2m']
    feels_vals  = hourly['apparent_temperature']
    hum_vals    = hourly['relativehumidity_2m']
    wind_vals   = hourly['windspeed_10m']
    wcode_vals  = hourly['weathercode']

    forecast_rows = []
    for i, t in enumerate(times):
        month = t.month
        dow   = t.weekday()   # 0=Mon … 6=Sun
        forecast_rows.append({
            'dteday':       str(t.date()),
            'hr':           t.hour,
            'temp_c':       temp_vals[i],
            'feels_like_c': feels_vals[i],
            'hum':          hum_vals[i],
            'windspeed':    wind_vals[i],
            'season':       get_season(month),
            'weathersit':   weathercode_to_sit(wcode_vals[i]),
            'workingday':   1 if dow < 5 else 0,
            'holiday':      0,
        })

    fc_df  = pd.DataFrame(forecast_rows)
    fc_eng = engineer_features(fc_df)
    fc_preds = np.maximum(0, np.round(model.predict(fc_eng[FEATURE_COLS]))).astype(int)
    fc_df['predicted_rentals'] = fc_preds

    # Aggregate by day
    daily = (
        fc_df.groupby('dteday')
        .agg(
            total_rentals=('predicted_rentals', 'sum'),
            peak_rentals=('predicted_rentals', 'max'),
            avg_temp=('temp_c', 'mean'),
            avg_hum=('hum', 'mean'),
            weathersit=('weathersit', lambda x: x.mode()[0]),
        )
        .reset_index()
    )
    daily['date']     = pd.to_datetime(daily['dteday'])
    daily['Day']      = daily['date'].dt.strftime('%a %b %d')
    daily['Avg Temp (°C)']  = daily['avg_temp'].round(1)
    daily['Avg Humidity']   = daily['avg_hum'].round(0).astype(int).astype(str) + '%'
    daily['Weather']  = daily['weathersit'].map({
        1:"☀️ Clear", 2:"🌥️ Cloudy", 3:"🌧️ Rain", 4:"⛈️ Heavy"
    })
    daily['Total Rentals']  = daily['total_rentals']
    daily['Peak Hour Rentals'] = daily['peak_rentals']

    # Summary metrics row
    best_day  = daily.loc[daily['Total Rentals'].idxmax()]
    worst_day = daily.loc[daily['Total Rentals'].idxmin()]
    ca, cb, cc = st.columns(3)
    ca.metric("Best Day",  best_day['Day'],  f"{best_day['Total Rentals']:,} rentals")
    cb.metric("Worst Day", worst_day['Day'], f"{worst_day['Total Rentals']:,} rentals")
    cc.metric("7-Day Total", f"{daily['Total Rentals'].sum():,} bikes")

    # Bar chart
    st.bar_chart(daily.set_index('Day')['Total Rentals'], use_container_width=True)

    # Table
    display_cols = ['Day', 'Weather', 'Avg Temp (°C)', 'Avg Humidity', 'Total Rentals', 'Peak Hour Rentals']
    st.dataframe(daily[display_cols], use_container_width=True, hide_index=True)
