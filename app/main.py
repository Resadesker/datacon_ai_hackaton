import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests


def dye_table(df):                                                                                                  
    def evaluate_column(column):
        eval_score = 0
        # Evaluation formula
        print(column.iloc[3])
        if column.iloc[0] > 25 or column.iloc[0] < -5:
            eval_score += 1
        if column.iloc[1] > 85:
            eval_score += 1
        if column.iloc[2] > 0:
            eval_score += 1
        if column.iloc[3] >= 15:
            eval_score += 1

        # Determine column color based on evaluation score
        if eval_score == 0:
            return "background-color: #4AA61C; color: white;"  # Green
        elif eval_score == 1:
            return "background-color: #F9B50B; color: black;"  # Yellow
        elif eval_score >= 2:
            return "background-color: #A71D31; color: white;"  # Red

    # Apply the evaluation to the entire DataFrame
    styles = pd.DataFrame("", index=df.index, columns=df.columns)  # Default empty styles
    for column in df.columns:
        color = evaluate_column(df[column])  # Evaluate the column
        styles[column] = color  # Apply the color to the entire column

    # Return a styled DataFrame
    return df.style.apply(lambda x: styles, axis=None)

st.set_page_config(page_title="Weather Orb")

st.session_state.selected_worksite = None

url = "http://localhost:8501"
api_url = "http://127.0.0.1:8000"

worksites_request = requests.get(f"{api_url}/worksites")
if worksites_request.status_code != 200:
    st.error("Failed to fetch worksites from the API.")
    st.stop()
worksites = worksites_request.json()

# Get the worksite from the URL parameter
query_params = st.experimental_get_query_params()
selected_worksite_identifier = query_params.get("worksite", [None])[0]

# Store in session state if needed
if selected_worksite_identifier:
    st.session_state.selected_worksite_identifier = selected_worksite_identifier

# Move the selected worksite to the end of the array
if "selected_worksite_identifier" in st.session_state:
    selected_worksite_identifier = st.session_state.selected_worksite_identifier
    worksites = [
        worksite for worksite in worksites if worksite["identifier"] != selected_worksite_identifier
    ] + [
        worksite for worksite in worksites if worksite["identifier"] == selected_worksite_identifier
    ]
def evaluate_button_color(raw_data_array):
    eval_score = 0
    for day_data in raw_data_array:
        eval_score += (
            (1 if day_data['temperature'] > 25 or day_data['temperature'] < -5 else 0)
            + (1 if day_data['humidity'] > 85 else 0)
            + (1 if day_data['precipitation'] > 0 else 0)
            + (1 if day_data['wind'] > 15 else 0)
        )
    if eval_score >= 2:
        return "#A71D31"  # Red
    elif eval_score >= 1:
        return "#F9B50B"  # Yellow
    return "#4AA61C"  # Green

# Sidebar worksite selection with button color logic
with st.sidebar:
    st.write("### Select a Worksite")
    for worksite in worksites:
        identifier = worksite["identifier"]
        raw_data_array = []

        # Fetch raw weather data for the worksite
        for day in range(0, 4):
            url_identifier = identifier.replace(" ", "%20")
            weather_request = requests.get(f"{api_url}/raw_weather/{url_identifier}/{day}")
            if weather_request.status_code != 200:
                st.error(f"Failed to fetch weather data for {identifier}.")
                continue
            raw_data_array.append(weather_request.json())

        # Determine button color based on evaluation
        button_color = evaluate_button_color(raw_data_array)


        # Render button with color
        if st.markdown(
            f"""
            <div style="text-align: center; margin-bottom: 10px;">
                <a href="?worksite={identifier}" target="_self" style="
                    display: block;
                    width: 100%;
                    padding: 10px;
                    text-align: center;
                    background-color: {button_color};
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    font-size: 16px;
                ">{identifier}</a>
            </div>
            """,
            unsafe_allow_html=True,
        ):
            st.session_state.selected_worksite_identifier = identifier
        if selected_worksite_identifier == identifier: break





# Retrieve the selected worksite identifier from session state
selected_worksite_identifier = st.session_state.selected_worksite_identifier

# Ensure a worksite is selected
if not selected_worksite_identifier:
    st.warning("Please select a worksite from the sidebar.")
    st.stop()

