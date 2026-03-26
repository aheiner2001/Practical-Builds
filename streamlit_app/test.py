import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Simple Data Explorer")

# File upload
uploaded_file = st.file_uploader("Upload your CSV file", type="csv")

if uploaded_file:
    # Load and display data
    df = pd.read_csv(uploaded_file)
    st.dataframe(df)

    # Interactive plotting
    column = st.selectbox("Select column to plot", df.columns)
    fig = px.histogram(df, x=column)
    st.plotly_chart(fig)
