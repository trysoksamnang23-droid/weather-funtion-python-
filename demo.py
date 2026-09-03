import datetime
import requests
import streamlit as st

st.set_page_config(page_title="Cambodia Weather", page_icon="⛅", layout="centered")

PROVINCES = [
    {"name": "Banteay Meanchey", "lat": 13.7532, "lon": 102.9896},
    {"name": "Battambang", "lat": 13.1027, "lon": 103.1982},
    {"name": "Kampong Cham", "lat": 12.0983, "lon": 105.3131},
    {"name": "Kampong Chhnang", "lat": 12.2500, "lon": 104.6667},
    {"name": "Kampong Speu", "lat": 11.6155, "lon": 104.3792},
    {"name": "Kampong Thom", "lat": 12.8167, "lon": 103.8413},
    {"name": "Kampot", "lat": 10.7325, "lon": 104.3792},
    {"name": "Kandal", "lat": 11.2237, "lon": 105.1259},
    {"name": "Kep", "lat": 10.4828, "lon": 104.3167},
    {"name": "Koh Kong", "lat": 11.5763, "lon": 103.3587},
    {"name": "Kratie", "lat": 12.5044, "lon": 105.9700},
    {"name": "Mondulkiri", "lat": 12.7879, "lon": 107.1012},
    {"name": "Oddar Meanchey", "lat": 14.1610, "lon": 103.8216},
    {"name": "Pailin", "lat": 12.8489, "lon": 102.6093},
    {"name": "Phnom Penh", "lat": 11.5564, "lon": 104.9282},
    {"name": "Preah Sihanouk", "lat": 10.6093, "lon": 103.5296},
    {"name": "Preah Vihear", "lat": 14.0086, "lon": 104.8455},
    {"name": "Prey Veng", "lat": 11.3802, "lon": 105.5005},
    {"name": "Pursat", "lat": 12.2721, "lon": 103.7289},
    {"name": "Ratanakiri", "lat": 13.8577, "lon": 107.1012},
    {"name": "Siem Reap", "lat": 13.3618, "lon": 103.8606},
    {"name": "Stung Treng", "lat": 13.5765, "lon": 105.9700},
    {"name": "Svay Rieng", "lat": 11.1427, "lon": 105.8290},
    {"name": "Takeo", "lat": 10.9322, "lon": 104.7988},
    {"name": "Tboung Khmum", "lat": 11.8891, "lon": 105.8760},
]

WMO_CODES = {
    0: ("Clear sky", "☀️"), 1: ("Mainly clear", "☀️"), 2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"), 45: ("Foggy", "🌫️"), 48: ("Rime fog", "🌫️"),
    51: ("Light drizzle", "🌧️"), 53: ("Drizzle", "🌧️"), 55: ("Dense drizzle", "🌧️"),
    56: ("Freezing drizzle", "🌧️"), 57: ("Freezing drizzle", "🌧️"),
    61: ("Slight rain", "🌧️"), 63: ("Moderate rain", "🌧️"), 65: ("Heavy rain", "🌧️"),
    66: ("Freezing rain", "🌧️"), 67: ("Freezing rain", "🌧️"),
    71: ("Slight snow", "❄️"), 73: ("Moderate snow", "❄️"), 75: ("Heavy snow", "❄️"),
    80: ("Rain showers", "🌧️"), 81: ("Rain showers", "🌧️"), 82: ("Heavy showers", "🌧️"),
    95: ("Thunderstorm", "⛈️"), 96: ("Thunderstorm", "⛈️"), 99: ("Thunderstorm", "⛈️")
}

@st.cache_data(ttl=600)
def fetch_weather(lat, lon, use_fahrenheit):
    unit_param = "&temperature_unit=fahrenheit" if use_fahrenheit else ""
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code"
        f"&hourly=temperature_2m,weather_code"
        f"&daily=temperature_2m_max,temperature_2m_min"
        f"&timezone=auto{unit_param}"
    )
    return requests.get(url, timeout=5).json()

st.title("🇰🇭 Cambodia Weather")

col1, col2 = st.columns([3, 1])
with col1:
    selected_name = st.selectbox("Select Province", [p["name"] for p in PROVINCES])
with col2:
    unit = st.radio("Unit", ["°C", "°F"], horizontal=True)

use_fahrenheit = unit == "°F"
prov = next(p for p in PROVINCES if p["name"] == selected_name)

try:
    data = fetch_weather(prov["lat"], prov["lon"], use_fahrenheit)
    current = data["current"]
    daily = data["daily"]
    
    cond_desc, emoji = WMO_CODES.get(current["weather_code"], ("Cloudy", "☁️"))
    unit_str = "°F" if use_fahrenheit else "°C"

    st.markdown("---")
    st.subheader(f"{emoji} {cond_desc}")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Temperature", f"{round(current['temperature_2m'])}{unit_str}")
    m2.metric("Feels Like", f"{round(current['apparent_temperature'])}{unit_str}")
    m3.metric("Humidity", f"{current['relative_humidity_2m']}%")

    m4, m5 = st.columns(2)
    m4.metric("High", f"{round(daily['temperature_2m_max'][0])}{unit_str}")
    m5.metric("Low", f"{round(daily['temperature_2m_min'][0])}{unit_str}")

except Exception as e:
    st.error("Failed to retrieve weather data.")
