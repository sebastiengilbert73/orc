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

def calculator(expression: str) -> str:
    """
    Evaluates a mathematical expression and returns the result.
    Supports basic arithmetic (+, -, *, /, **), logarithms, trigonometry, and proper order of operations.
    Example expressions: '2 + 2', 'sin(pi / 2)', 'log(100, 10)'
    Arguments:
        expression: The mathematical string expression to evaluate.
    """
    import math
    try:
        allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
        allowed_names['math'] = math
        # Safely evaluate without builtins
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {e}"

def read_text(filepath: str) -> str:
    """
    Reads and returns the content of a text file from disk.
    Call this tool when a file path is provided in the task description and you need to read its content.
    Arguments:
        filepath: The path to the text file to read.
    """
    import os
    if not os.path.isabs(filepath):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filepath = os.path.join(base, filepath)
    
    if not os.path.exists(filepath):
        return f"Error: File not found: {filepath}"
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return f"Content of {os.path.basename(filepath)} ({len(content)} characters):\n{content}"
    except Exception as e:
        return f"Error reading file: {e}"

def read_pdf(filepath: str) -> str:
    """
    Reads and returns the extracted text from a PDF file.
    Call this tool when a PDF file path is provided in the task description and you need to read its content.
    Arguments:
        filepath: The path to the PDF file to read.
    """
    import os
    try:
        import pypdf
    except ImportError:
        return "Error: pypdf library is not installed."
        
    if not os.path.isabs(filepath):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filepath = os.path.join(base, filepath)
    
    if not os.path.exists(filepath):
        return f"Error: File not found: {filepath}"
    
    try:
        reader = pypdf.PdfReader(filepath)
        text = ""
        for i, page in enumerate(reader.pages):
            text += f"\n--- Page {i+1} ---\n"
            text += page.extract_text() or ""
            
        return f"Content of {os.path.basename(filepath)} ({len(reader.pages)} pages):\n{text}"
    except Exception as e:
        return f"Error reading PDF file: {e}"

def list_directory(dirpath: str) -> str:
    """
    Lists all files and subdirectories in the specified directory.
    Call this tool when you need to find out what files are available to analyze or read.
    Arguments:
        dirpath: The path of the directory to list (e.g. '.', './output', or an absolute path).
    """
    import os
    if not os.path.isabs(dirpath):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dirpath = os.path.join(base, dirpath)
        
    if not os.path.exists(dirpath):
        return f"Error: Directory not found: {dirpath}"
    
    if not os.path.isdir(dirpath):
        return f"Error: Path is not a directory: {dirpath}"

    try:
        items = os.listdir(dirpath)
        if not items:
            return f"Directory '{dirpath}' is empty."
            
        result = [f"Contents of {dirpath}:"]
        for item in sorted(items):
            item_path = os.path.join(dirpath, item)
            is_dir = os.path.isdir(item_path)
            prefix = "[DIR] " if is_dir else "[FILE]"
            size = "" if is_dir else f" ({os.path.getsize(item_path)} bytes)"
            result.append(f"  {prefix} {item}{size}")
            
        return "\n".join(result)
    except Exception as e:
        return f"Error listing directory: {e}"

