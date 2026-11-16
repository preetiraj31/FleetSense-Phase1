import streamlit as st
st.set_page_config(page_title="MetroCab Operations", layout="wide")
st.title(" MetroCab Operations - Airport Desk")
st.write("Waiting for DuckDB warehouse connection")
tab1, tab2, tab3 = st.tabs(["Airport Zones", "City Zones", "Holiday Week Accuracy"])
with tab1:
    st.header("Airport Hourly Pickups")
    st.info("Airport charts.")
with tab2:
    st.header("City Hourly Pickups")
    st.info("City demand charts will appear here.")
    
with tab3:
    st.header("Holiday Week Performance")
    st.info("Accuracy reporting for holiday weeks.")