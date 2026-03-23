import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Bank Campaign Predictor", page_icon="🏦", layout="centered")
st.title("🏦 Bank Marketing Campaign Predictor")
st.write("Enter customer details below to predict whether they are likely to subscribe to a term deposit.")

# ---------------------------------------------------
# Feature engineering — same transformations as notebook
# ---------------------------------------------------
def engineer_features(df):
    df = df.copy()

    # Euribor bin
    df["euribor_bin"] = pd.cut(
        df["euribor3m"],
        bins=[0, 1, 3, 5],
        labels=["0-1%", "1,3", "3-5%"],
        right=False
    )

    # Age bin
    df["age_bin"] = pd.cut(
        df["age"],
        bins=[18, 25, 35, 45, 55, 65, float("inf")],
        labels=["18–24", "25–34", "35–44", "45–54", "55–64", "65+"],
        right=False
    )

    # Job group
    job_map = {
        "admin.": "white_collar", "management": "white_collar", "technician": "white_collar",
        "services": "service", "housemaid": "service",
        "blue-collar": "manual",
        "entrepreneur": "self_employed", "self-employed": "self_employed",
        "student": "limited_income", "retired": "limited_income", "unemployed": "limited_income",
        "unknown": "unknown"
    }
    df["job_group"] = df["job"].map(job_map)

    # Season
    season_map = {
        "jan": "winter", "feb": "winter", "dec": "winter",
        "mar": "spring", "apr": "spring", "may": "spring",
        "jun": "summer", "jul": "summer", "aug": "summer",
        "sep": "fall",   "oct": "fall",   "nov": "fall",
    }
    df["season"] = df["month"].map(season_map)

    # Education group
    education_map = {
        "primary": "low", "secondary": "medium",
        "tertiary": "high", "unknown": "unknown"
    }
    df["education_group"] = df["education"].map(education_map)

    # Day group
    weekday_map = {
        "mon": "weekday", "tue": "weekday", "wed": "weekday",
        "thu": "weekday", "fri": "weekday",
        "sat": "weekend", "sun": "weekend"
    }
    df["day_group"] = df["day_of_week"].map(weekday_map)

    return df

FEATURES = [
    'job_group', 'marital', 'education_group', 'age_bin',
    'housing', 'loan', 'season', 'day_group',
    'previous', 'contact', 'euribor_bin'
]

DATA_URL = "https://raw.githubusercontent.com/byui-cse/cse450-course/master/data/bank.csv"

# ---------------------------------------------------
# Train model once (cached)
# ---------------------------------------------------
@st.cache_resource
def train_model():
    campaign = pd.read_csv(DATA_URL)
    campaign = engineer_features(campaign)

    X = pd.get_dummies(campaign[FEATURES], drop_first=True)
    y = campaign['y']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=46
    )

    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=12,
        min_samples_leaf=10,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    clf.fit(X_train, y_train)

    precision = precision_score(y_test, clf.predict(X_test), pos_label='yes')
    recall    = recall_score(y_test, clf.predict(X_test), pos_label='yes')

    return clf, X_train.columns.tolist(), precision, recall

with st.spinner("Training model on campaign data... (only happens once)"):
    clf, train_cols, precision, recall = train_model()

col_p, col_r = st.columns(2)
col_p.success(f"Model ready! · Precision: {precision:.2%}")
col_r.success(f"Recall: {recall:.2%}")

st.divider()

# ---------------------------------------------------
# User Inputs
# ---------------------------------------------------
st.subheader("Customer Details")

col1, col2 = st.columns(2)

with col1:
    age = st.number_input("Age", 18, 100, 35)

    job = st.selectbox("Job", [
        "admin.", "blue-collar", "entrepreneur", "housemaid",
        "management", "retired", "self-employed", "services",
        "student", "technician", "unemployed", "unknown"
    ])

    marital = st.selectbox("Marital Status", ["married", "single", "divorced"])

    education = st.selectbox("Education Level", [
        "primary", "secondary", "tertiary", "unknown"
    ])

    housing = st.selectbox("Has Housing Loan?", ["yes", "no"],
                           format_func=lambda x: "Yes" if x == "yes" else "No")

    loan = st.selectbox("Has Personal Loan?", ["yes", "no"],
                        format_func=lambda x: "Yes" if x == "yes" else "No")

