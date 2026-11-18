import streamlit as st
import duckdb
import pandas as pd

st.set_page_config(page_title="MetroCab Operations", layout="wide")
st.title(" MetroCab Operations - Airport Desk")

DB_PATH = 'data/warehouse/fleetsense.duckdb'

# Read the SQL file
with open('queries.sql', 'r') as file:
    sql_file_content = file.read()

# Split the file by the ';' character to get the two separate queries
queries = sql_file_content.split(';')
airport_query = queries[0]
city_query = queries[1]

@st.cache_data
def load_data(query):
    with duckdb.connect(DB_PATH) as conn:
        return conn.execute(query).df()

airport_df = load_data(airport_query)
city_df = load_data(city_query)

airport_df.set_index('hour_of_day', inplace=True)
city_df.set_index('hour_of_day', inplace=True)

# Build the tabs
tab1, tab2 = st.tabs(["✈️ Airport Zones", "🏙️ City Zones"])

with tab1:
    st.header("Airport Hourly Pickups (Sept 2025)")
    st.bar_chart(airport_df)

with tab2:
    st.header("City Hourly Pickups (Sept 2025)")
    st.bar_chart(city_df)