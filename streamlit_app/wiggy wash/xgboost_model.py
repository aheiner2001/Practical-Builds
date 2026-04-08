# wiggy_wash_app.py  –  Wiggy Wash Forecasting Dashboard
# Run with:  streamlit run wiggy_wash_app.py
st.write("App starting...")
import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import re
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Wiggy Wash · Forecast Dashboard",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}
h1, h2, h3 { font-family: 'Space Mono', monospace; }

.stApp { background: #0d1117; color: #e6edf3; }

.metric-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 18px 22px;
    text-align: center;
}
.metric-card .label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #8b949e;
    margin-bottom: 6px;
}
.metric-card .value {
    font-family: 'Space Mono', monospace;
    font-size: 28px;
    font-weight: 700;
    color: #58a6ff;
}
.metric-card .sub {
    font-size: 12px;
    color: #8b949e;
    margin-top: 4px;
}

.flag-chip {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
    margin: 2px;
}
.flag-upsell  { background: #1a3a1a; color: #56d364; border: 1px solid #238636; }
.flag-warning { background: #3a1a00; color: #f0883e; border: 1px solid #9e4a00; }
.flag-info    { background: #0d2a4a; color: #58a6ff; border: 1px solid #1f6feb; }

[data-testid="stSidebar"] {
    background: #161b22;
    border-right: 1px solid #30363d;
}
.stSelectbox label, .stDateInput label, .stSlider label {
    color: #8b949e !important;
    font-size: 12px !important;
    text-transform: uppercase;
    letter-spacing: 1px;
}
div[data-testid="metric-container"] {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 12px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def metric_card(label, value, sub=""):
    st.markdown(f"""
    <div class="metric-card">
        <div class="label">{label}</div>
        <div class="value">{value}</div>
        <div class="sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

def flag_chip(text, kind="info"):
    return f'<span class="flag-chip flag-{kind}">{text}</span>'

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING & MODEL  (100% original logic, unchanged)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading & training model…")
def load_and_train():

    # ── 1. RAW DATA ──────────────────────────────────────────────────────────
    def clean_and_tag_dates(url):
        df_raw = pd.read_csv(url, header=None)
        location = df_raw.iloc[3, 0] if "Location" in str(df_raw.iloc[3, 0]) else "UT0032"
        col_names = [
            'Time Interval', '# Cars (Total)', 'drop1', '$ Sales (Total)',
            '$ Sales (Total/Car)', 'drop2', '$ Sales (Base)', '# Cars (Extra)',
            '$ Sales (Extra)', '$ Sales (Ext/Car)', 'drop3', '% Cars (Extra)',
            '# Cars (Inv)', '$ Sales (Inv)'
        ]
        df_raw.columns = col_names
        date_pattern = r'\d{2}/\d{2}/\d{4}'
        df_raw['Date'] = df_raw['Time Interval'].apply(
            lambda x: x if re.match(date_pattern, str(x)) else None)
        df_raw['Date'] = df_raw['Date'].ffill()
        df_clean = df_raw[df_raw['Time Interval'].str.contains('am|pm', na=False, case=False)].copy()
        df_clean['Location'] = location
        df_clean = df_clean.drop(columns=[c for c in df_clean.columns if 'drop' in c])
        numeric_cols = df_clean.columns.drop(['Time Interval', 'Date', 'Location'])
        for col in numeric_cols:
            df_clean[col] = pd.to_numeric(
                df_clean[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        return df_clean

    urls = [
        'https://raw.githubusercontent.com/aheiner2001/Machine-Learning/refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data%20(3).csv',
        'https://raw.githubusercontent.com/aheiner2001/Machine-Learning/refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data.csv',
        'https://raw.githubusercontent.com/aheiner2001/Machine-Learning/refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data%20(4).csv',
        'https://raw.githubusercontent.com/aheiner2001/Machine-Learning/refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data%20(5).csv',
        'https://raw.githubusercontent.com/aheiner2001/Machine-Learning/refs/heads/main/wiggy/Traffic%20Report%20-%20Sales%20Data%20(6).csv',
    ]
    cleaned_dataframes = [clean_and_tag_dates(url) for url in urls]
    df = pd.concat(cleaned_dataframes, ignore_index=True)

    # ── 2. COLUMN RENAME ─────────────────────────────────────────────────────
    column_mapping = {
        'Time Interval': 'time_interval',
        '# Cars (Total)': 'cars_total',
        '$ Sales (Total)': 'sales_total',
        'Date': 'day'
    }
    df = df.rename(columns=column_mapping)
    df = df[list(column_mapping.values())].copy()

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

    df['hour_of_day'] = df['time_interval'].apply(parse_hour)
    df['date'] = pd.to_datetime(df['day'], errors='coerce')
    df['datetime'] = df['date'] + pd.to_timedelta(df['hour_of_day'], unit='h')
    df['hour_sin'] = np.sin(2 * np.pi * df['hour_of_day'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour_of_day'] / 24)

    for col in ['cars_total']:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str).str.replace(r'[$,]', '', regex=True)
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['car_count'] = df['cars_total']
    df['Location'] = 'UT0032'

    # ── 3. WEATHER ───────────────────────────────────────────────────────────
    params = {
        'latitude': 40.1618, 'longitude': -111.6348,
        'start_date': df['date'].min().strftime('%Y-%m-%d'),
        'end_date':   df['date'].max().strftime('%Y-%m-%d'),
        'hourly': ['temperature_2m', 'precipitation', 'wind_speed_10m', 'weather_code'],
        'daily':  ['temperature_2m_max', 'temperature_2m_min', 'precipitation_sum', 'wind_speed_10m_max'],
        'timezone': 'America/Denver',
        'temperature_unit': 'fahrenheit',
        'precipitation_unit': 'inch',
        'wind_speed_unit': 'mph'
    }
    response = requests.get('https://archive-api.open-meteo.com/v1/archive', params=params)
    w_data = response.json()

    hourly_weather = pd.DataFrame({
        'datetime': pd.to_datetime(w_data['hourly']['time']),
        'hour_temp': w_data['hourly']['temperature_2m'],
        'hour_precip': w_data['hourly']['precipitation'],
        'hour_wind': w_data['hourly']['wind_speed_10m'],
        'weather_code': w_data['hourly']['weather_code']
    })
    daily_weather = pd.DataFrame({
        'date': pd.to_datetime(w_data['daily']['time']),
        'day_temp_max': w_data['daily']['temperature_2m_max'],
        'day_precip_sum': w_data['daily']['precipitation_sum'],
        'day_wind_max': w_data['daily']['wind_speed_10m_max']
    })

    df = pd.merge(df, hourly_weather, on='datetime', how='left')
    df = pd.merge(df, daily_weather, on='date', how='left')
    df = df.sort_values(['date', 'hour_of_day']).reset_index(drop=True)

    # ── 4. FEATURE ENGINEERING ───────────────────────────────────────────────
    df['hour_sin'] = np.sin(2 * np.pi * df['hour_of_day'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour_of_day'] / 24)
    df['day_num']  = df['date'].dt.dayofweek
    df['month_sin'] = np.sin(2 * np.pi * df['date'].dt.month / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['date'].dt.month / 12)

    df['precip_yesterday']  = df['day_precip_sum'].shift(1)
    df['precip_2days_ago']  = df['day_precip_sum'].shift(2)
    df['precip_3days_ago']  = df['day_precip_sum'].shift(3)
    df['precip_last_7days'] = df['day_precip_sum'].rolling(7).sum().shift(1)

    holidays = pd.to_datetime([
        '2025-01-01','2025-01-20','2025-02-17','2025-05-26','2025-06-19','2025-07-04',
        '2025-09-01','2025-10-13','2025-11-11','2025-11-27','2025-12-25',
        '2026-01-01','2026-01-19','2026-02-16','2026-05-25','2026-06-19','2026-07-03',
        '2026-09-07','2026-10-12','2026-11-11','2026-11-26','2026-12-25'
    ])
    days_after_holidays = holidays + pd.to_timedelta(1, unit='D')
    df['is_holiday']          = df['date'].isin(holidays).astype(int)
    df['is_day_after_holiday']= df['date'].isin(days_after_holidays).astype(int)

    m, d = df['date'].dt.month, df['date'].dt.day
    df['is_christmas_week']      = ((m==12)&(d>=23)).astype(int)
    df['is_christmas_season']    = ((m==12)&(d>=15)).astype(int)
    df['is_new_years_week']      = ((m==1)&(d<=7)).astype(int)
    df['is_holiday_week']        = ((df['is_christmas_week']==1)|(df['is_new_years_week']==1)).astype(int)
    df['is_pre_christmas_rush']  = ((m==12)&(d>=15)&(d<=22)).astype(int)
    df['is_post_christmas_slow'] = (((m==12)&(d>=26))|((m==1)&(d<=3))).astype(int)
    df['is_early_december']      = ((m==12)&(d<=14)).astype(int)
    df['is_post_thanksgiving']   = ((m==11)&(d>=28)&(d<=30)).astype(int)
    df['days_left_in_month']     = df['date'].dt.days_in_month - df['date'].dt.day

    df['is_thanksgiving'] = (
        (df['date'].dt.month==11)&(df['date'].dt.day>=22)&
        (df['date'].dt.day<=28)&(df['date'].dt.weekday==3)).astype(int)
    df['is_thanksgiving_saturday'] = (
        (df['date'].dt.month==11)&(df['date'].dt.day>=24)&
        (df['date'].dt.day<=30)&(df['date'].dt.weekday==5)).astype(int)
    df['is_pioneer_day']    = ((df['date'].dt.month==7)&(df['date'].dt.day==24)).astype(int)

    df['wind_yesterday']    = df['day_wind_max'].shift(1)
    df['wind_2days_ago']    = df['day_wind_max'].shift(2)
    df['wind_3days_ago']    = df['day_wind_max'].shift(3)
    df['rolling_7day_wind'] = df['day_wind_max'].rolling(7).mean().shift(1).round(1)
    df['rolling_3day_wind'] = df['day_wind_max'].rolling(3).mean().shift(1).round(1)
    df['post_valentines_day']= ((df['date'].dt.month==2)&(df['date'].dt.day>=14)&(df['date'].dt.day<=21)).astype(int)

    df['is_summer_break'] = (
        (df['date'].dt.month==6)|(df['date'].dt.month==7)|
        ((df['date'].dt.month==5)&(df['date'].dt.day>=27))|
        ((df['date'].dt.month==8)&(df['date'].dt.day<=18))).astype(int)
    df['is_back_to_school'] = (
        (df['date'].dt.month==8)&(df['date'].dt.day>=12)&(df['date'].dt.day<=31)).astype(int)
    df['is_spring_break_k12'] = (
        (df['date'].dt.month==3)&(df['date'].dt.day>=17)&(df['date'].dt.day<=28)).astype(int)
    df['is_fall_break_k12'] = (
        (df['date'].dt.month==10)&(df['date'].dt.day>=13)&(df['date'].dt.day<=18)).astype(int)
    df['is_university_in_session'] = (
        ((df['date'].dt.month==8)&(df['date'].dt.day>=18)|
         df['date'].dt.month.isin([9,10,11])|
         (df['date'].dt.month==12)&(df['date'].dt.day<=13))|
        ((df['date'].dt.month==1)&(df['date'].dt.day>=13)|
         df['date'].dt.month.isin([2,3,4]))).astype(int)
    df['is_university_winter_break'] = (
        ((df['date'].dt.month==12)&(df['date'].dt.day>=14))|
        ((df['date'].dt.month==1)&(df['date'].dt.day<=12))).astype(int)
    df['is_spring_break_university'] = (
        (df['date'].dt.month==3)&(df['date'].dt.day>=16)&(df['date'].dt.day<=22)).astype(int)
    df['is_finals_week'] = (
        ((df['date'].dt.month==12)&(df['date'].dt.day>=8)&(df['date'].dt.day<=13))|
        ((df['date'].dt.month==4)&(df['date'].dt.day>=22)&(df['date'].dt.day<=30))).astype(int)
    df['is_university_thanksgiving_break'] = (
        (df['date'].dt.month==11)&(df['date'].dt.day>=24)&(df['date'].dt.day<=30)).astype(int)

    def get_weather_cat(code):
        if code in [0,1,2,3]: return 'clear'
        if code in [51,53,55,61,63,65]: return 'rain'
        if code in [71,73,75,85,86]: return 'snow'
        return 'other'
    df['weather_cat'] = df['weather_code'].apply(get_weather_cat)

    df['is_rainy_day'] = (df['day_precip_sum'] > 0.05).astype(int)
    day_groups = df['is_rainy_day'].cumsum()
    df['days_since_last_rain'] = df.groupby(day_groups).cumcount()
    df.loc[df['is_rainy_day']==1, 'days_since_last_rain'] = 0

    # ── 5. TRAINING PREP ─────────────────────────────────────────────────────
    df['car_count'] = pd.to_numeric(df['cars_total'], errors='coerce').fillna(0)

    df['grocery_peak']   = ((df['day_num']==5)&(df['hour_of_day'].between(10,14))).astype(int)
    df['commuter']       = ((df['day_num']<5)&(df['hour_of_day']==17)).astype(int)
    df['is_monday']      = (df['day_num']==0).astype(int)
    df['is_recovery_day']= ((df['days_since_last_rain']==1)&(df['hour_temp']>32)).astype(int)
    df['pioneer_weekend']= ((df['date'].dt.month==7)&(df['date'].dt.day.between(24,27))).astype(int)
    df['is_christmas_eve']= ((df['date'].dt.month==12)&(df['date'].dt.day==24)).astype(int)
    df['rolling_7day_temp']= df['day_temp_max'].rolling(window=7).mean().shift(1)
    df['temp_anomaly']   = df['hour_temp'] - df.groupby(df['date'].dt.month)['hour_temp'].transform('mean')
    df['hour_pct_of_day']= df.groupby(['day_num','hour_of_day'])['car_count'].transform('mean') / \
                           df.groupby(['day_num'])['car_count'].transform('mean')
    df['is_heavy_holiday_shopping']= ((df['date'].dt.month==12)&(df['date'].dt.day.between(15,23))).astype(int)
    df['is_january_reset']= ((df['date'].dt.month==1)&(df['date'].dt.day.between(5,12))&(df['day_num'].isin([4,5]))).astype(int)
    df['is_pay_day']     = (df['date'].dt.day.isin([1,15])).astype(int)
    df['is_upsell_weather']= ((df['hour_temp']>60)&(df['hour_precip']==0)).astype(int)
    df['is_peak_holiday_shopping']= ((df['date'].dt.month==12)&(df['date'].dt.day.between(15,23))).astype(int)
    df['is_first_thaw']  = ((df['date'].dt.month==2)&(df['temp_anomaly']>15)).astype(int)
    df['is_jan_back_to_school']= ((df['date'].dt.month==1)&(df['date'].dt.day.between(5,12))).astype(int)

    df_model = df[(df['car_count']>2)&(df['day_num']!=6)].copy()
    df_model['car_count_smoothed'] = df_model['car_count'].rolling(window=2, min_periods=1).mean()

    features = [
        'hour_of_day','hour_sin','hour_cos','day_num',
        'hour_temp','hour_precip','hour_wind',
        'precip_yesterday','precip_last_7days',
        'days_since_last_rain',
        'is_holiday','is_day_after_holiday',
        'is_summer_break','is_university_in_session',
        'is_pre_christmas_rush','days_left_in_month',
        'month_sin','month_cos',
        'grocery_peak','commuter','is_monday','is_recovery_day',
        'pioneer_weekend','is_christmas_eve',
        'hour_pct_of_day','is_peak_holiday_shopping',
        'is_first_thaw','is_jan_back_to_school','is_pay_day'
    ]

    df_model = df_model.dropna(subset=features)
    y = np.log1p(df_model['car_count_smoothed'])
    X = pd.get_dummies(df_model[features + ['weather_cat']], drop_first=True)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    max_date = df_model['date'].max()
    weights  = np.exp(-0.005*(max_date - df_model.loc[X_train.index,'date']).dt.days)

    model = GradientBoostingRegressor(
    n_estimators=600,      # same idea
    learning_rate=0.05,    # same
    max_depth=7,           # controls tree depth
    min_samples_split=5,
    min_samples_leaf=3,
    subsample=0.8,         # like stochastic boosting (important!)
    random_state=42
)

    model.fit(X_train, y_train, sample_weight=weights)

    # ── 6. EVAL ──────────────────────────────────────────────────────────────
    preds_raw = np.expm1(model.predict(X_test))
    actuals   = np.expm1(y_test)
    residuals = actuals - preds_raw

    mae  = mean_absolute_error(actuals, preds_raw)
    rmse = np.sqrt(mean_squared_error(actuals, preds_raw))
    r2   = r2_score(actuals, preds_raw)
    mape = np.mean(np.abs((actuals - preds_raw)/(actuals + 1e-9)))*100

    if 'day_name' not in df_model.columns:
        df_model['day_name'] = df_model['date'].dt.day_name()

    test_df = pd.DataFrame({
        'date':        df_model.loc[y_test.index,'date'].values,
        'day_of_week': df_model.loc[y_test.index,'day_name'].values,
        'hour_of_day': df_model.loc[y_test.index,'hour_of_day'].values,
        'actual':      actuals.values,
        'predicted':   preds_raw,
        'error':       residuals.values,
        'abs_error':   np.abs(residuals.values),
        'hour_temp':   df_model.loc[y_test.index,'hour_temp'].values,
        'hour_precip': df_model.loc[y_test.index,'hour_precip'].values,
        'is_pay_day':  df_model.loc[y_test.index,'is_pay_day'].values,
        'is_upsell_weather': df_model.loc[y_test.index,'is_upsell_weather'].values,
    }).sort_values('date')

    feat_imp = pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False)

    return df, df_model, model, X, test_df, feat_imp, mae, rmse, r2, mape

# ─────────────────────────────────────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────────────────────────────────────
with st.spinner("🚗 Loading Wiggy Wash data & training model…"):
    df, df_model, model, X, test_df, feat_imp, mae, rmse, r2, mape = load_and_train()

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🚗 Wiggy Wash")
    st.markdown("---")
    page = st.radio("Navigate", [
        "📊 Weekly Overview",
        "📅 Day Breakdown",
        "🌤️ Weather Analysis",
        "📈 Model Performance",
        "💰 Upsell Flags",
    ])
    st.markdown("---")
    st.markdown("**Model Info**")
    st.markdown(f"🔹 Training rows: `{len(df_model):,}`")
    st.markdown(f"🔹 Date range: `{df_model['date'].min().date()}` → `{df_model['date'].max().date()}`")
    st.markdown(f"🔹 Location: `UT0032`")

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: WEEKLY OVERVIEW
# ─────────────────────────────────────────────────────────────────────────────
if page == "📊 Weekly Overview":
    st.title("Weekly Overview")
    st.caption("Average predicted and actual hourly car volume by day of week")

    # Top metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("MAE", f"{mae:.1f}", "cars / hour")
    with c2: metric_card("RMSE", f"{rmse:.1f}", "cars / hour")
    with c3: metric_card("R²", f"{r2:.3f}", "model fit")
    with c4: metric_card("MAPE", f"{mape:.1f}%", "avg % error")

    st.markdown("---")

    # Heatmap: avg cars by day × hour
    day_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
    pivot = df_model.groupby(['day_name','hour_of_day'])['car_count'].mean().reset_index()
    pivot = pivot[pivot['day_name'].isin(day_order)]
    pivot_wide = pivot.pivot(index='day_name', columns='hour_of_day', values='car_count')
    pivot_wide = pivot_wide.reindex(day_order)

    fig_heat = go.Figure(data=go.Heatmap(
        z=pivot_wide.values,
        x=[f"{h}:00" for h in pivot_wide.columns],
        y=pivot_wide.index.tolist(),
        colorscale='Blues',
        hoverongaps=False,
        colorbar=dict(title="Avg Cars", tickfont=dict(color='#8b949e'), titlefont=dict(color='#8b949e')),
    ))
    fig_heat.update_layout(
        title="Average Cars by Day & Hour",
        paper_bgcolor='#0d1117', plot_bgcolor='#161b22',
        font=dict(color='#e6edf3'),
        xaxis=dict(title="Hour of Day", gridcolor='#30363d'),
        yaxis=dict(title=""),
        height=320,
        margin=dict(t=50, b=40, l=10, r=10)
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    # Bar: avg cars by day
    day_avg = df_model[df_model['day_name'].isin(day_order)].groupby('day_name')['car_count'].sum().reindex(day_order)
    fig_bar = go.Figure(go.Bar(
        x=day_avg.index, y=day_avg.values,
        marker_color=['#58a6ff']*5 + ['#3fb950'],
        text=[f"{v:.0f}" for v in day_avg.values],
        textposition='outside',
        textfont=dict(color='#8b949e', size=11),
    ))
    fig_bar.update_layout(
        title="Total Cars by Day of Week (All Data)",
        paper_bgcolor='#0d1117', plot_bgcolor='#161b22',
        font=dict(color='#e6edf3'),
        xaxis=dict(gridcolor='#30363d'),
        yaxis=dict(gridcolor='#30363d', title="Cars"),
        height=280,
        margin=dict(t=50, b=20, l=10, r=10),
        showlegend=False,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    st.info("💡 Click **Day Breakdown** in the sidebar to drill into any specific day with hourly predictions.")

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: DAY BREAKDOWN
# ─────────────────────────────────────────────────────────────────────────────
elif page == "📅 Day Breakdown":
    st.title("Day Breakdown")
    st.caption("Select a day to see hourly predictions, actual counts, and contextual flags")

    # Date selector
    available_dates = sorted(test_df['date'].dt.date.unique())
    selected_date = st.selectbox(
        "Select a date",
        options=available_dates,
        index=len(available_dates)-1,
        format_func=lambda d: d.strftime("%A, %b %d %Y")
    )

    day_data = test_df[test_df['date'].dt.date == selected_date].sort_values('hour_of_day')

    if day_data.empty:
        st.warning("No test data for this date. Try another.")
    else:
        dow   = pd.Timestamp(selected_date).day_name()
        temp  = day_data['hour_temp'].mean()
        precip= day_data['hour_precip'].sum()
        upsell= int(day_data['is_upsell_weather'].any())
        payday= int(day_data['is_pay_day'].any())

        # Context flags
        flags_html = ""
        if upsell: flags_html += flag_chip("☀️ Upsell Weather", "upsell")
        if payday: flags_html += flag_chip("💵 Pay Day", "upsell")
        if precip > 0.1: flags_html += flag_chip(f"🌧️ Rain {precip:.2f}\"", "warning")
        if temp < 32: flags_html += flag_chip(f"❄️ Freezing {temp:.0f}°F", "warning")
        if temp > 75: flags_html += flag_chip(f"🔆 Hot {temp:.0f}°F", "info")
        if not flags_html: flags_html = flag_chip("No special flags", "info")

        col1, col2 = st.columns([3,1])
        with col1:
            st.markdown(f"### {dow}, {selected_date.strftime('%B %d, %Y')}")
            st.markdown(flags_html, unsafe_allow_html=True)
        with col2:
            mae_day = mean_absolute_error(day_data['actual'], day_data['predicted'])
            metric_card("Day MAE", f"{mae_day:.1f}", "cars/hour")

        # Hourly chart
        fig_day = go.Figure()
        fig_day.add_trace(go.Bar(
            x=day_data['hour_of_day'],
            y=day_data['actual'],
            name='Actual',
            marker_color='#58a6ff',
            opacity=0.7,
        ))
        fig_day.add_trace(go.Scatter(
            x=day_data['hour_of_day'],
            y=day_data['predicted'],
            name='Predicted',
            mode='lines+markers',
            line=dict(color='#f0883e', width=2.5),
            marker=dict(size=7),
        ))
        fig_day.add_trace(go.Bar(
            x=day_data['hour_of_day'],
            y=day_data['error'],
            name='Error',
            marker_color=['#56d364' if e>=0 else '#f85149' for e in day_data['error']],
            opacity=0.5,
            yaxis='y2',
        ))
        fig_day.update_layout(
            title=f"Hourly Cars – {selected_date.strftime('%A %b %d')}",
            paper_bgcolor='#0d1117', plot_bgcolor='#161b22',
            font=dict(color='#e6edf3'),
            xaxis=dict(title="Hour of Day", gridcolor='#30363d',
                       tickvals=list(day_data['hour_of_day']),
                       ticktext=[f"{h}:00" for h in day_data['hour_of_day']]),
            yaxis=dict(title="Cars", gridcolor='#30363d'),
            yaxis2=dict(title="Error", overlaying='y', side='right',
                        gridcolor='#30363d', showgrid=False),
            legend=dict(bgcolor='#161b22', bordercolor='#30363d'),
            height=380,
            margin=dict(t=50, b=40, l=10, r=60),
            barmode='overlay',
        )
        st.plotly_chart(fig_day, use_container_width=True)

        # Hourly table
        tbl = day_data[['hour_of_day','actual','predicted','error','hour_temp','hour_precip','is_upsell_weather']].copy()
        tbl.columns = ['Hour','Actual','Predicted','Error','Temp °F','Precip in','Upsell?']
        tbl['Hour']      = tbl['Hour'].apply(lambda h: f"{h}:00")
        tbl['Actual']    = tbl['Actual'].round(1)
        tbl['Predicted'] = tbl['Predicted'].round(1)
        tbl['Error']     = tbl['Error'].round(1)
        tbl['Temp °F']   = tbl['Temp °F'].round(1)
        tbl['Upsell?']   = tbl['Upsell?'].apply(lambda x: "✅" if x else "—")
        st.dataframe(tbl, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: WEATHER ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────
elif page == "🌤️ Weather Analysis":
    st.title("Weather Analysis")
    st.caption("How weather conditions correlate with car volume")

    col1, col2 = st.columns(2)

    # Scatter: temp vs cars
    with col1:
        fig_temp = px.scatter(
            df_model.sample(min(3000, len(df_model)), random_state=1),
            x='hour_temp', y='car_count',
            color='weather_cat',
            color_discrete_map={'clear':'#58a6ff','rain':'#f85149','snow':'#d2a8ff','other':'#8b949e'},
            opacity=0.45,
            title="Temperature vs Car Count",
            labels={'hour_temp':'Temp (°F)','car_count':'Cars'},
            trendline='lowess',
        )
        fig_temp.update_layout(
            paper_bgcolor='#0d1117', plot_bgcolor='#161b22',
            font=dict(color='#e6edf3'),
            legend=dict(bgcolor='#161b22', bordercolor='#30363d'),
            height=320, margin=dict(t=50,b=30,l=10,r=10)
        )
        st.plotly_chart(fig_temp, use_container_width=True)

    # Box: weather category vs cars
    with col2:
        fig_box = px.box(
            df_model[df_model['weather_cat'].isin(['clear','rain','snow'])],
            x='weather_cat', y='car_count',
            color='weather_cat',
            color_discrete_map={'clear':'#58a6ff','rain':'#f85149','snow':'#d2a8ff'},
            title="Cars by Weather Condition",
            labels={'weather_cat':'Condition','car_count':'Cars'},
        )
        fig_box.update_layout(
            paper_bgcolor='#0d1117', plot_bgcolor='#161b22',
            font=dict(color='#e6edf3'),
            showlegend=False,
            height=320, margin=dict(t=50,b=30,l=10,r=10)
        )
        st.plotly_chart(fig_box, use_container_width=True)

    # Precipitation lag bars
    lag_df = pd.DataFrame({
        'Lag': ['Same Day','Yesterday','2 Days Ago','3 Days Ago'],
        'Corr': [
            df_model['day_precip_sum'].corr(df_model['car_count']),
            df_model['precip_yesterday'].corr(df_model['car_count']),
            df_model['precip_2days_ago'].corr(df_model['car_count']),
            df_model['precip_3days_ago'].corr(df_model['car_count']),
        ]
    })
    fig_lag = go.Figure(go.Bar(
        x=lag_df['Lag'], y=lag_df['Corr'],
        marker_color=['#f85149' if c<0 else '#56d364' for c in lag_df['Corr']],
        text=[f"{c:.3f}" for c in lag_df['Corr']],
        textposition='outside',
        textfont=dict(color='#8b949e'),
    ))
    fig_lag.update_layout(
        title="Precipitation Lag Correlation with Car Count",
        paper_bgcolor='#0d1117', plot_bgcolor='#161b22',
        font=dict(color='#e6edf3'),
        yaxis=dict(title="Pearson r", gridcolor='#30363d', zeroline=True, zerolinecolor='#30363d'),
        xaxis=dict(gridcolor='#30363d'),
        height=280, margin=dict(t=50,b=30,l=10,r=10)
    )
    st.plotly_chart(fig_lag, use_container_width=True)

    # Days since last rain
    fig_dslr = px.scatter(
        df_model[df_model['days_since_last_rain']<=14],
        x='days_since_last_rain', y='car_count',
        opacity=0.3,
        trendline='lowess',
        title="Days Since Last Rain vs Car Volume",
        labels={'days_since_last_rain':'Days Since Rain','car_count':'Cars'},
        color_discrete_sequence=['#58a6ff'],
    )
    fig_dslr.update_layout(
        paper_bgcolor='#0d1117', plot_bgcolor='#161b22',
        font=dict(color='#e6edf3'),
        height=280, margin=dict(t=50,b=30,l=10,r=10)
    )
    st.plotly_chart(fig_dslr, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: MODEL PERFORMANCE
# ─────────────────────────────────────────────────────────────────────────────
elif page == "📈 Model Performance":
    st.title("Model Performance")
    st.caption("XGBoost evaluation metrics, residuals, and feature importance")

    # Metric row
    c1,c2,c3,c4 = st.columns(4)
    with c1: metric_card("MAE",  f"{mae:.1f}",  "avg cars off")
    with c2: metric_card("RMSE", f"{rmse:.1f}", "root mean sq err")
    with c3: metric_card("R²",   f"{r2:.3f}",   "variance explained")
    with c4: metric_card("MAPE", f"{mape:.1f}%","mean abs % error")

    st.markdown("---")

    col1, col2 = st.columns(2)

    # Actual vs Predicted scatter
    with col1:
        fig_scatter = go.Figure()
        fig_scatter.add_trace(go.Scatter(
            x=test_df['actual'], y=test_df['predicted'],
            mode='markers', marker=dict(color='#58a6ff', opacity=0.4, size=5),
            name='Predictions'
        ))
        mn, mx = test_df['actual'].min(), test_df['actual'].max()
        fig_scatter.add_trace(go.Scatter(
            x=[mn,mx], y=[mn,mx], mode='lines',
            line=dict(color='#f85149', dash='dash'), name='Perfect'
        ))
        fig_scatter.update_layout(
            title="Actual vs Predicted",
            paper_bgcolor='#0d1117', plot_bgcolor='#161b22',
            font=dict(color='#e6edf3'),
            xaxis=dict(title="Actual", gridcolor='#30363d'),
            yaxis=dict(title="Predicted", gridcolor='#30363d'),
            legend=dict(bgcolor='#161b22'),
            height=320, margin=dict(t=50,b=30,l=10,r=10)
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    # Residual histogram
    with col2:
        fig_hist = go.Figure(go.Histogram(
            x=test_df['error'], nbinsx=30,
            marker_color='#58a6ff', opacity=0.8
        ))
        fig_hist.add_vline(x=0, line_color='#f85149', line_dash='dash')
        fig_hist.update_layout(
            title="Residual Distribution",
            paper_bgcolor='#0d1117', plot_bgcolor='#161b22',
            font=dict(color='#e6edf3'),
            xaxis=dict(title="Error (actual − predicted)", gridcolor='#30363d'),
            yaxis=dict(title="Count", gridcolor='#30363d'),
            height=320, margin=dict(t=50,b=30,l=10,r=10)
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    # Error by day of week
    day_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
    day_errors = test_df.groupby('day_of_week')['abs_error'].mean().reindex(day_order)
    fig_day_err = go.Figure(go.Bar(
        x=day_errors.index, y=day_errors.values,
        marker_color='#58a6ff',
        text=[f"{v:.1f}" for v in day_errors.values],
        textposition='outside', textfont=dict(color='#8b949e'),
    ))
    fig_day_err.update_layout(
        title="Avg Absolute Error by Day of Week",
        paper_bgcolor='#0d1117', plot_bgcolor='#161b22',
        font=dict(color='#e6edf3'),
        yaxis=dict(title="MAE (cars)", gridcolor='#30363d'),
        xaxis=dict(gridcolor='#30363d'),
        height=280, margin=dict(t=50,b=30,l=10,r=10)
    )
    st.plotly_chart(fig_day_err, use_container_width=True)

    # Feature importance
    top_feats = feat_imp.head(15).sort_values()
    fig_fi = go.Figure(go.Bar(
        x=top_feats.values, y=top_feats.index,
        orientation='h', marker_color='#58a6ff'
    ))
    fig_fi.update_layout(
        title="Top 15 Feature Importances",
        paper_bgcolor='#0d1117', plot_bgcolor='#161b22',
        font=dict(color='#e6edf3'),
        xaxis=dict(title="Importance", gridcolor='#30363d'),
        yaxis=dict(gridcolor='#30363d'),
        height=420, margin=dict(t=50,b=30,l=10,r=10)
    )
    st.plotly_chart(fig_fi, use_container_width=True)

    # Worst predictions table
    st.subheader("20 Worst Predictions")
    worst = test_df.sort_values('abs_error', ascending=False).head(20)[
        ['date','day_of_week','hour_of_day','actual','predicted','abs_error']].copy()
    worst['date'] = worst['date'].dt.strftime('%Y-%m-%d')
    worst.columns = ['Date','Day','Hour','Actual','Predicted','Abs Error']
    worst['Actual']    = worst['Actual'].round(1)
    worst['Predicted'] = worst['Predicted'].round(1)
    worst['Abs Error'] = worst['Abs Error'].round(1)
    st.dataframe(worst, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: UPSELL FLAGS
# ─────────────────────────────────────────────────────────────────────────────
elif page == "💰 Upsell Flags":
    st.title("Upsell Opportunity Flags")
    st.caption("Conditions that maximize upsell conversion: warm temp, no rain, payday, high traffic")

    # Summary metrics
    upsell_days = df_model[df_model['is_upsell_weather']==1]
    non_upsell  = df_model[df_model['is_upsell_weather']==0]
    payday_days = df_model[df_model['is_pay_day']==1]

    c1,c2,c3 = st.columns(3)
    with c1: metric_card("Avg Cars (Upsell Wx)", f"{upsell_days['car_count'].mean():.1f}", "per hour")
    with c2: metric_card("Avg Cars (Normal)",   f"{non_upsell['car_count'].mean():.1f}",  "per hour")
    with c3: metric_card("Avg Cars (Pay Day)",  f"{payday_days['car_count'].mean():.1f}", "per hour")

    st.markdown("---")

    # Day × Hour upsell heatmap
    day_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
    upsell_heat = upsell_days.groupby(['day_name','hour_of_day'])['car_count'].mean().reset_index()
    upsell_heat = upsell_heat[upsell_heat['day_name'].isin(day_order)]
    uph_wide = upsell_heat.pivot(index='day_name', columns='hour_of_day', values='car_count').reindex(day_order)

    fig_up = go.Figure(data=go.Heatmap(
        z=uph_wide.values,
        x=[f"{h}:00" for h in uph_wide.columns],
        y=uph_wide.index.tolist(),
        colorscale='YlGn',
        colorbar=dict(title="Avg Cars", tickfont=dict(color='#8b949e'), titlefont=dict(color='#8b949e')),
    ))
    fig_up.update_layout(
        title="Avg Cars During Upsell-Favorable Weather (Warm + Dry)",
        paper_bgcolor='#0d1117', plot_bgcolor='#161b22',
        font=dict(color='#e6edf3'),
        height=320, margin=dict(t=50,b=40,l=10,r=10)
    )
    st.plotly_chart(fig_up, use_container_width=True)

    # Compare upsell vs non-upsell by hour
    comp = df_model.groupby(['is_upsell_weather','hour_of_day'])['car_count'].mean().reset_index()
    fig_comp = go.Figure()
    for val, label, color in [(1,"Upsell Weather","#56d364"),(0,"Normal","#8b949e")]:
        sub = comp[comp['is_upsell_weather']==val]
        fig_comp.add_trace(go.Scatter(
            x=sub['hour_of_day'], y=sub['car_count'],
            mode='lines+markers', name=label,
            line=dict(color=color, width=2.5),
            marker=dict(size=6),
        ))
    fig_comp.update_layout(
        title="Hourly Volume: Upsell Weather vs Normal",
        paper_bgcolor='#0d1117', plot_bgcolor='#161b22',
        font=dict(color='#e6edf3'),
        xaxis=dict(title="Hour", gridcolor='#30363d'),
        yaxis=dict(title="Avg Cars", gridcolor='#30363d'),
        legend=dict(bgcolor='#161b22'),
        height=280, margin=dict(t=50,b=30,l=10,r=10)
    )
    st.plotly_chart(fig_comp, use_container_width=True)

    # Weekly predicted upsell calendar from test set
    st.subheader("Predicted Upsell Opportunities (Test Set)")
    st.caption("Days with ≥4 consecutive upsell-favorable hours in peak window (10 AM – 5 PM)")

    peak_upsell = test_df[
        (test_df['hour_of_day'].between(10,17)) &
        (test_df['is_upsell_weather']==1)
    ].groupby('date').agg(
        upsell_hours=('is_upsell_weather','sum'),
        avg_predicted=('predicted','mean'),
        avg_temp=('hour_temp','mean'),
        payday=('is_pay_day','max')
    ).reset_index()
    peak_upsell = peak_upsell[peak_upsell['upsell_hours']>=4].sort_values('date')

    if peak_upsell.empty:
        st.info("No strong upsell days found in test set.")
    else:
        peak_upsell['date_str']  = peak_upsell['date'].dt.strftime('%Y-%m-%d')
        peak_upsell['day_name']  = peak_upsell['date'].dt.day_name()
        peak_upsell['Payday']    = peak_upsell['payday'].apply(lambda x: "💵 Yes" if x else "—")
        peak_upsell['Pred Cars'] = peak_upsell['avg_predicted'].round(1)
        peak_upsell['Temp °F']   = peak_upsell['avg_temp'].round(1)
        display = peak_upsell[['date_str','day_name','upsell_hours','Pred Cars','Temp °F','Payday']]
        display.columns = ['Date','Day','Upsell Hours','Pred Cars/hr','Avg Temp °F','Pay Day?']
        st.dataframe(display, use_container_width=True, hide_index=True)

    # Upsell intensity levels
    st.subheader("Upsell Level Guide")
    st.markdown("""
    | Level | Criteria | Action |
    |-------|----------|--------|
    | 🟢 **High** | Warm (>70°F), dry, payday, Sat/Fri | Push premium packages aggressively |
    | 🟡 **Medium** | Warm (60–70°F), dry, mid-week | Suggest upgrades at register |
    | 🟠 **Low** | Mild (50–60°F), no rain | Mention add-ons, don't push |
    | 🔴 **Avoid** | Rain, snow, or <50°F | Focus on throughput only |
    """)