def write_to_pdf(filename: str, title: str, content: str) -> str:
    """
    Writes a formatted report to a PDF file in the ./output/ directory.
    Call this tool when the user asks you to produce a report, a document, or save results to a file.
    Arguments:
        filename: The name of the PDF file (e.g. 'report.pdf'). Will be saved to ./output/filename.
        title: The title displayed at the top of the PDF.
        content: The full text content of the report. Use newlines to separate paragraphs.
    """
    import os
    from fpdf import FPDF
    
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    if not filename.endswith('.pdf'):
        filename += '.pdf'
    filepath = os.path.join(output_dir, filename)
    
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Use a Windows system font that supports Unicode (Arial)
    font_dir = "C:/Windows/Fonts"
    if os.path.exists(os.path.join(font_dir, "arial.ttf")):
        pdf.add_font("ArialUni", "", os.path.join(font_dir, "arial.ttf"))
        pdf.add_font("ArialUni", "B", os.path.join(font_dir, "arialbd.ttf"))
        font_name = "ArialUni"
    else:
        font_name = "Helvetica"
    
    # Title
    pdf.set_font(font_name, "B", 18)
    pdf.multi_cell(0, 12, title, align="C")
    pdf.ln(6)
    
    # Clean up markdown bold/italic markers
    import re
    def clean_md(text):
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # bold
        text = re.sub(r'\*(.+?)\*', r'\1', text)        # italic
        text = text.replace('&amp;', '&')
        text = text.replace('&#x27;', "'")
        text = text.replace('&gt;', '>')
        text = text.replace('&lt;', '<')
        return text.strip()
    
    # Content — split by lines, handle basic markdown-like headers
    pdf.set_font(font_name, "", 11)
    for line in content.split('\n'):
        pdf.set_x(pdf.l_margin)  # Reset cursor to left margin
        stripped = line.strip()
        if stripped.startswith('### '):
            pdf.ln(4)
            pdf.set_font(font_name, "B", 13)
            pdf.multi_cell(0, 7, clean_md(stripped[4:]))
            pdf.set_font(font_name, "", 11)
        elif stripped.startswith('## '):
            pdf.ln(5)
            pdf.set_font(font_name, "B", 15)
            pdf.multi_cell(0, 8, clean_md(stripped[3:]))
            pdf.set_font(font_name, "", 11)
        elif stripped.startswith('# '):
            pdf.ln(6)
            pdf.set_font(font_name, "B", 17)
            pdf.multi_cell(0, 9, clean_md(stripped[2:]))
            pdf.set_font(font_name, "", 11)
        elif stripped.startswith('- ') or stripped.startswith('* '):
            pdf.multi_cell(0, 6, "  \u2022 " + clean_md(stripped[2:]))
        elif stripped.startswith('---'):
            pdf.ln(3)
            pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + pdf.epw, pdf.get_y())
            pdf.ln(3)
        elif stripped == '':
            pdf.ln(3)
        else:
            pdf.multi_cell(0, 6, clean_md(stripped))
    
    pdf.output(filepath)
    return f"PDF saved successfully: {filepath}"

def write_to_md(filename: str, title: str, content: str) -> str:
    """
    Writes a rich Markdown report to a file in the ./output/ directory.
    Call this tool when the user asks you to produce a report or document in Markdown format.
    Use emojis, headers, bullet points, bold, italic, tables, blockquotes, and horizontal rules to make it visually appealing.
    Arguments:
        filename: The name of the Markdown file (e.g. 'report.md'). Will be saved to ./output/filename.
        title: The title displayed at the top of the document.
        content: The full Markdown content of the report. Use rich formatting: emojis, headers (##, ###), bold (**text**), bullet points, tables, blockquotes (>), and horizontal rules (---).
    """
    import os
    from datetime import datetime

    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
    os.makedirs(output_dir, exist_ok=True)

    if not filename.endswith('.md'):
        filename += '.md'
    filepath = os.path.join(output_dir, filename)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    header = f"# {title}\n\n"
    header += f"> 📅 *Généré le {now}*  \n"
    header += f"> 🤖 *Rapport produit par orc — Agentic AI Orchestration Engine*\n\n"
    header += "---\n\n"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(header + content + "\n")

    return f"Markdown report saved successfully: {filepath}"

AVAILABLE_TOOLS = [get_location, get_weather, web_search, ask_user, list_directory, read_text, read_pdf, calculator, write_to_pdf, write_to_md]

def execute_tool(name: str, arguments: Dict[str, Any]) -> str:
    tool_map = {
        "get_location": get_location,
        "get_weather": get_weather,
        "web_search": web_search,
        "ask_user": ask_user,
        "list_directory": list_directory,
        "read_text": read_text,
        "read_pdf": read_pdf,
        "calculator": calculator,
        "write_to_pdf": write_to_pdf,
        "write_to_md": write_to_md
    }
    
    func = tool_map.get(name)
    if not func:
        return f"Error: Tool '{name}' not found."
        
    try:
        return str(func(**arguments))
    except Exception as e:
        return f"Error executing {name}: {e}"