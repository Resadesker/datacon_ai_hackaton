# rag_retrieval.py

from weather_api import WeatherFetcher
from datetime import datetime
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

class WeatherLangChain:
    def __init__(self, weather_fetcher: WeatherFetcher, openai_api_key: str):
        self.weather_fetcher = weather_fetcher
        # Initialize ChatOpenAI with your API key and desired model
        self.llm = ChatOpenAI(
            openai_api_key=openai_api_key,
            model_name="gpt-4",  # or "gpt-3.5-turbo" if you don't have access to GPT-4
            temperature=0.7,
        )

    def get_weather_analysis(self) -> str:
        try:
            data = self.weather_fetcher.get_weather_data()
        except Exception:
            print("something happened idk")
        forecasts = data.get('list', [])
        weather_summaries = self.aggregate_daily_forecasts(forecasts)

        # Combine all daily summaries into a single string
        combined_summary = "\n".join(weather_summaries)

        # Use LangChain's LLM to analyze the combined weather data
        analysis = self.analyze_weather(combined_summary)
        return analysis

    def aggregate_daily_forecasts(self, forecasts):
        daily_data = {}
        for entry in forecasts:
            dt = datetime.utcfromtimestamp(entry['dt'])
            date = dt.date()

            if date not in daily_data:
                daily_data[date] = {
                    'temperatures': [],
                    'weather_descriptions': [],
                    'humidity': [],
                    'wind_speed': [],
                }

            daily_data[date]['temperatures'].append(entry['main']['temp'])
            daily_data[date]['weather_descriptions'].append(entry['weather'][0]['description'])
            daily_data[date]['humidity'].append(entry['main']['humidity'])
            daily_data[date]['wind_speed'].append(entry['wind']['speed'])

        summaries = []
        for date, data in daily_data.items():
            avg_temp = sum(data['temperatures']) / len(data['temperatures'])
            common_desc = max(set(data['weather_descriptions']), key=data['weather_descriptions'].count)
            avg_humidity = sum(data['humidity']) / len(data['humidity'])
            avg_wind_speed = sum(data['wind_speed']) / len(data['wind_speed'])

            content = (
                f"Date: {date}\n"
                f"Average Temperature: {avg_temp:.1f}°C\n"
                f"Weather: {common_desc}\n"
                f"Average Humidity: {avg_humidity:.1f}%\n"
                f"Average Wind Speed: {avg_wind_speed:.1f} m/s\n"
            )
            summaries.append(content)
        return summaries

    def analyze_weather(self, weather_data: str) -> str:
        # Create a prompt template
        construction_description = "Sample construction."
        prompt_template = PromptTemplate(
            input_variables=["weather_data"],
            template=(
                "You are a construction expert providing detailed analysis. You have a construction site and you have to provide a VERY short description of current risks (if they exist) and rate the overall risk from 1 to 10 due to the weather. Womit können Probleme sein (Zement, Schienen, usw)?\n"
                "Analyze the following 5-day weather forecast data and provide a short text, "
                "including important trends, warnings, or recommendations:\n\n"
                f"Construction site description: {construction_description}"
                f"{weather_data}"
            ),
        )

        # Format the prompt with the weather data
        prompt = prompt_template.format(weather_data=weather_data)

        try:
            # Use the LLM to get the analysis
            analysis = self.llm.predict(prompt)
            return analysis

        except Exception as e:
            print(f"Error during OpenAI API call: {e}")
            return ""
