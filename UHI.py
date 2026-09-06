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
        ee.Initialize()
    except Exception:
        ee.Authenticate()
        ee.Initialize()

initialize_gee()

st.title("Dynamic Urban Heat Island & Albedo Monitor")
st.markdown("Monitor live surface temperature and surface albedo via Google Earth Engine and Landsat 8/9.")

# Sidebar controls
st.sidebar.header("Parameters")
sensor = st.sidebar.selectbox("Select Sensor", ["Landsat 8/9 (30m)", "MODIS Daily (1km)"])
start_date = st.sidebar.date_input("Start Date", value=pd.to_datetime("2026-01-01"))
end_date = st.sidebar.date_input("End Date", value=pd.to_datetime("2026-09-01"))
cloud_max = st.sidebar.slider("Max Cloud Cover (%)", 0, 50, 15)

# Define AOI for Dhaka
aoi = ee.Geometry.Polygon([[[90.30, 23.70], [90.55, 23.70], [90.55, 23.90], [90.30, 23.90]]])

if st.button("Run Live GEE Analysis"):
    with st.spinner("Processing satellite bands on Google servers..."):
        
        # Base Folium Map centered on Dhaka
        m = folium.Map(location=[23.8103, 90.4125], zoom_start=11, tiles="CartoDB positron")
        
        if "Landsat" in sensor:
            collection = (
                ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
                .merge(ee.ImageCollection("LANDSAT/LC09/C02/T1_L2"))
                .filterBounds(aoi)
                .filterDate(str(start_date), str(end_date))
                .filter(ee.Filter.lt('CLOUD_COVER', cloud_max))
            )
            
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
            
            # Add Earth Engine map tiles to Folium via EE tile server URL
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
            modis = ee.ImageCollection("MODIS/061/MOD11A1").filterDate(str(start_date), str(end_date)).select('LST_Day_1km').mosaic().clip(aoi)
            modis_c = modis.multiply(0.02).subtract(273.15).rename('MODIS_LST')
            
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
        st_folium(m, width="100%", height=500)
