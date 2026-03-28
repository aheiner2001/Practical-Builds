# streamlit_app.py

import streamlit as st
from st_supabase_connection import SupabaseConnection

# Initialize connection.
conn = st.connection("supabase",type=SupabaseConnection)

# Perform query.
rows = conn.query("*", table="test", ttl="10m").execute()

# Print results.
for row in rows.data:
    st.write(f"{row['']} has a :{row['']}:")
