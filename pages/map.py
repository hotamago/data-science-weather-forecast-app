import streamlit as st
import xarray as xr
import numpy as np
import imageio
import io
import time

import plotly.graph_objects as go

@st.cache_resource
def load_data():
    # Load the weather data
    data = xr.open_dataset('./dataset/data_stream-oper_stepType-instant.nc')
    return data

import plotly.graph_objects as go

def load_basemap(fig,
                        llcrnrlon=90,
                        llcrnrlat=-10,
                        urcrnrlon=140,
                        urcrnrlat=30,
                        resolution=50,   # numeric, approximate equivalent to Basemap resolution
                        projection="mercator"):
    """
    Replicate the bounding box, coastlines, countries, and lat/lon grid lines from Basemap
    using a Plotly Geo layout.

    :param fig: A Plotly figure object to be updated.
    :param llcrnrlon: Lower-left corner longitude.
    :param llcrnrlat: Lower-left corner latitude.
    :param urcrnrlon: Upper-right corner longitude.
    :param urcrnrlat: Upper-right corner latitude.
    :param resolution: Resolution in Plotly. 50 is a reasonable value for moderate detail.
    :param projection: Map projection, e.g. "mercator", "equirectangular", etc.
    :return: Updated figure with geo layout that roughly emulates Basemap's bounding box.
    """
    fig.update_geos(
        # Set the projection type
        projection=dict(type=projection),
        
        # Rough approximate to Basemap resolution 'i' or 'h'
        resolution=resolution,

        # Show coastlines/countries
        showcoastlines=True,
        coastlinecolor="black",
        coastlinewidth=1,
        showcountries=True,
        countrycolor="black",
        
        # Fill land/ocean, if desired
        showland=True,
        landcolor="whitesmoke",
        showocean=True,
        oceancolor="lightblue",

        # Limit the lat/lon range as your bounding box
        lataxis=dict(
            range=[llcrnrlat, urcrnrlat],
            showgrid=True,   # parallels => "grid lines"
            dtick=5,         # spacing for parallels
            gridwidth=0.5,
            gridcolor="gray"
        ),
        lonaxis=dict(
            range=[llcrnrlon, urcrnrlon],
            showgrid=True,   # meridians => "grid lines"
            dtick=10,        # spacing for meridians
            gridwidth=0.5,
            gridcolor="gray"
        ),
    )

    # Remove extra padding around the map
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0)
    )

    return fig

def create_plotly_figure(variable, lat, lon, data, time_index=0):
    """
    Create a single Plotly figure given a variable (Temperature or Wind),
    lat, lon arrays, and a time index.
    """
    if variable == "Temperature":
        # Temperature array: subtract 273.15 to convert from K to °C
        t2m = data.t2m[time_index, :, :].values - 273.15
        fig = go.Figure(
            data=go.Contour(
                z=t2m,
                x=lon.values,
                y=lat.values,
                colorscale='Jet',
                contours=dict(showlabels=False),
                colorbar=dict(title="°C")
            )
        )
        fig = load_basemap(fig,
                   llcrnrlon=90, llcrnrlat=-10,
                   urcrnrlon=140, urcrnrlat=30,
                   projection="mercator")
        fig.update_layout(
            title=f"Temperature (°C) at time index {time_index}",
            xaxis_title="Longitude",
            yaxis_title="Latitude"
        )
    else:  # "Wind"
        # Compute wind speed magnitude
        wind_u = data.u10[time_index, :, :].values
        wind_v = data.v10[time_index, :, :].values
        WS = np.sqrt(wind_u**2 + wind_v**2)
        fig = go.Figure(
            data=go.Contour(
                z=WS,
                x=lon.values,
                y=lat.values,
                colorscale='Jet',
                contours=dict(showlabels=False),
                colorbar=dict(title="m/s")
            )
        )
        fig = load_basemap(fig,
                   llcrnrlon=90, llcrnrlat=-10,
                   urcrnrlon=140, urcrnrlat=30,
                   projection="mercator")
        fig.update_layout(
            title=f"Wind Speed (m/s) at time index {time_index}",
            xaxis_title="Longitude",
            yaxis_title="Latitude"
        )

    # Restrict the axes range to approximate your previous Basemap region
    fig.update_xaxes(range=[90, 140])
    fig.update_yaxes(range=[-10, 30])

    # Enforce 1:1 aspect ratio and make the figure square
    fig.update_layout(
        width=600,
        height=600,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    fig.update_yaxes(
        scaleanchor="x",  # Tie the y-axis scale to the x-axis
        scaleratio=1      # Keep a 1:1 ratio
    )

    return fig

def render():
    st.title("Weather Data Heatmap (Plotly)")

    # import plotly.graph_objects as go

    # fig = go.Figure(go.Scattergeo())
    # fig = load_basemap(fig,
    #                llcrnrlon=90, llcrnrlat=-10,
    #                urcrnrlon=140, urcrnrlat=30,
    #                projection="mercator")
    
    # st.plotly_chart(fig)

    # Top-level layout and instructions
    st.write("Use the sliders and buttons below to explore the data interactively.")

    with st.spinner("Loading data..."):
        data = load_data()

    if "stop_animation" not in st.session_state:
        st.session_state.stop_animation = False

    # Create a UI layout with columns for better organization
    col1, col2 = st.columns(2)

    with col1:
        time_index = st.slider("Time index", 0, data.valid_time.size - 1, 0)
        variable = st.selectbox("Select variable", ("Temperature", "Wind"))

    with col2:
        fps = st.slider("Animation FPS", 1, 10, 2, help="Frames per second for both real-time animation and GIF.")

    st.write("### Controls")
    animate = st.button("Animate")
    stop = st.button("Stop Animation")

    if stop:
        st.session_state.stop_animation = True

    lat = data.latitude
    lon = data.longitude

    # Show static or interactive animation in the Streamlit loop
    if animate:
        st.session_state.stop_animation = False
        placeholder = st.empty()

        for i in range(data.valid_time.size):
            if st.session_state.stop_animation:
                break
            fig = create_plotly_figure(variable, lat, lon, data, i)
            placeholder.plotly_chart(fig, use_container_width=True)

            # Sleep for 1/fps seconds to simulate frame rate
            time.sleep(1.0 / fps)

    else:
        # If not animating, show static plot for the selected time_index
        fig = create_plotly_figure(variable, lat, lon, data, time_index)
        st.plotly_chart(fig, use_container_width=True)