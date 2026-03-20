import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Housing Price Predictor", page_icon="🏠", layout="centered")
st.title("🏠 Housing Price Predictor")
st.write("Enter house details below to get a predicted sale price.")

# ---------------------------------------------------
# POI Coordinates (same as your model)
# ---------------------------------------------------
SEATTLE_LAT, SEATTLE_LON = 47.6062, -122.3321
GOLF_COURSES = [(47.53632,-122.14365),(47.61010,-122.17854),(47.61088,-122.15558),(47.63970,-122.28900),(47.52360,-122.25620),(47.75370,-122.24440),(47.68240,-122.26090),(47.56900,-122.29530),(47.57640,-122.38630),(47.70580,-122.12320)]
PARKS = [(47.59424,-122.18437),(47.61060,-122.17878),(47.61542,-122.20113),(47.59058,-122.20698),(47.65730,-122.40580),(47.55150,-122.25510),(47.64560,-122.33440),(47.71170,-122.37250),(47.66410,-122.12150),(47.52860,-122.13980),(47.65640,-122.17380),(47.57990,-122.40950),(47.53030,-122.39520)]
LAKES = [(47.62605,-122.21970),(47.59320,-122.08960),(47.60144,-122.14050),(47.63960,-122.33430),(47.68050,-122.32850),(47.60360,-122.33050)]
EMPLOYERS = [(47.64258,-122.13602),(47.61500,-122.19200),(47.61540,-122.19450),(47.61510,-122.19390),(47.60620,-122.33210),(47.62450,-122.33650),(47.62770,-122.33810),(47.61010,-122.20150),(47.64980,-122.35090),(47.62050,-122.34930),(47.64300,-122.13100)]

good_zips = {'98004','98005','98006','98007','98008','98040','98052','98033','98034','98053','98027','98029','98110','98122','98188','98103','98199','98109','98119','98115'}

# ---------------------------------------------------
# Helper functions
# ---------------------------------------------------
def haversine(lat1, lon1, lat2, lon2):
    R = 3958.8
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    return R * 2 * np.arcsin(np.sqrt(a))

def min_distance(df, points):
    distances = [haversine(df['lat'], df['long'], lat, lon) for lat, lon in points]
    return np.min(distances, axis=0)

def engineer_features(df):
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%dT%H%M%S')
    df['sale_year']  = df['date'].dt.year
    df['sale_month'] = df['date'].dt.month
    df['house_age']  = df['sale_year'] - df['yr_built']
    df['years_since_renovation'] = np.where(df['yr_renovated'] == 0, df['house_age'], df['sale_year'] - df['yr_renovated'])
    df['is_renovated']            = (df['yr_renovated'] != 0).astype(int)
    df['sqft_living_log']         = np.log1p(df['sqft_living'])
    df['sqft_lot_log']            = np.log1p(df['sqft_lot'])
    df['sqft_lot15_log']          = np.log1p(df['sqft_lot15'])
    df['living_to_lot_ratio']     = df['sqft_living'] / (df['sqft_lot'] + 1)
    df['basement_ratio']          = df['sqft_basement'] / (df['sqft_living'] + 1)
    df['living15_to_living_ratio']= df['sqft_living15'] / (df['sqft_living'] + 1)
    df['is_apartment'] = (((df['sqft_lot'] < 2000) & (df['sqft_living'] < 1500)) | (df['sqft_living'] / (df['sqft_lot'] + 1) > 0.6) | (df['sqft_living'] < 800)).astype(int)
    df['has_basement']   = (df['sqft_basement'] > 0).astype(int)
    df['bath_per_bed']   = df['bathrooms'] / (df['bedrooms'] + 1)
    df['grade_per_sqft'] = df['grade'] / (df['sqft_living'] + 1)
    df['has_good_school']= df['zipcode'].astype(str).isin(good_zips).astype(int)
    df['dist_to_seattle']  = haversine(df['lat'], df['long'], SEATTLE_LAT, SEATTLE_LON)
    df['dist_to_golf']     = min_distance(df, GOLF_COURSES)
    df['dist_to_park']     = min_distance(df, PARKS)
    df['dist_to_lake']     = min_distance(df, LAKES)
    df['dist_to_employer'] = min_distance(df, EMPLOYERS)
    df = df.drop('date', axis=1)
    return df

feature_cols = [
    'bedrooms','bathrooms','sqft_living','sqft_lot','floors','waterfront','view',
    'condition','grade','sqft_above','sqft_basement','yr_built','yr_renovated',
    'zipcode','lat','long','sqft_living15','sqft_lot15','sale_year','sale_month',
    'house_age','years_since_renovation','is_renovated','sqft_living_log',
    'sqft_lot_log','sqft_lot15_log','living_to_lot_ratio','basement_ratio',
    'living15_to_living_ratio','is_apartment','has_basement','bath_per_bed',
    'grade_per_sqft','has_good_school','dist_to_seattle','dist_to_golf',
    'dist_to_park','dist_to_lake','dist_to_employer'
]

