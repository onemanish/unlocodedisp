import pandas as  pd
import openpyxl
import folium
from haversine import haversine, Unit, haversine_vector
import streamlit as st
from streamlit_folium import st_folium

@st.cache_data
def get_unlocodes(): # split the coords col to lat long and convert to decimal
    df = pd.read_excel('2023-2UNLOCODECodeList.xlsx') # read the date file with UNLO Codes
    print('read the data')
    
    def deg2dec(degVal):
        direction = degVal[-1]  # Extract the direction ('N' or 'S')
        degVal = degVal[:-1]  # Remove the direction
        degrees = int(degVal[:-2])  # Extract the degrees part
        minutes = int(degVal[-2:])  # Extract the minutes part
        decDeg = degrees + (minutes / 60)
        if direction == 'S' or direction == 'W':
            decDeg *= -1  # If direction is S or W, make decimal degrees negative
        return decDeg
    
    df['unloc'] = df['Country'] + df['Location']
    df.dropna(subset=['Coordinates'], inplace=True) # throw out rows without lat/long info
    df.drop(columns=['Country', 'Location','Change','IATA', 'Remarks', 'Subdivision', 'Status', 'NameWoDiacritics'], inplace=True)
    df['lat'] = df['Coordinates'].str.split().str[0].apply(deg2dec)
    df['long'] = df['Coordinates'].str.split().str[1].apply(deg2dec)
    return df

# Set page parameters
st.set_page_config(layout='wide', page_title='UN/LOCODES')
st.sidebar.title('UN/LOCODE locator')
vLat = st.sidebar.number_input('Latitude (use -ve value for S)', min_value=-90.0, max_value=90.0, value=19.0)
vLong = st.sidebar.number_input('Longitude (use -ve value for W)', min_value=-180.0, max_value=180.0, value=72.5)
diff = st.sidebar.number_input('Show UN/LO Codes around (º)', value=1.0)
vCircle = st.sidebar.number_input('Draw Circle Around Me (NM)', value=20)
mapZoom = st.sidebar.number_input('Map zoom', value=9)
st.subheader('UN/LOCode Viewer')

df1 = get_unlocodes()
sel_df = df1[(df1['lat'] >= vLat - diff) & (df1['lat'] <= vLat + diff)] # remove all points diff deg far from my location
sel_df = sel_df[(sel_df['long'] >= vLong - diff) & (sel_df['long'] <= vLong + diff)] # remove all points diff º far from my location

def get_dist(row):
    return haversine((row['lat'], row['long']), (vLat, vLong), unit=Unit.NAUTICAL_MILES)

sel_df['dist'] = sel_df.apply(get_dist, axis=1)
sel_df = sel_df.sort_values(by='dist')
sel_df.reset_index(drop=True, inplace=True) # to be able to address each point sequentially
st.error(f'Nearest UN/LO Code locations [{len(sel_df)}] within {diff}º from own position.')
st.dataframe(sel_df)

 # set up map and add markers
m = folium.Map(location=[vLat, vLong], tiles="OpenStreetMap", zoom_start=mapZoom)
folium.Marker(location=[vLat, vLong], tooltip=folium.Tooltip('I am here!'), icon=folium.Icon(color='orange')).add_to(m)
folium.Circle(location=[vLat, vLong], radius=vCircle*1852, color="black", weight=1, \
    opacity=1, fill_opacity=0.2, fill_color="green", fill=False, tooltip=f"{vCircle}NM").add_to(m)

for i in range(0,len(sel_df)):
    dist = haversine((vLat,vLong), (sel_df.iloc[i]['lat'], sel_df.iloc[i]['long']), unit=Unit.NAUTICAL_MILES)
    folium.Marker(location=[sel_df.iloc[i]['lat'], sel_df.iloc[i]['long']],
      tooltip=f"{sel_df.iloc[i]['Name']} - {sel_df.iloc[i]['unloc']} - {sel_df.iloc[i]['dist']:0.1f}NM away",
   ).add_to(m)

st_data = st_folium(m, use_container_width=True)
selData = st_data['last_object_clicked_tooltip']
# st.warning(selData)
if selData != None:
    selData = "  --  ".join(st_data['last_object_clicked_tooltip'].split('-'))
    st.sidebar.error(f"{selData}")