selected_worksite_location = None                                                                                   
selected_worksite_description = None                                                                               
for worksite in worksites:
    if worksite["identifier"] == selected_worksite_identifier:
        selected_worksite_location = worksite["location"]
        selected_worksite_description = worksite["description"]
        break

#check for errors
if selected_worksite_location is None or selected_worksite_description is None:
    st.error(f"Details for the selected worksite '{selected_worksite_identifier}' could not be found.")
    st.stop()

# Fetch weather data for the selected worksite
url_identifier = selected_worksite_identifier.replace(" ", "%20")
weather_request = requests.get(f"{api_url}/cache/{url_identifier}")
#region - check
if weather_request.status_code != 200:
    st.error("Failed to fetch weather data for the selected worksite.")
    st.stop()
five_day_weather_analysis = weather_request.json().get("text", "No analysis available.")
# endregion

# Fetch raw weather data
raw_data_array = []
for day in range(0,5):
    raw_data = requests.get(f"{api_url}/raw_weather/{url_identifier}/{day}")
    #region - check
    if raw_data.status_code != 200:
        st.error("Failed to fetch raw weather data")
        st.stop()
    #endregion
    raw_data_array.append(raw_data.json())


weather_table_data = {
    "Today": [raw_data_array[0]['temperature'], raw_data_array[0]['humidity'], raw_data_array[0]['precipitation'], raw_data_array[0]['wind']],
    "Tomorrow": [raw_data_array[1]['temperature'], raw_data_array[1]['humidity'], raw_data_array[1]['precipitation'], raw_data_array[1]['wind']],
    "In 2 Days": [raw_data_array[2]['temperature'], raw_data_array[2]['humidity'], raw_data_array[2]['precipitation'], raw_data_array[2]['wind']],
    "In 3 Days": [raw_data_array[3]['temperature'], raw_data_array[3]['humidity'], raw_data_array[3]['precipitation'], raw_data_array[3]['wind']],
    "In 4 Days": [raw_data_array[4]['temperature'], raw_data_array[4]['humidity'], raw_data_array[4]['precipitation'], raw_data_array[4]['wind']]
}
weather_table_labels = ["Temperature", "Humidity", "Precipitation", "Wind"]
weather_dataframe = pd.DataFrame(weather_table_data, index=weather_table_labels).round(2)
styled_df = dye_table(weather_dataframe)
styled_df = styled_df.format(precision=2, formatter="{:.2f}".format)

# Display the selected worksite title and weather analysis
st.title(selected_worksite_identifier)
st.write(five_day_weather_analysis)

# Display the weather table
st.write("### 5-Day Weather Forecast")
st.markdown(styled_df.to_html(), unsafe_allow_html=True)

st.markdown("***")

# Display selected worksite details
st.write(f"**Location:** Longitude: {selected_worksite_location['longitude']}, Latitude: {selected_worksite_location['latitude']}")
st.write(f"**Description:** {selected_worksite_description}")

# Prepare locations for the map
worksite_locations_for_map = [
    {
        "identifier": worksite["identifier"],
        "latitude": worksite["location"]["latitude"],
        "longitude": worksite["location"]["longitude"],
        "description": worksite["description"],
    }
    for worksite in worksites
]

# Calculate the center of the map
if worksite_locations_for_map:
    average_latitude = sum(location["latitude"] for location in worksite_locations_for_map) / len(worksite_locations_for_map)
    average_longitude = sum(location["longitude"] for location in worksite_locations_for_map) / len(worksite_locations_for_map)
else:
    average_latitude, average_longitude = 0, 0  # Default to (0, 0) if no locations are available

# Create and populate the map
map_center = [average_latitude, average_longitude]
folium_map = folium.Map(location=map_center, zoom_start=5)

for worksite in worksite_locations_for_map:
    folium.Marker(
        location=[worksite["latitude"], worksite["longitude"]],
        popup=f"<b>{worksite['identifier']}</b><br>{worksite['description']}",
        tooltip=worksite["identifier"],
    ).add_to(folium_map)

# Highlight the selected worksite
folium.Marker(
    location=[selected_worksite_location["latitude"], selected_worksite_location["longitude"]],
    popup=f"<b>{selected_worksite_identifier}</b><br>{selected_worksite_description}",
    tooltip="Selected Worksite",
    icon=folium.Icon(color="red", icon="info-sign"),
).add_to(folium_map)

# Display the map
st.write("### Worksite Map")
st_folium(folium_map, width=700, height=500)


