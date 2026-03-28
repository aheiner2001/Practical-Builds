import streamlit as st
import pandas as pd

# We need to define 'data' so the editor and download button have something to use
data = pd.DataFrame({
    "Column A": [1, 2, 3],
    "Column B": ["Apple", "Banana", "Cherry"]
})

st.title("Streamlit Widget Gallery")

st.button('Hit me')
st.data_editor('Edit data', data)
st.checkbox('Check me out')
st.radio('Pick one:', ['nose','ear'])
st.selectbox('Select', [1,2,3])
st.multiselect('Multiselect', [1,2,3])
st.slider('Slide me', min_value=0, max_value=10)
st.select_slider('Slide to select', options=[1,'2'])
st.text_input('Enter some text')
st.number_input('Enter a number')
st.text_area('Area for textual entry')
st.date_input('Date input')
st.time_input('Time entry')
st.file_uploader('File uploader')

# Converting the dataframe to CSV for the download button
csv = data.to_csv(index=False).encode('utf-8')
st.download_button('On the dl', data=csv, file_name="data.csv")

st.camera_input("一二三,茄子!")
st.color_picker('Pick a color')
