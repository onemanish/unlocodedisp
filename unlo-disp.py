import pandas as  pd
import openpyxl
import folium
from haversine import haversine, Unit
import streamlit as st
from streamlit_folium import st_folium

@st.cache_data
def get_unlocodes():
    df = pd.read_excel('2023-2UNLOCODECodeList.xlsx')
    print('read the data')
    df.dropna(subset=['Coordinates'], inplace=True)
    df['slat'] = df['Coordinates'].str.split().str[0]
    df['slong'] = df['Coordinates'].str.split().str[1]
    df['lat'] = df['slat'].str.extract('(\d+)').astype(int)/100
    df.loc[df['slat'].str.endswith('S'), 'lat'] *= -1
    df['long'] = df['slong'].str.extract('(\d+)').astype(int)/100
    df.loc[df['slong'].str.endswith('W'), 'long'] *= -1
    return df

st.set_page_config(layout='wide', page_title='UN/LOCODES')
st.sidebar.title('UN/LOCODE locator')
# vName = st.sidebar.text_input('Enter Vessel Name', value='I am here!')
vLat = st.sidebar.number_input('Latitude (use -ve value for S)', min_value=-90, max_value=90)
vLong = st.sidebar.number_input('Longitude (use -ve value for W)', min_value=-180, max_value=180)
diff = st.sidebar.number_input('Show UN/LO Codes around (º)', value=2)
vCircle = st.sidebar.number_input('Draw Circle Around Me (NM)', value=20)
mapZoom = st.sidebar.number_input('Map zoom', value=9)
st.subheader('UN/LOCode Viewer  -- click on marker to select')

df1 = get_unlocodes()
filtered_df = df1[(df1['lat'] >= vLat - diff) & (df1['lat'] <= vLat + diff)] # remove all points diffº far from my location
filtered_df = filtered_df[(filtered_df['long'] >= vLong - diff) & (filtered_df['long'] <= vLong + diff)] # remove all points diffº far from my location
filtered_df.reset_index(drop=True, inplace=True) # to be able to address each point separately

m = folium.Map(location=[vLat, vLong], tiles="OpenStreetMap", zoom_start=mapZoom) # set up map
folium.Marker(
      location=[vLat, vLong],
      tooltip=folium.Tooltip('I am here!'),
      icon=folium.Icon(color='orange')
   ).add_to(m)

folium.Circle(
    location=[vLat, vLong], radius=vCircle*1852,
    color="black", weight=1,
    opacity=1, fill_opacity=0.2,
    fill_color="green", fill=False,  
    tooltip=f"{vCircle}NM",
).add_to(m)

print('-----done-----')

for i in range(0,len(filtered_df)):
    dist = haversine((vLat,vLong), (filtered_df.iloc[i]['lat'], filtered_df.iloc[i]['long']), unit=Unit.NAUTICAL_MILES)
    folium.Marker(
      location=[filtered_df.iloc[i]['lat'], filtered_df.iloc[i]['long']],
      tooltip=f"{filtered_df.iloc[i]['Name']}-{filtered_df.iloc[i]['Country']}{filtered_df.iloc[i]['Location']}-{dist:.1f}NM away",
   ).add_to(m)

st_data = st_folium(m, use_container_width=True)
selData = st_data['last_object_clicked_tooltip']
# st.warning(selData)
if selData != None:
    selData = "  --  ".join(st_data['last_object_clicked_tooltip'].split('-'))
    st.sidebar.error(f"{selData}")
