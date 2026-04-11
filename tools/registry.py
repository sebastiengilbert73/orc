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

def web_search(query: str) -> str:
    """
    Performs a web search using the provided query and returns a summary of the top results with their source URLs.
    Call this tool when you need to find up-to-date information, news, or facts on the internet.
    """
    import urllib.parse
    import urllib.request
    import re
    
    try:
        url = "https://lite.duckduckgo.com/lite/"
        data = urllib.parse.urlencode({'q': query}).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
            
            # Extract result links: href comes BEFORE class='result-link' in DDG Lite
            links = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]+class=["\']result-link["\'][^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
            # Extract snippets
            snippets = re.findall(r'<td[^>]*class=["\']result-snippet["\'][^>]*>(.*?)</td>', html, re.IGNORECASE | re.DOTALL)
            
            results = []
            count = min(len(links), len(snippets), 5)
            if count == 0:
                return "No results found."
            
            for i in range(count):
                link_url = links[i][0].strip()
                title = re.sub(r'<[^>]+>', '', links[i][1]).strip()
                snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip()
                results.append(f"[{i+1}] {title}\n    URL: {link_url}\n    {snippet}")
            
            return "Web Search Results:\n" + "\n\n".join(results)
    except Exception as e:
        return f"Error performing web search: {e}"

def ask_user(question: str) -> str:
    """
    Suspends the agent's execution to ask the user a question.
    Call this tool when you lack critical information necessary to complete a task and need human input.
    """
    # This function is never called directly.
    # agent_runner.py intercepts 'ask_user' tool calls and delegates
    # to task_manager.request_user_input() which pauses the task,
    # waits for the user's reply via the dashboard, then resumes.
    raise RuntimeError("ask_user should be intercepted by agent_runner, not called directly")

AVAILABLE_TOOLS = [get_location, get_weather, web_search, ask_user]

def execute_tool(name: str, arguments: Dict[str, Any]) -> str:
    tool_map = {
        "get_location": get_location,
        "get_weather": get_weather,
        "web_search": web_search,
        "ask_user": ask_user
    }
    
    func = tool_map.get(name)
    if not func:
        return f"Error: Tool '{name}' not found."
        
    try:
        return str(func(**arguments))
    except Exception as e:
        return f"Error executing {name}: {e}"