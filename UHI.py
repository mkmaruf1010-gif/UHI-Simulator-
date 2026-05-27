import streamlit as st
import numpy as np
import folium
from folium.raster_layers import ImageOverlay
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# 1. Page Configuration
st.set_page_config(page_title="Global 100x100 UHI Grid Simulator", layout="wide")

st.title("  Global High-Resolution UHI Grid Simulator ")
st.write(" Simulate micro-climate environments globally with an ultra-dense, 10,000-cell continuous square raster framework.")

# Initialize Geocoder
geolocator = Nominatim(user_agent="uhi_highres_raster_2026")

# 2. Control Panel (Sidebar with Numeric Inputs)
st.sidebar.header("  Simulation Parameters")
st.sidebar.subheader("Location Settings")
city_name = st.sidebar.text_input("Type City Name", value="Dhaka")

# Geocoding Logic
try:
    location = geolocator.geocode(city_name)
    if location:
        detected_lat = location.latitude
        detected_lon = location.longitude
        st.sidebar.success(f"  Found: {location.address.split(',')[0]} ({detected_lat:.4f}, {detected_lon:.4f})")
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

# 4. High-Resolution 100x100 Matrix Engine
grid_res = 100  # 100x100 grid (10,000 data points)
lat_span = 0.06
lon_span = 0.06

# Defining spatial matrix boundaries
lat_min, lat_max = float(detected_lat - lat_span/2), float(detected_lat + lat_span/2)
lon_min, lon_max = float(detected_lon - lon_span/2), float(detected_lon + lon_span/2)

np.random.seed(42)
spatial_noise = np.random.normal(0, 1.8, (grid_res, grid_res))
simulated_lst_matrix = np.full((grid_res, grid_res), current_avg_temp) + spatial_noise

# 5. Native Color Mapping Array Conversion
min_display_temp = 15.0
max_display_temp = 45.0

cmap = plt.get_cmap('RdYlBu_r')
norm_matrix = (simulated_lst_matrix - min_display_temp) / (max_display_temp - min_display_temp) 
norm_matrix = np.clip(norm_matrix, 0, 1)               
rgba_raster_image = cmap(norm_matrix)                  

# 6. Generate Reference Color Bar for Sidebar
st.sidebar.write("---")
st.sidebar.subheader("  Color Reference Bar (°C)")

fig, ax = plt.subplots(figsize=(6, 1))
fig.subplots_adjust(bottom=0.5)
norm_legend = mcolors.Normalize(vmin=min_display_temp, vmax=max_display_temp)
cb = fig.colorbar(
    plt.cm.ScalarMappable(norm=norm_legend, cmap=cmap),
    cax=ax, 
    orientation='horizontal',
    label='Land Surface Temperature (LST) in °C'
)
# Style color bar text to fit sidebar cleanly
ax.xaxis.label.set_size(10)
ax.tick_params(labelsize=9)

# Display the generated color bar directly inside the sidebar
st.sidebar.pyplot(fig)
plt.close(fig)  # Clear plot memory allocation

# 7. Main Dashboard Layout
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
    st.caption("ℹ️ *The simulation renders a 100×100 grid overlaying micro-climate thermal zones onto your selected urban region.* ")

with col2:
    # 8. Initialize Folium Map
    m = folium.Map(location=[detected_lat, detected_lon], zoom_start=12, tiles="OpenStreetMap")
    
    # 9. High-Performance Continuous Raster Image Overlay
    ImageOverlay(
        image=rgba_raster_image,
        bounds=[[lat_min, lon_min], [lat_max, lon_max]],
        opacity=0.5,                  # Exact 50% continuous matrix grid transparency
        pixelated=True,               # Forces crisp, clean, independent raster square cells
        name="100x100 Simulated UHI Grid"
    ).add_to(m)
    
    # Render interactive map component on the dashboard
    st_folium(m, width=900, height=600, returned_objects=[])
