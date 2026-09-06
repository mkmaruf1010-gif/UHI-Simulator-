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
    credentials = ee.ServiceAccountCredentials(
        st.secrets["gee"]["fieldmapping@fieldmapping-507507.iam.gserviceaccount.com"], 
        key_data=st.secrets["gee"]["MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC+5su/HJ7aY4Kl
JfxvzESry9SjsbYFp5q7JNgMbQaNQ9QxbQo68zq/63lkS9TVBE4Mzew4yp7OZSxf
1sJZM+5VF+j1rqQbKA2s6rDQ0RzYtDdnfZDHx9qz5CZPGVbvQHNGj4YsZ48EtVRm
Dn5z7PqDp+iefjg4W9veE2Qf8f9x2eCw+kYiYaIuXdAY+2oKPORobDtEnVlr5ZcP
yzYVrEbxoVbcBKN8HmqjLCerYrQc57bMyVEfLbS7c9QXUBfor/oGSijRmrl1uZ6/
hCqB5eXnZJLtDUMOs8EGn9xdVOUlz0q2pS4nIiPJpV8HH75NSSqZjGE/qmwq8OCH
qHmzoIVvAgMBAAECggEAHhZP/GHtY2wVliPDgndGR3FLpTUIBCIjT+WBq4uvYapU
EiomV54oH0Fkk3skIyKXjosR9O1yVAM8GCrH3LlDkeO/0qDgumr4pM0kavTaQAk/
Ri9TFzmXbYzCwOq0eebFhFRwiCUWNF7D24XjRjAOV5uqHPi1saRApeKWgDZq1S2E
2gyXpLYOv4RjvUumtx2ZU2Ki63Il+jJZzYMhmhy9ePICvI2OVohU5Mji/k+/YNkZ
AGweEjq8k4SpLu47zUBurrb2HLXLoAiT0gDHC0mNb9N4i4koej2rr3/c3qkZSzhf
XRbpj/yBBZSNzqjhofKxWTqxM3WP21fQZK4FudwWuQKBgQDrlc3fXxh7O0fgZiN3
vIDl6mEGtjZcYzSYM1Oo2LzU92zXAqOhy9Npr541eI7fueQCKpPPZ8Q6DeK1RWli
2pLDSgsmmn1Rpv6J5qvcBrwHQhgS5hpzuv6DHCLzfs9OO3Neowm7ErndTMFD6F0E
vxRvQa6FamdhWRLQmSiTrhEQzQKBgQDPcbwo3kJAKoAoHbrTCAHs3vPTbGVqn3Kp
jlj9TtJCX7xNUv1ZuKdQ1EgiJtzokkqq57oRNerVtJmN9tHlE1zWZN1P5fjwZk7s
1JEyy4zKtaJYP2pFcMB4mgYImvW3U2eIG+DhOZUin1olM8LKvEXAYF3insqOelYg
FDYhKSF/KwKBgBYW4Mvd/cyoPVAUI6U5fpiQRnK7qRM2lhrjTSfa0rHhVUo/zBoC
o5sYRWxcFoFxy6hMV7mt0B9lZ+l5Ta1gMzyud6cx+ygp0Voaz+h8lSrVDq7O9pH9
aZnfjINqU4PRXTr1bJcm5ViTttdoNTiZtg/Mh9GorXLaSEJY6g4W1zDNAoGBAIeZ
+T1dzEDVh2CxzmYUXe3Q7+HMgZ7pC7L6cgFjfN4WZqjFDwePRQ/5NA3fCZidyGFf
iKmnbRK1M4sxRJNRzOX4mRKZadj7h6wYZ7GkjSwU/0Jgcb9irO4pALivUt+7jXnT
f3S6h1pSgELBSxvrZk0SsUxqME5iedoOXDPhBxxxAoGBAKwDfacgj/nblvXspTyD
nnOVneITTLkfJgOTgLT0b/xECi7BJW+0egvJjtcJWRniJn2RRswmwy/OzSERmvs6
S3vCfn7Lt59In/X7fx3KK+3vS/sonOwE7VF9qPnom0ico/wSKsuPh5w4ghS6toae
+9IQEJIF6qqsvKJNqQxGSdvK"]
    )
    ee.Initialize(credentials)

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
