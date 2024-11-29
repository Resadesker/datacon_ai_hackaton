# weather_api.py

import requests

class WeatherFetcher:
    def __init__(self, api_key, latitude, longitude):
        self.api_key = api_key
        self.lat = latitude
        self.lon = longitude
        self.base_url = 'https://api.openweathermap.org/data/2.5/forecast'  # Should be the 5-Day Forecast API endpoint

    def get_weather_data(self):
        params = {
            'lat': self.lat,
            'lon': self.lon,
            'units': 'metric',
            'lang': 'de',  # Language parameter for German descriptions
            'appid': self.api_key
        }
        response = requests.get(self.base_url, params=params)

        # Check for HTTP errors
        if response.status_code != 200:
            print(f"Status Code: {response.status_code}")
            print(f"Response URL: {response.url}")
            print(f"Response Text: {response.text}")
            try:
                data = response.json()
                message = data.get('message', 'Unknown error')
            except ValueError:
                message = 'Non-JSON response received'
            raise Exception(f"Error fetching data: {message}")

        try:
            data = response.json()
        except ValueError:
            raise Exception("Error parsing JSON response")

        return data
