# Construction Site risk estimation by weather forecast
Provides an overview of current weather-related risks on the construction site via an LLM (RAG), colors worksites at risk by weeks and days green, yellow or red accordingly based on pre-defined risk values.

Created for the DataCon.AI hackathon in 24 hours.
![](/preview.png)
![](/image.png)

## Parts

- API: Backend. Required for any action with the DB or any API (OpenAI, OpenWeatherMap)
- App: The frontend part running on Streamlit. Accesses the Rest API and maps the costruction site accordingly.

The generated (LLMs) data in /api is being cached and can be regenerated on any set interval (suggestion: 6-12hrs).

## Usage
Install requirements

`pip install -r requirements.txt`

Replace OpenWeatherMap and OpenAI API key in `api/api.py`

Launch

```
python api/api.py
python app/main.py
```