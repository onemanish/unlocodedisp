import pandas as  pd
import openpyxl, folium
from haversine import haversine, Unit, haversine_vector
import streamlit as st
from streamlit_folium import st_folium

# This app reads a master list of UN/LO Codes downloaded from the UNECE website
# and shows the location of the nearest UNLOC positions from own position to select suitable 
# position for reporting. (c) Manish Srivastava 04 2024 / open source

@st.cache_data
def get_unlocodes(): # split the coords col to Lat Long and convert to decimal
    df = pd.read_excel('UNLOCODECodeList.xlsx') # read the date file with UNLO Codes
    dfDNV = pd.read_excel('DNVUNLOCODES.xlsx')
    print('read the master data')
    
    def deg2dec(degVal):
        direction = degVal[-1]  # Extract the direction ('N' or 'S')
        degVal = degVal[:-1]  # Remove the direction
        degrees = int(degVal[:-2])  # Extract the degrees part
        minutes = int(degVal[-2:])  # Extract the minutes part
        decDeg = degrees + (minutes / 60)
        if direction == 'S' or direction == 'W':
            decDeg *= -1  # If direction is S or W, make decimal degrees negative
        return decDeg
    
    df['UNLOCode'] = df['Country'] + df['Location']
    df.dropna(subset=['Coordinates'], inplace=True) # throw out rows without Lat/Long info
    df.drop(columns=['Country', 'Date', 'Location','Change','IATA', 'Remarks', 'Subdivision', 'Status', 'NameWoDiacritics'], inplace=True)
    df['InDNV'] = df['UNLOCode'].isin(dfDNV['Port Code']).map({True:'Y', False:' '}) # Check whether the codes exists in DNV db or not
    df['Lat'] = df['Coordinates'].str.split().str[0].apply(deg2dec)
    df['Long'] = df['Coordinates'].str.split().str[1].apply(deg2dec)
    return df

def get_dist(row):
    return haversine((row['Lat'], row['Long']), (vLat, vLong), unit=Unit.NAUTICAL_MILES)
    

if 'vLat' not in st.session_state:
    st.session_state.vLat = 19.0
if 'vLong' not in st.session_state:
    st.session_state.vLong = 72.5

# Update the sidebar inputs to use session state
# print('------ start --------')
# Set page parameters
st.set_page_config(layout='wide', page_title='UN/LOCODES')
st.sidebar.subheader('Click on map to set own location')
vLat = st.sidebar.number_input('My Latitude (use -ve decimal for S)', min_value=-90.0, max_value=90.0, value=st.session_state.vLat)
vLong = st.sidebar.number_input('My Longitude (use -ve decimal for W)', min_value=-180.0, max_value=180.0, value=st.session_state.vLong)
vCircle = st.sidebar.number_input('Draw Circle Around Me (NM)', value=20)
st.sidebar.divider()
diff = st.sidebar.number_input('Show UN/LO Codes around (º)', value=1.0)
mapZoom = st.sidebar.number_input('Map zoom', value=9)
st.sidebar.write('---')
st.subheader('UN/LOCode Viewer')

df1 = get_unlocodes()
sel_df = df1[(df1['Lat'] >= vLat - diff) & (df1['Lat'] <= vLat + diff)] # remove all points diff deg far from my location
sel_df = sel_df[(sel_df['Long'] >= vLong - diff) & (sel_df['Long'] <= vLong + diff)] # remove all points diff º far from my location

sel_df['Distance'] = sel_df.apply(get_dist, axis=1) # Add column for distances 
sel_df = sel_df.sort_values(by='Distance')
sel_df.reset_index(drop=True, inplace=True) # to be able to address each point sequentially
st.error(f'{len(sel_df)} UN/LO Code locations found within {diff}º from my position ({vLat}º, {vLong}º).') # no error, just color change
# st.write(sel_df)
styled_df = sel_df.style.apply(lambda x: ["background-color: pink" if val == "Y" else "" for val in x], axis=1)
styled_df = styled_df.format("{:.2f}", subset=pd.IndexSlice[:, ["Lat", 'Long','Distance']])
st.dataframe(styled_df)

 # set up map and add markers
m = folium.Map(location=[vLat, vLong], tiles="OpenStreetMap", zoom_start=mapZoom)
folium.Marker(location=[vLat, vLong], tooltip=folium.Tooltip('I am here!'), icon=folium.Icon(color='orange')).add_to(m)
folium.Circle(location=[vLat, vLong], radius=vCircle*1852, color="black", weight=1, \
    opacity=1, fill_opacity=0.2, fill_color="green", fill=False, tooltip=f"{vCircle}NM").add_to(m)

for i in range(0,len(sel_df)):
    Distance = haversine((vLat,vLong), (sel_df.iloc[i]['Lat'], sel_df.iloc[i]['Long']), unit=Unit.NAUTICAL_MILES)
    folium.Marker(location=[sel_df.iloc[i]['Lat'], sel_df.iloc[i]['Long']],
      tooltip=f"{sel_df.iloc[i]['Name']} - {sel_df.iloc[i]['UNLOCode']} - {sel_df.iloc[i]['Distance']:0.1f}NM away",
      icon=folium.Icon(color='red' if sel_df.iloc[i]['InDNV'] == 'Y' else 'darkgreen'),
   ).add_to(m)

st_data = st_folium(m, use_container_width=True)
selData = st_data['last_object_clicked_tooltip']
# Update coordinates when map is clicked
if st_data['last_clicked']:
    st.session_state.vLat = st_data['last_clicked']['lat']
    st.session_state.vLong = st_data['last_clicked']['lng']
    st.experimental_rerun()

# st.warning(selData)
if selData != None:
    selData = "  --  ".join(st_data['last_object_clicked_tooltip'].split('-'))
    st.sidebar.error(f"{selData}")
