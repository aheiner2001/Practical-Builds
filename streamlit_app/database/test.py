# streamlit_app.py

import streamlit as st
from st_supabase_connection import SupabaseConnection
st.write("hellow, me biggy bag")
# Initialize connection.
conn = st.connection("supabase",type=SupabaseConnection)

# Perform query.
rows = conn.table("questions").select("*").execute()

# Print results.
for row in rows.data:
    st.write(row)
