import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from mpl_toolkits.basemap import Basemap
import imageio
import io

@st.cache_resource
def load_data():
    # Load the weather data
    data = xr.open_dataset('./dataset/data_stream-oper_stepType-instant.nc')
    return data

# @st.cache_data()
def load_basemap(llcrnrlon=90, llcrnrlat=-10, urcrnrlon=140, urcrnrlat=30, resolution='i'):
    m = Basemap(projection='cyl',
                llcrnrlon=llcrnrlon,
                llcrnrlat=llcrnrlat,
                urcrnrlon=urcrnrlon,
                urcrnrlat=urcrnrlat,
                resolution=resolution)
    m.drawcoastlines(1)
    m.drawcountries()
    parallels = np.arange(-15, 15 + 0.25, 5)
    m.drawparallels(parallels, labels=[1, 0, 0, 0], linewidth=0.5)
    meridians = np.arange(90, 150 + 0.25, 10)
    m.drawmeridians(meridians, labels=[0, 0, 0, 1], linewidth=0.5)
    return m

def create_gif(variable, lat, lon, data, frames_per_second=2):
    """
    Create a GIF from time-stepped data.
    Returns the path to the generated GIF file.
    """

    frames = []
    num_times = data.valid_time.size

    for time_index in range(num_times):
        fig = plt.figure(figsize=(15, 8))
        m = load_basemap()  # reload basemap for each frame

        if variable == "Temperature":
            t2m = data.t2m[time_index, :, :]
            plt.contourf(lon, lat, t2m - 273.15, cmap='jet', extend='both')
        elif variable == "Wind":
            wind_u = data.u10
            wind_v = data.v10
            WS = np.sqrt(wind_u**2 + wind_v**2)
            plt.contourf(lon, lat, WS[time_index, :, :], cmap='jet')
            Q = plt.quiver(
                lon[::6],
                lat[::6],
                wind_u[time_index, ::6, ::6],
                wind_v[time_index, ::6, ::6],
                scale_units='xy',
                scale=3,
                width=0.0015
            )

        # Convert current figure to a PNG in memory
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        frames.append(imageio.v3.imread(buf.getvalue()))

        plt.close(fig)

    # Save frames to an animated GIF
    gif_filename = "weather_animation.gif"
    imageio.mimsave(gif_filename, frames, fps=frames_per_second)
    return gif_filename

def render():
    st.title("Weather Data Heatmap")

    with st.spinner("Loading data..."):
        data = load_data()

    if "stop_animation" not in st.session_state:
        st.session_state.stop_animation = False

    time_index = st.slider("Time index", 0, data.valid_time.size - 1, 0)
    variable = st.selectbox("Select variable", ("Temperature", "Wind"))
    animate = st.button("Animate")
    stop = st.button("Stop Animation")
    gif_create = st.button("Create GIF")

    if stop:
        st.session_state.stop_animation = True

    lat = data.latitude
    lon = data.longitude

    # Show static or interactive animation in the Streamlit loop
    if animate:
        st.session_state.stop_animation = False
        # Your existing animate_plot code
        placeholder = st.empty()
        for i in range(data.valid_time.size):
            if st.session_state.stop_animation:
                break
            fig = plt.figure(figsize=(15, 8))
            m = load_basemap()

            if variable == "Temperature":
                t2m = data.t2m[i, :, :]
                cf = plt.contourf(lon, lat, t2m - 273.15, cmap='jet', extend='both')
                cb = plt.colorbar(cf, fraction=0.0235, pad=0.03)
                cb.set_label(' \u00b0K', fontsize=15, rotation=0)
            elif variable == "Wind":
                wind_u = data.u10
                wind_v = data.v10
                WS = np.sqrt(wind_u**2 + wind_v**2)
                cf = plt.contourf(lon, lat, WS[i, :, :], cmap='jet')
                Q = plt.quiver(lon[::6], lat[::6],
                               wind_u[i, ::6, ::6],
                               wind_v[i, ::6, ::6],
                               scale_units='xy', scale=3, width=0.0015)
                qk = plt.quiverkey(Q, 1, 1.04, 5, str(5) + ' m/s',
                                   labelpos='E', coordinates='axes')
                cb = plt.colorbar(cf, fraction=0.0235, pad=0.03)
                cb.set_label('m/s', fontsize=15)

            placeholder.pyplot(fig)
            plt.close(fig)

    elif gif_create:
        # Use the create_gif function to generate the GIF
        with st.spinner("Generating GIF..."):
            gif_path = create_gif(variable, lat, lon, data, frames_per_second=2)
        st.success(f"GIF created: {gif_path}")
        # Display the GIF in the Streamlit app
        with open(gif_path, "rb") as f:
            st.image(f.read())

    else:
        # If not animating, show static plot for selected time_index
        if variable == "Temperature":
            t2m = data.t2m[time_index, :, :]
            fig = plt.figure(figsize=(15, 8))
            m = load_basemap()
            cf = plt.contourf(lon, lat, t2m - 273.15, cmap='jet', extend='both')
            cb = plt.colorbar(cf, fraction=0.0235, pad=0.03)
            cb.set_label(' \u00b0K', fontsize=15, rotation=0)
            st.pyplot(fig)
        elif variable == "Wind":
            wind_u = data.u10
            wind_v = data.v10
            WS = np.sqrt(wind_u**2 + wind_v**2)
            fig_wind = plt.figure(figsize=(15, 8))
            m = load_basemap()
            cf = plt.contourf(lon, lat, WS[time_index, :, :], cmap='jet')
            Q = plt.quiver(lon[::6], lat[::6],
                           wind_u[time_index, ::6, ::6],
                           wind_v[time_index, ::6, ::6],
                           scale_units='xy', scale=3, width=0.0015)
            qk = plt.quiverkey(Q, 1, 1.04, 5,
                               str(5) + ' m/s',
                               labelpos='E', coordinates='axes')
            cb = plt.colorbar(cf, fraction=0.0235, pad=0.03)
            cb.set_label('m/s', fontsize=15)
            st.pyplot(fig_wind)