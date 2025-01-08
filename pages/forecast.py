import streamlit as st
import pandas as pd
import plotly.express as px

# Import the helper functions from the modules folder
from modules.helper import get_weather_forecast, get_location
from modules.cache import cache_manager

def render():
    # Get the location from the user
    location = get_location()

    # Attempt to load weather data from cache
    weather_data = cache_manager.load(location["latitude"], location["longitude"])
    
    if not weather_data:
        # Get the weather forecast data
        weather_data = get_weather_forecast(location["latitude"], location["longitude"])
        # Save the fetched data to cache
        cache_manager.save(weather_data, location["latitude"], location["longitude"])
    
    # Button to clear cache
    if st.button("Clear Cache"):
        cache_manager.clear_cache(location["latitude"], location["longitude"])
        st.success("Cache cleared.")

    # Check if the weather data is available
    if weather_data:
        # Extract the hourly data
        hourly_data = weather_data["hourly"]

        # Convert the hourly data to a DataFrame
        hourly_df = pd.DataFrame(hourly_data)

        # Display the hourly data
        st.subheader("Hourly Weather Forecast")
        st.write(hourly_df)

        # Plot the hourly temperature data
        fig = px.line(hourly_df, x="time", y="temperature_2m", title="Hourly Temperature Forecast")
        st.plotly_chart(fig)

        # Plot the hourly wind speed data
        fig = px.line(hourly_df, x="time", y="windspeed_10m", title="Hourly Wind Speed Forecast")
        st.plotly_chart(fig)

        # Plot the hourly wind direction data
        fig = px.line(hourly_df, x="time", y="winddirection_10m", title="Hourly Wind Direction Forecast")
        st.plotly_chart(fig)

        # Extract the daily data
        daily_data = weather_data["daily"]

        # Convert the daily data to a DataFrame
        daily_df = pd.DataFrame(daily_data)

        # Display the daily data
        st.subheader("Daily Weather Forecast")
        st.write(daily_df)

        # Plot the daily temperature data
        fig = px.bar(daily_df, x="time", y=["temperature_2m_max", "temperature_2m_min"], barmode="group", title="Daily Temperature Forecast")
        st.plotly_chart(fig)

        # Plot the daily wind speed data
        fig = px.bar(daily_df, x="time", y="windspeed_10m_max", title="Daily Wind Speed Forecast")
        st.plotly_chart(fig)