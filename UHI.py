import streamlit as st
import numpy as np
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# 1. Page Configuration
st.set_page_config(page_title="Global UHI Raster Grid Simulator", layout="wide")

st.title("🛰️ Global Urban Heat Island (UHI) Raster Grid Simulator")
st.write("Type any city globally to fetch its coordinates and instantly generate a continuous, semi-transparent square-cell raster grid simulation.")

# Initialize Geocoder
geolocator = Nominatim(user_agent="uhi_raster_grid_2026")

# 2. Control Panel (Sidebar with Numeric Inputs)
st.sidebar.header("🛠️ Simulation Parameters")
st.sidebar.subheader("Location Settings")
city_name = st.sidebar.text_input("Type City Name", value="Dhaka")

# Geocoding Logic
try:
    location = geolocator.geocode(city_name)
    if location:
        detected_lat = location.latitude
        detected_lon = location.longitude
        st.sidebar.success(f"📍 Found: {location.address.split(',')[0]} ({detected_lat:.4f}, {detected_lon:.4f})")
    else:
        st.sidebar.error("City not found. Defaulting to Dhaka coordinates.")
        detected_lat, detected_lon = 23.8103, 90.4125
except GeocoderTimedOut:
    st.sidebar.error("Geocoding service timed out. Using default coordinates.")
    detected_lat, detected_lon = 23.8103, 90.4125

base_temp = st.sidebar.number_input("Baseline Average Temperature (°C)", min_value=0.0, max_value=60.0, value=36.5, step=0.1)

# Mitigation Variables
st.sidebar.subheader("Mitigation Variables (Input Changes)")
ndvi_change = st.sidebar.number_input("Increase in Vegetation Index (Δ NDVI)", min_value=0.00, max_value=1.00, value=0.05, step=0.01, format="%.2f")
albedo_change = st.sidebar.number_input("Increase in Surface Albedo (Δ Albedo)", min_value=0.00, max_value=1.00, value=0.10, step=0.01, format="%.2f")

# 3. Scientific Mathematical Engine
BETA_NDVI = -5.42  
BETA_ALBEDO = -3.55  

temperature_reduction = (ndvi_change * BETA_NDVI) + (albedo_change * BETA_ALBEDO)
current_avg_temp = base_temp + temperature_reduction

# 4. Generate Square Raster Grid Cells
grid_res = 20  # 20x20 Grid creates 400 clean square raster cells
lat_span = 0.06
lon_span = 0.06

# Defining the boundaries explicitly
lat_edges = np.linspace(detected_lat - lat_span/2, detected_lat + lat_span/2, grid_res + 1)
lon_edges = np.linspace(detected_lon - lon_span/2, detected_lon + lon_span/2, grid_res + 1)

np.random.seed(42)
spatial_noise = np.random.normal(0, 1.5, (grid_res, grid_res))

# Setup Color Mapping (Colormap matching standard thermal profiles)
cmap = plt.get_cmap('RdYlBu_r') 
norm = mcolors.Normalize(vmin=15, vmax=45)

# Build a GeoJSON Feature Collection representing true contiguous grid cells
features = []
for i in range(grid_res):
    for j in range(grid_res):
        cell_temp = current_avg_temp + spatial_noise[i, j]
        
        # Get hex color code based on temperature
        rgba_color = cmap(norm(cell_temp))
        hex_color = mcolors.to_hex(rgba_color)
        
        # FIXED: Variable names fully declared and matching here
        lat_min, lat_max = lat_edges[i], lat_edges[i+1]
        lon_min, lon_max = lon_edges[j], lon_edges[j+1]
        
        feature = {
            "type": "Feature",
            "properties": {
                "fillColor": hex_color,
                "temperature": f"{cell_temp:.2f} °C"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [lon_min, lat_min],
                    [lon_max, lat_min],
                    [lon_max, lat_max],
                    [lon_min, lat_max],
                    [lon_min, lat_min]
                ]]
            }
        }
        features.append(feature)

geojson_grid = {"type": "FeatureCollection", "features": features}

# 5. Main Dashboard Layout
col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("Key Metrics")
    st.metric(
        label="Simulated Avg Temperature", 
        value=f"{current_avg_temp:.2f} °C", 
        delta=f"{temperature_reduction:.2f} °C" if temperature_reduction != 0 else None
    )
    st.write("---")
    st.info(
        f"**Scenario Summary for {city_name}:**\n\n"
        f"Increasing vegetation by **{ndvi_change:.2f} NDVI** and enhancing surface albedo by **{albedo_change:.2f}** "
        f"is modeled to reduce the average surface temperature by **{abs(temperature_reduction):.2f}°C**."
    )

with col2:
    # 6. Base Map Setup
    m = folium.Map(location=[detected_lat, detected_lon], zoom_start=12, tiles="OpenStreetMap")
    
    # Add the contiguous GeoJSON Grid onto the map with 50% transparency
    folium.GeoJson(
        geojson_grid,
        style_function=lambda feature: {
            'fillColor': feature['properties']['fillColor'],
            'color': 'gray',         # Grid line borders
            'weight': 0.4,           # Fine thin line borders
            'fillOpacity': 0.5       # Strict 50% continuous grid transparency
        },
        tooltip=folium.GeoJsonTooltip(fields=['temperature'], aliases=['Simulated LST: '])
    ).add_to(m)
    
    # Render interactive continuous square-cell raster grid onto dashboard
    st_folium(m, width=900, height=600, returned_objects=[])