import streamlit as st
import ee
import folium
from streamlit_folium import st_folium
import pandas as pd

# Page setup
st.set_page_config(page_title="Live UHI & Albedo Simulator", layout="wide")

# Initialize Google Earth Engine securely
@st.cache_resource
def initialize_gee():
    try:
        credentials = ee.ServiceAccountCredentials(
            st.secrets["gee"]["client_email"], 
            key_data=st.secrets["gee"]["private_key"]
        )
        ee.Initialize(credentials)
    except Exception:
        ee.Authenticate()
        ee.Initialize()

initialize_gee()

st.title("Dynamic Urban Heat Island & Albedo Monitor")
st.markdown("Monitor live surface temperature and surface albedo via Google Earth Engine and Landsat 8/9.")

# Sidebar controls
st.sidebar.header("Parameters")
sensor = st.sidebar.selectbox("Select Sensor", ["Landsat 8/9 (30m)", "MODIS Daily (1km)"])
start_date = st.sidebar.date_input("Start Date", value=pd.to_datetime("2025-08-25"))
end_date = st.sidebar.date_input("End Date", value=pd.to_datetime("2025-09-30"))
cloud_max = st.sidebar.slider("Max Cloud Cover (%)", 0, 50, 50)

# --- USER SELECTABLE POLYGON / AREA OF INTEREST ---
st.sidebar.subheader("Area of Interest (AOI)")
area_option = st.sidebar.selectbox(
    "Select Study Region", 
    ["Dhaka Core", "Uttara / North Dhaka", "Motijheel / South Dhaka", "Custom Bounding Box"]
)

if area_option == "Dhaka Core":
    aoi = ee.Geometry.Polygon([[[90.35, 23.70], [90.48, 23.70], [90.48, 23.85], [90.35, 23.85]]])
    center_lat, center_lon = 23.775, 4125
elif area_option == "Uttara / North Dhaka":
    aoi = ee.Geometry.Polygon([[[90.38, 23.83], [90.44, 23.83], [90.44, 23.90], [90.38, 23.90]]])
    center_lat, center_lon = 23.86, 90.41
elif area_option == "Motijheel / South Dhaka":
    aoi = ee.Geometry.Polygon([[[90.40, 23.71], [90.46, 23.71], [90.46, 23.77], [90.40, 23.77]]])
    center_lat, center_lon = 23.74, 90.43
else:
    st.sidebar.markdown("Enter Custom Coordinates:")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        min_lon = st.number_input("Min Longitude", value=88)
        min_lat = st.number_input("Min Latitude", value=20.5)
    with col2:
        max_lon = st.number_input("Max Longitude", value=93)
        max_lat = st.number_input("Max Latitude", value=26.7)
    
    aoi = ee.Geometry.Polygon([[[min_lon, min_lat], [max_lon, min_lat], [max_lon, max_lat], [min_lon, max_lat]]])
    center_lat, center_lon = (min_lat + max_lat) / 2, (min_lon + max_lon) / 2

# Use Session State to preserve the map across reruns
if "run_analysis" not in st.session_state:
    st.session_state.run_analysis = False

if st.button("Run Live GEE Analysis"):
    st.session_state.run_analysis = True

if st.session_state.run_analysis:
    with st.spinner("Processing satellite bands on Google servers..."):
        try:
            m = folium.Map(location=[23.8103, 90.4125], zoom_start=11, tiles="CartoDB positron")
            
            if "Landsat" in sensor:
                collection = (
                    ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
                    .merge(ee.ImageCollection("LANDSAT/LC09/C02/T1_L2"))
                    .filterBounds(aoi)
                    .filterDate(str(start_date), str(end_date))
                    .filter(ee.Filter.lt('CLOUD_COVER', cloud_max))
                )
                
                if collection.size().getInfo() == 0:
                    st.warning("No Landsat images found for this date range and cloud filter. Try increasing the cloud cover limit.")
                else:
                    img = collection.mosaic().clip(aoi)
                    optical = img.select(['SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B6', 'SR_B7']).multiply(0.0000275).add(-0.2)
                    thermal = img.select(['ST_B10']).multiply(0.00341802).add(149.0)
                    
                    albedo = (
                        optical.select('SR_B2').multiply(0.356)
                        .add(optical.select('SR_B4').multiply(0.130))
                        .add(optical.select('SR_B5').multiply(0.373))
                        .add(optical.select('SR_B6').multiply(0.085))
                        .add(optical.select('SR_B7').multiply(0.072))
                        .subtract(0.0018)
                        .rename('Albedo')
                    )
                    
                    lst_c = thermal.subtract(273.15).rename('LST_Celsius')
                    
                    lst_id = lst_c.getMapId({'min': 25, 'max': 45, 'palette': ['blue', 'cyan', 'green', 'yellow', 'red']})
                    folium.raster_layers.TileLayer(
                        tiles=lst_id['tile_fetcher'].url_format,
                        attr='Google Earth Engine',
                        name='Land Surface Temperature (°C)',
                        overlay=True,
                        control=True
                    ).add_to(m)
                    
                    st.success("Analysis complete using Landsat 8/9!")
                
            else:
                modis = ee.ImageCollection("MODIS/061/MOD11A1").filterDate(str(start_date), str(end_date)).select('LST_Day_1km')
                if modis.size().getInfo() == 0:
                    st.warning("No MODIS images found for this date range.")
                else:
                    modis_img = modis.mosaic().clip(aoi)
                    modis_c = modis_img.multiply(0.02).subtract(273.15).rename('MODIS_LST')
                    
                    modis_id = modis_c.getMapId({'min': 25, 'max': 45, 'palette': ['blue', 'yellow', 'red']})
                    folium.raster_layers.TileLayer(
                        tiles=modis_id['tile_fetcher'].url_format,
                        attr='Google Earth Engine',
                        name='MODIS LST (°C)',
                        overlay=True,
                        control=True
                    ).add_to(m)
                    
                    st.success("Analysis complete using MODIS daily data!")
                    
            folium.LayerControl().add_to(m)
            st_folium(m, width="100%", height=500, returned_objects=[])
            
        except Exception as e:
            st.error(f"An error occurred during GEE processing: {e}")