with col2:
    contact = st.selectbox("Contact Method", ["cellular", "telephone"])

    month = st.selectbox("Month of Contact", [
        "jan","feb","mar","apr","may","jun",
        "jul","aug","sep","oct","nov","dec"
    ], index=4)

    day_of_week = st.selectbox("Day of Week", ["mon","tue","wed","thu","fri","sat","sun"])

    previous = st.number_input("# Previous Campaign Contacts", 0, 50, 0)

    euribor3m = st.number_input("Euribor 3-Month Rate (%)", 0.0, 5.0, 1.5, step=0.1)

# ---------------------------------------------------
# Build input row and predict
# ---------------------------------------------------
if st.button("Predict Subscription", type="primary"):

    input_dict = {
        'age':         age,
        'job':         job,
        'marital':     marital,
        'education':   education,
        'housing':     housing,
        'loan':        loan,
        'contact':     contact,
        'month':       month,
        'day_of_week': day_of_week,
        'previous':    previous,
        'euribor3m':   euribor3m,
    }

    row     = pd.DataFrame([input_dict])
    row_eng = engineer_features(row)

    X_input = pd.get_dummies(row_eng[FEATURES], drop_first=True)
    X_input = X_input.reindex(columns=train_cols, fill_value=0)

    prob       = clf.predict_proba(X_input)[0, 1]
    prediction = "yes" if prob >= 0.5 else "no"

    st.divider()
    st.subheader("Prediction")

    col3, col4, col5 = st.columns(3)
    col3.metric("Likely to Subscribe?", "Yes ✅" if prediction == "yes" else "No ❌")
    col4.metric("Confidence", f"{prob:.1%}")
    col5.metric("Risk Tier",
                "High 🔥" if prob >= 0.65 else
                "Medium 🟡" if prob >= 0.35 else
                "Low ❄️")

    if prediction == "yes":
        st.success("This customer is a strong candidate — prioritize them in the campaign!")
    elif prob >= 0.35:
        st.info("This customer is on the fence — worth including in the campaign.")
    else:
        st.warning("This customer is unlikely to subscribe — lower priority for outreach.")

st.divider()

# ---------------------------------------------------
# Segment Explorer — top segments from the training data
# ---------------------------------------------------
st.subheader("📊 Segment Insights")
st.caption("Based on the full training dataset — shows which customer groups respond best.")

@st.cache_data
def load_segment_data():
    campaign = pd.read_csv(DATA_URL)
    campaign = engineer_features(campaign)
    X = pd.get_dummies(campaign[FEATURES], drop_first=True)
    probs = clf.predict_proba(X)[:, 1]
    campaign['yes_probability'] = probs
    return campaign

seg_df = load_segment_data()

tab1, tab2, tab3, tab4 = st.tabs(["By Age", "By Job", "By Season", "By Education"])

with tab1:
    age_seg = seg_df.groupby('age_bin', observed=True)['yes_probability'].mean().reset_index()
    age_seg.columns = ['Age Group', 'Avg Subscription Probability']
    age_seg['Avg Subscription Probability'] = age_seg['Avg Subscription Probability'].round(3)
    st.bar_chart(age_seg.set_index('Age Group'))

with tab2:
    job_seg = seg_df.groupby('job_group')['yes_probability'].mean().sort_values(ascending=False).reset_index()
    job_seg.columns = ['Job Group', 'Avg Subscription Probability']
    job_seg['Avg Subscription Probability'] = job_seg['Avg Subscription Probability'].round(3)
    st.bar_chart(job_seg.set_index('Job Group'))

with tab3:
    sea_seg = seg_df.groupby('season')['yes_probability'].mean().sort_values(ascending=False).reset_index()
    sea_seg.columns = ['Season', 'Avg Subscription Probability']
    sea_seg['Avg Subscription Probability'] = sea_seg['Avg Subscription Probability'].round(3)
    st.bar_chart(sea_seg.set_index('Season'))

with tab4:
    edu_seg = seg_df.groupby('education_group')['yes_probability'].mean().sort_values(ascending=False).reset_index()
    edu_seg.columns = ['Education Level', 'Avg Subscription Probability']
    edu_seg['Avg Subscription Probability'] = edu_seg['Avg Subscription Probability'].round(3)
    st.bar_chart(edu_seg.set_index('Education Level'))
