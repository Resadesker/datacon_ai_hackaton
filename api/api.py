# api.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import json
import os
from weather_api import WeatherFetcher
from rag_retrieval import WeatherLangChain
from typing import List
from threading import Lock

app = FastAPI()

# Load construction sites from worksites.json
worksites_file = 'worksites.json'
worksites_lock = Lock()

weather_api_key = "ENTER API KEY"
openai_api_key = "ENTER API KEY"

try:
    with open("cache.json", 'r') as f:
        cache_data = json.load(f)
except FileNotFoundError:
    cache_data = []

try:
    with open(worksites_file, 'r') as f:
        construction_sites = json.load(f)
except FileNotFoundError:
    construction_sites = []

# Define Pydantic models
class Location(BaseModel):
    latitude: float
    longitude: float

class Worksite(BaseModel):
    identifier: str
    location: Location
    description: str

class WeatherAnalysisResponse(BaseModel):
    identifier: str
    description: str
    analysis: str

class RawWeatherData(BaseModel):
    temperature: float
    humidity: int
    precipitation: int
    wind: int

@app.get("/worksites", response_model=List[Worksite])
async def get_worksites():
    return construction_sites

@app.get("/weather/{identifier}", response_model=WeatherAnalysisResponse)
async def get_weather_for_site(identifier: str):
    # Find the construction site by identifier
    site = next((site for site in construction_sites if site["identifier"] == identifier), None)
    if not site:
        raise HTTPException(status_code=404, detail="Construction site not found")

    # Extract location data
    latitude = site["location"]["latitude"]
    longitude = site["location"]["longitude"]
    
    # Initialize WeatherFetcher and WeatherLangChain
    weather_fetcher = WeatherFetcher(weather_api_key, latitude, longitude)
    weather_langchain = WeatherLangChain(weather_fetcher, openai_api_key)

    try:
        # Get the weather analysis
        analysis = weather_langchain.get_weather_analysis()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

    return WeatherAnalysisResponse(
        identifier=site["identifier"],
        description=site["description"],
        analysis=analysis
    )

@app.post("/create", response_model=Worksite)
async def create_worksite(worksite: Worksite):
    # Check if the identifier is unique
    if any(site["identifier"] == worksite.identifier for site in construction_sites):
        raise HTTPException(status_code=400, detail="Worksite identifier must be unique")

    # Add the new worksite
    new_worksite = worksite.dict()

    with worksites_lock:
        construction_sites.append(new_worksite)
        
        # Write to the JSON file
        try:
            with open(worksites_file, 'w') as f:
                json.dump(construction_sites, f, indent=4)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred while saving the worksite: {e}")

    return new_worksite


@app.get("/raw_weather/{identifier}/{dayIndex}", response_model=RawWeatherData)
async def get_raw_weather_data(identifier: str, dayIndex: str):
    # Find the construction site by identifier
    site = next((site for site in construction_sites if site["identifier"] == identifier), None)
    if not site:
        raise HTTPException(status_code=404, detail="Construction site not found")
    
    # Extract location data
    latitude = site["location"]["latitude"]
    longitude = site["location"]["longitude"]
    
    if not weather_api_key:
        raise HTTPException(status_code=500, detail="API key is not set")

    # Initialize WeatherFetcher
    weather_fetcher = WeatherFetcher(weather_api_key, latitude, longitude)

    try:
        # Get the raw weather data
        data = weather_fetcher.get_weather_data()

        # Extract relevant fields from the raw weather data
        current_weather = data['list'][int(dayIndex)]  # Assuming the first item in the list is the current weather

        temperature = current_weather['main']['temp']
        humidity = current_weather['main']['humidity']
        wind_speed = current_weather['wind']['speed']
        precipitation = current_weather.get('rain', {}).get('3h', 0)  # 3-hour precipitation in mm, default to 0 if not available

        # Convert wind speed to km/h (if given in m/s)
        wind_speed_kmh = wind_speed * 3.6

    except KeyError as e:
        raise HTTPException(status_code=500, detail=f"Missing expected field in weather data: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while fetching raw weather data: {e}")

    try:
        return RawWeatherData(
            temperature=temperature,
            humidity=humidity,
            precipitation=precipitation,
            wind=int(wind_speed_kmh)  # Ensure wind is returned as an integer
        )
    except Exception:
        return RawWeatherData(
            temperature=0,
            humidity=0,
            precipitation=0,
            wind=int(0)  # Ensure wind is returned as an integer
        )

@app.get("/cache/{identifier}")
async def get_text_from_cache(identifier: str):
    # Find the entry in the cache by identifier
    entry = next((item for item in cache_data if item["identifier"] == identifier), None)
    if not entry:
        raise HTTPException(status_code=404, detail="Identifier not found in cache")

    return {"identifier": identifier, "text": entry["text"]}

@app.post("/regenerate")
async def regenerate_cache():
    new_cache = []

    for site in construction_sites:
        identifier = site["identifier"]
        description = site["description"]
        latitude = site["location"]["latitude"]
        longitude = site["location"]["longitude"]
        print("Got data from worksites")

        # Initialize WeatherFetcher and WeatherLangChain
        weather_fetcher = WeatherFetcher(weather_api_key, latitude, longitude)
        weather_langchain = WeatherLangChain(weather_fetcher, openai_api_key)

        try:
            # Generate new text using WeatherLangChain
            new_text = weather_langchain.get_weather_analysis()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to regenerate text for {identifier}: {e}")

        # Create the updated cache entry
        new_entry = {
            "identifier": identifier,
            "days": {
                "0": "Das ist eine Nachricht.",
                "1": "test"
            },
            "text": new_text
        }
        new_cache.append(new_entry)

        print("Saving to JSON")
        # Save the new cache to cache.json
        try:
            with open("cache.json", 'w') as f:
                json.dump(new_cache, f, indent=4)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred while saving cache: {e}")

        # Update the in-memory cache
        cache_data = new_cache

    return {"message": "Cache regenerated successfully", "cache": new_cache}

# Add this block to run the app with uvicorn when executing `python api.py`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
