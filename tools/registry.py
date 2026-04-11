import urllib.request
import json
from typing import Callable, Dict, Any

def get_location() -> str:
    """
    Detects and returns the current user's geographical location.
    Call this tool when the user asks where they are or asks for localized information.
    """
    try:
        req = urllib.request.Request("http://ip-api.com/json/", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            return f"{data.get('city')}, {data.get('regionName')}, {data.get('country')}"
    except Exception as e:
        return f"Location unknown (error: {e})"

def get_weather(location: str) -> str:
    """
    Fetches the current weather and up to 3 days of forecast for a given location.
    Call this tool when the user asks for the weather or forecast.
    """
    import urllib.parse
    loc_encoded = urllib.parse.quote(location)
    try:
        req = urllib.request.Request(f"https://wttr.in/{loc_encoded}?format=j1", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            current = data['current_condition'][0]
            forecast = data.get('weather', [])
            
            res = f"Current Weather in {location}: {current['temp_C']}°C, {current['weatherDesc'][0]['value']}. "
            if forecast:
                res += "Forecast: "
                for day in forecast:
                    res += f"[{day['date']}] High {day['maxtempC']}°C, Low {day['mintempC']}°C. "
                    hourly_res = []
                    for h in day.get('hourly', []):
                        t = h.get('time')
                        if t == "900": hourly_res.append(f"Morning: {h['tempC']}°C {h['weatherDesc'][0]['value']}")
                        elif t == "1500": hourly_res.append(f"Afternoon: {h['tempC']}°C {h['weatherDesc'][0]['value']}")
                        elif t == "1800": hourly_res.append(f"Evening: {h['tempC']}°C {h['weatherDesc'][0]['value']}")
                        elif t == "2100": hourly_res.append(f"Night: {h['tempC']}°C {h['weatherDesc'][0]['value']}")
                    if hourly_res:
                        res += "(" + ", ".join(hourly_res) + ") "
            return res.strip()
    except Exception as e:
        return f"Could not fetch weather for {location} (error: {e})"

AVAILABLE_TOOLS = [get_location, get_weather]

def execute_tool(name: str, arguments: Dict[str, Any]) -> str:
    tool_map = {
        "get_location": get_location,
        "get_weather": get_weather
    }
    
    func = tool_map.get(name)
    if not func:
        return f"Error: Tool '{name}' not found."
        
    try:
        return str(func(**arguments))
    except Exception as e:
        return f"Error executing {name}: {e}"