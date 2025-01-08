import streamlit as st

# Config
st.set_page_config(
    page_title="Weather Forecast App",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Set the title of the app
st.title("Weather Forecast App")

# Get the menu selection from url
menu = st.sidebar.radio(
    "Menu",
    ["Forecast", "Map - Plotly", "Map - Plot"],
)

if menu == "Forecast":
    from pages.forecast import render
    render()
elif menu == "Map - Plotly":
    from pages.map import render
    render()
elif menu == "Map - Plot":
    from pages.map_old import render
    render()