# ---------------------------------------------------
# Train model once (cached so it doesn't retrain on every click)
# ---------------------------------------------------
@st.cache_resource
def train_model():
    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context
    housing = pd.read_csv('https://raw.githubusercontent.com/byui-cse/cse450-course/master/data/housing.csv')
    housing_eng = engineer_features(housing)
    X = housing_eng[feature_cols]
    y = housing_eng['price']
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=7)
    model = GradientBoostingRegressor(
        n_estimators=1000, learning_rate=0.05, max_depth=6,
        min_samples_split=6, min_samples_leaf=3, subsample=0.8,
        max_features=0.8, random_state=42, verbose=0
    )
    model.fit(X_train, y_train)
    return model

with st.spinner("Training model on housing data... (only happens once)"):
    model = train_model()

st.success("Model ready!")
st.divider()

# ---------------------------------------------------
# User Inputs
# ---------------------------------------------------
st.subheader("Property Details")

col1, col2 = st.columns(2)
with col1:
    bedrooms    = st.number_input("Bedrooms", 1, 15, 3)
    bathrooms   = st.number_input("Bathrooms", 0.5, 10.0, 2.0, step=0.25)
    floors      = st.selectbox("Floors", [1.0, 1.5, 2.0, 2.5, 3.0])
    sqft_living = st.number_input("Sqft Living", 300, 15000, 1800)
    sqft_lot    = st.number_input("Sqft Lot", 500, 150000, 5000)
    sqft_above  = st.number_input("Sqft Above Ground", 300, 10000, 1800)
    sqft_basement = st.number_input("Sqft Basement", 0, 5000, 0)

with col2:
    sqft_living15 = st.number_input("Sqft Living (neighbors avg)", 300, 10000, 1800)
    sqft_lot15    = st.number_input("Sqft Lot (neighbors avg)", 500, 150000, 5000)
    yr_built      = st.number_input("Year Built", 1900, 2015, 1990)
    yr_renovated  = st.number_input("Year Renovated (0 if never)", 0, 2015, 0)
    zipcode       = st.number_input("Zipcode", 98000, 98200, 98052)
    lat           = st.number_input("Latitude", 47.0, 48.0, 47.56, format="%.5f")
    long          = st.number_input("Longitude", -122.6, -121.0, -122.20, format="%.5f")

st.subheader("Condition & Features")
col3, col4 = st.columns(2)
with col3:
    grade      = st.slider("Grade (1-13)", 1, 13, 7)
    condition  = st.slider("Condition (1-5)", 1, 5, 3)
    view       = st.slider("View Quality (0-4)", 0, 4, 0)
with col4:
    waterfront = st.selectbox("Waterfront?", [0, 1], format_func=lambda x: "Yes" if x else "No")
    sale_month = st.selectbox("Month of Sale", list(range(1, 13)), index=4,
                               format_func=lambda x: ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][x-1])
    sale_year  = st.selectbox("Year of Sale", [2014, 2015], index=1)

# ---------------------------------------------------
# Build input row and predict
# ---------------------------------------------------
if st.button("Predict Price", type="primary"):
    input_dict = {
        'id': 0,
        'date': f'{sale_year}0101T000000',
        'bedrooms': bedrooms,
        'bathrooms': bathrooms,
        'sqft_living': sqft_living,
        'sqft_lot': sqft_lot,
        'floors': floors,
        'waterfront': waterfront,
        'view': view,
        'condition': condition,
        'grade': grade,
        'sqft_above': sqft_above,
        'sqft_basement': sqft_basement,
        'yr_built': yr_built,
        'yr_renovated': yr_renovated,
        'zipcode': zipcode,
        'lat': lat,
        'long': long,
        'sqft_living15': sqft_living15,
        'sqft_lot15': sqft_lot15,
    }

    row = pd.DataFrame([input_dict])
    row_eng = engineer_features(row)
    X_input = row_eng[feature_cols]

    prediction = model.predict(X_input)[0]

    st.divider()
    st.subheader("Prediction")

    col5, col6, col7 = st.columns(3)
    col5.metric("Estimated Price", f"${prediction:,.0f}")
    col6.metric("Price per Sqft", f"${prediction / sqft_living:,.0f}")
    col7.metric("Good School Zone", "Yes ✅" if str(zipcode) in good_zips else "No ❌")

    if prediction > 800000:
        st.success("This is a high-value property!")
    elif prediction > 400000:
        st.info("This is a mid-range property.")
    else:
        st.warning("This is an entry-level property.")
