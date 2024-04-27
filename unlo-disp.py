import pandas as  pd
import openpyxl
import folium
from haversine import haversine, Unit
import streamlit as st
from streamlit_folium import st_folium

@st.cache_data
def get_unlocodes(): # split the coords col to lat long and convert to decimal
    df = pd.read_excel('2023-2UNLOCODECodeList.xlsx') # read the date file with UNLO Codes
    print('read the data')
    
    def dddmmX_decimal(degVal):
        direction = degVal[-1]  # Extract the direction ('N' or 'S')
        degVal = degVal[:-1]  # Remove the direction
        degrees = int(degVal[:-2])  # Extract the degrees part
        minutes = int(degVal[-2:])  # Extract the minutes part
        decimal_degrees = degrees + (minutes / 60)
        if direction == 'S' or direction == 'W':
            decimal_degrees *= -1  # If direction is S or W, make decimal degrees negative
        return decimal_degrees

    df.dropna(subset=['Coordinates'], inplace=True) # throw out rows without lat/long info
    df['lat'] = df['Coordinates'].str.split().str[0].apply(dddmmX_decimal)
    df['long'] = df['Coordinates'].str.split().str[1].apply(dddmmX_decimal)
    return df

st.set_page_config(layout='wide', page_title='UN/LOCODES')
st.sidebar.title('UN/LOCODE locator')
vLat = st.sidebar.number_input('Latitude (use -ve value for S)', min_value=-90, max_value=90, value=8)
vLong = st.sidebar.number_input('Longitude (use -ve value for W)', min_value=-180, max_value=180, value=77)
diff = st.sidebar.number_input('Show UN/LO Codes around (º)', value=2)
vCircle = st.sidebar.number_input('Draw Circle Around Me (NM)', value=20)
mapZoom = st.sidebar.number_input('Map zoom', value=9)
st.subheader('UN/LOCode Viewer  -- click on marker to select')

df1 = get_unlocodes()
sel_df = df1[(df1['lat'] >= vLat - diff) & (df1['lat'] <= vLat + diff)] # remove all points diffº far from my location
sel_df = sel_df[(sel_df['long'] >= vLong - diff) & (sel_df['long'] <= vLong + diff)] # remove all points diffº far from my location
sel_df.reset_index(drop=True, inplace=True) # to be able to address each point sequentially

 # set up map and add markers
m = folium.Map(location=[vLat, vLong], tiles="OpenStreetMap", zoom_start=mapZoom)

folium.Marker(location=[vLat, vLong], tooltip=folium.Tooltip('I am here!'), icon=folium.Icon(color='orange')).add_to(m)
folium.Circle(location=[vLat, vLong], radius=vCircle*1852, color="black", weight=1, \
    opacity=1, fill_opacity=0.2, fill_color="green", fill=False, tooltip=f"{vCircle}NM").add_to(m)

print('-----done-----')

for i in range(0,len(sel_df)):
    dist = haversine((vLat,vLong), (sel_df.iloc[i]['lat'], sel_df.iloc[i]['long']), unit=Unit.NAUTICAL_MILES)
    folium.Marker(location=[sel_df.iloc[i]['lat'], sel_df.iloc[i]['long']],
      tooltip=f"{sel_df.iloc[i]['Name']}-{sel_df.iloc[i]['Country']}{sel_df.iloc[i]['Location']}-{dist:.1f}NM away",
   ).add_to(m)

st_data = st_folium(m, use_container_width=True)
selData = st_data['last_object_clicked_tooltip']
# st.warning(selData)
if selData != None:
    selData = "  --  ".join(st_data['last_object_clicked_tooltip'].split('-'))
    st.sidebar.error(f"{selData}")
