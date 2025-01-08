import datetime
import streamlit as st
import requests
import numpy as np
import hashlib
import os
import json
from modules.cache import cache_manager
import asyncio
import aiohttp

# global_url = "http://localhost:8080"

def get_weather_forecast(latitude, longitude):
    # Open Meteo API endpoint
    url = f"https://api.open-meteo.com/v1/forecast"  # Use local server for testing
    
    # Parameters for the API
    params = {
        "latitude": latitude,  # Fixed typo here
        "longitude": longitude,
        "hourly": "temperature_2m,windspeed_10m,winddirection_10m",  # Added winddirection_10m
        "daily": "temperature_2m_max,temperature_2m_min,windspeed_10m_max",
        "timezone": "auto"
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        # st.error("Error fetching data from Open Meteo API")
        print("Error fetching data from Open Meteo API")
        return None
    
def get_location():
    st.sidebar.subheader("Location")
    # Default location is Hanoi Vietnam
    latitude = st.sidebar.number_input("Latitude", value=21.0285)
    longitude = st.sidebar.number_input("Longitude", value=105.8542)
    return {"latitude": latitude, "longitude": longitude}

def generate_grid_points(center_lat, center_lon, radius_km, num_points):
    radius_deg = radius_km / 111  # Approximate conversion from km to degrees
    latitudes = np.linspace(center_lat - radius_deg, center_lat + radius_deg, num_points)
    longitudes = np.linspace(center_lon - radius_deg, center_lon + radius_deg, num_points)
    grid_points = [(lat, lon) for lat in latitudes for lon in longitudes]
    return grid_points

def fetch_weather_data_for_grid(grid_points):
    weather_data = {}
    progress_bar = st.progress(0)
    total_points = len(grid_points)
    completed_tasks = 0  # Initialize a counter for completed tasks

    async def fetch(session, lat, lon):
        nonlocal completed_tasks
        lat = round(lat, 1)
        lon = round(lon, 1)
        cached_data = cache_manager.load(lat, lon)
        if cached_data:
            weather_data[(lat, lon)] = cached_data
        else:
            data = await get_weather_forecast_async(session, lat, lon)
            if data:
                weather_data[(lat, lon)] = data
                cache_manager.save(data, lat, lon)
        completed_tasks += 1
        progress_bar.progress(completed_tasks / total_points)

    async def get_weather_forecast_async(session, latitude, longitude):
        url = "https://archive-api.open-meteo.com/v1/era5"
        # Get start_date from the current date - 2 days
        start_date = (datetime.datetime.now() - datetime.timedelta(days=2)).strftime("%Y-%m-%d")
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": start_date,
            "hourly": "temperature_2m,windspeed_10m,winddirection_10m",
            "daily": "rain_sum",
            "timezone": "auto"
        }
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    # Ensure 'temperature_2m' data is present
                    if 'hourly' in data and 'temperature_2m' in data['hourly']:
                        return data
                    else:
                        st.error(f"Temperature data missing for ({latitude}, {longitude})")
                        return None
                else:
                    st.error("Error fetching data from Open Meteo API")
                    return None
        except Exception as e:
            # st.error(f"Exception occurred: {e}")
            print(f"Exception occurred: {e}")
            return None

    async def main():
        async with aiohttp.ClientSession() as session:
            tasks = [fetch(session, lat, lon) for lat, lon in grid_points]
            await asyncio.gather(*tasks)
        progress_bar.progress(1.0)  # Ensure the progress bar reaches 100%

    asyncio.run(main())

    return weather_data

@st.cache_data
def fetch_weather_data_for_grid_cached(grid_points):
    return fetch_weather_data_for_grid(grid_points)

def save_user_config(latitude, longitude, radius_km, num_points):
    config = {
        "latitude": latitude,
        "longitude": longitude,
        "radius_km": radius_km,
        "num_points": num_points
    }
    cache_manager.save(config, "user_config")

def load_user_config():
    config = cache_manager.load("user_config")
    if config:
        return config
    return None

def get_location_and_grid():
    config = load_user_config()
    if config:
        latitude = config["latitude"]
        longitude = config["longitude"]
        radius_km = config["radius_km"]
        num_points = config["num_points"]
    else:
        location = get_location()
        latitude = location["latitude"]
        longitude = location["longitude"]
        radius_km = st.sidebar.number_input("Radius (km)", value=1.0)
        num_points = st.sidebar.number_input("Number of Points", value=5)
    grid_points = generate_grid_points(latitude, longitude, radius_km, num_points)
    save_user_config(latitude, longitude, radius_km, num_points)
    return grid_points