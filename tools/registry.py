import urllib.request
import json
from typing import Callable, Dict, Any, List, Union, Tuple

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

def read_url(url: str) -> str:
    """
    Fetches the content of a web page and returns its main text.
    Call this tool when you have a specific URL and need to read the full article or page content.
    Arguments:
        url: The full URL to read (e.g. 'https://www.example.com/article').
    """
    import urllib.request
    import re
    from html import unescape
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            # Remove scripts and styles
            html = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
            # Remove all other tags
            text = re.sub(r'<[^>]+>', ' ', html)
            # Unescape HTML entities
            text = unescape(text)
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Return first 8000 characters to avoid context overflow for simple tasks
            if len(text) > 8000:
                return text[:8000] + "... [Content Truncated]"
            return text
            
    except Exception as e:
        return f"Error reading URL {url}: {e}"

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

def search_agents(specialization: str) -> str:
    """
    Searches for available agents with a specific specialization or skill.
    Call this tool to find collaborators who can help with specialized tasks.
    Arguments:
        specialization: The skill or area of expertise to search for (e.g. 'coding', 'research', 'design').
    """
    raise RuntimeError("search_agents should be intercepted by agent_runner")

def call_agent(agent_name: str, task: str) -> str:
    """
    Delegates a specific sub-task to another agent and waits for their response.
    Call this tool when you have found a suitable collaborator and want them to perform a task for you.
    Arguments:
        agent_name: The exact name of the agent to call.
        task: A detailed description of the task you want the other agent to perform.
    """
    raise RuntimeError("call_agent should be intercepted by agent_runner")

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

def speech_to_text(seconds: int, language: str) -> str:
    """
    Records a given number of seconds of audio and transcribes the speech to text.
    Supports English and French. Shows a live visual progress bar during recording.
    Exposes starting and ending signals via task memory and system beeps.
    Arguments:
        seconds: Number of seconds to record audio for.
        language: Language code ('en' for English, 'fr' for French).
    """
    import os
    import sys
    import time
    import sounddevice as sd
    import numpy as np
    import wavio
    from transformers import pipeline

    try:
        # Fetch current task context to write to task memories
        from engine.context import current_task_id, current_agent_id
        task_id_val = current_task_id.get() or os.environ.get("CURRENT_TASK_ID")
        agent_id_val = current_agent_id.get() or os.environ.get("CURRENT_AGENT_ID")
        
        db_helper = None
        if task_id_val and agent_id_val:
            try:
                from engine.memory_manager import MemoryManager
                from uuid import UUID
                task_uuid = task_id_val if isinstance(task_id_val, UUID) else UUID(task_id_val)
                agent_uuid = agent_id_val if isinstance(agent_id_val, UUID) else UUID(agent_id_val)
                db_helper = lambda text: MemoryManager.add_memory(
                    agent_id=agent_uuid,
                    task_id=task_uuid,
                    interaction_type="Action",
                    content=text
                )
            except Exception as e:
                print(f"Failed to setup memory logging helper: {e}")
                
        fs = 44100
        start_msg = "🔴 [Audio Recording Started] Please speak now..."
        print(f"\n{start_msg}")
        if db_helper:
            db_helper(start_msg)
            
        # Play start sound signal (beep)
        try:
            import winsound
            winsound.Beep(1000, 400)
        except Exception as e:
            print(f"Beep error: {e}")
            
        recording = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='int16')
        
        # Display progress bar
        bar_width = 30
        for i in range(101):
            time.sleep(seconds / 100.0)
            progress = int((i / 100.0) * bar_width)
            bar = "█" * progress + "-" * (bar_width - progress)
            sys.stdout.write(f"\rRecording: |{bar}| {i}%")
            sys.stdout.flush()
            
        sd.wait()
        
        end_msg = "🟩 [Audio Recording Finished]"
        print(f"\n{end_msg}\n")
        if db_helper:
            db_helper(end_msg)
            
        # Play end sound signal (double beep)
        try:
            import winsound
            winsound.Beep(1500, 200)
            time.sleep(0.05)
            winsound.Beep(1500, 200)
        except Exception as e:
            print(f"Beep error: {e}")
            
        # Save the recorded audio to a WAV file
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
        os.makedirs(output_dir, exist_ok=True)
        wav_path = os.path.join(output_dir, "recorded_audio.wav")
        wavio.write(wav_path, recording, fs)
        
        # Transcribe the speech using a pre-trained model from Hugging Face's transformers library
        if language == 'en':
            transcriber = pipeline("automatic-speech-recognition", model="facebook/wav2vec2-base-960h")
        elif language == 'fr':
            transcriber = pipeline("automatic-speech-recognition", model="jonatasgrosman/wav2vec2-large-xlsr-53-french")
        else:
            return f"Unsupported language: {language}"
        
        result = transcriber(wav_path)
        transcription = result['text']
        return transcription
    
    except Exception as e:
        return f"Error: {e}"

def create_1d_plot(
    data: Union[List[float], List[Tuple[float, float]], str], 
    x_label: str, 
    y_label: str, 
    title: str,
    x_min: Union[float, str] = -10.0,
    x_max: Union[float, str] = 10.0
) -> str:
    """
    Generates a 1D line plot. If the data is a mathematical formula of 'x' (like 'sin(x)/x' or 'x**2 - 2*x'), it automatically evaluates it and plots the curve. Always prefer passing a formula string (e.g. 'sin(x)/x') for mathematical functions to ensure accuracy.
    Arguments:
        data: A list of float values, list of (x,y) pairs, or a mathematical formula string of 'x' (e.g. 'sin(x)/x', 'x**2').
        x_label: The label for the x-axis.
        y_label: The label for the y-axis.
        title: The title of the plot. Will be used to name the saved file.
        x_min: Optional minimum x value when evaluating a formula string (defaults to -10.0). Can be a number or a formula like 'pi/2'.
        x_max: Optional maximum x value when evaluating a formula string (defaults to 10.0). Can be a number or a formula like 'pi/2'.
    """
    import matplotlib.pyplot as plt
    import os
    import re
    import numpy as np
    import math

    # Parse mathematical limits for x_min and x_max
    safe_math_dict = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
    safe_math_dict['pi'] = math.pi
    safe_math_dict['e'] = math.e

    def parse_limit(val, default):
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            try:
                return float(eval(val, {"__builtins__": {}}, safe_math_dict))
            except Exception:
                pass
        return default

    x_min_val = parse_limit(x_min, -10.0)
    x_max_val = parse_limit(x_max, 10.0)

    # Handle string input or mathematical formula
    if isinstance(data, str):
        data_clean = data.strip()
        # Check if it's a formula rather than a JSON array
        if not (data_clean.startswith('[') and data_clean.endswith(']')) and any(c in data_clean for c in ['x', 'sin', 'cos', 'tan', 'exp', 'log', 'pi', 'sinc']):
            x_vals = np.linspace(x_min_val, x_max_val, 500)
            # Avoid division by zero by replacing exact 0.0 with a tiny value
            x_vals_safe = np.where(x_vals == 0, 1e-20, x_vals)
            
            # Safe evaluation context with numpy functions mapped to standard names
            safe_dict = {
                'x': x_vals_safe,
                'np': np,
                'numpy': np,
                'sin': np.sin,
                'cos': np.cos,
                'tan': np.tan,
                'exp': np.exp,
                'log': np.log,
                'sqrt': np.sqrt,
                'pi': np.pi,
                'e': np.e,
                'sinc': lambda val: np.where(val == 0, 1.0, np.sin(val) / val)
            }
            try:
                y_vals = eval(data_clean, {"__builtins__": {}}, safe_dict)
                if isinstance(y_vals, (int, float)):
                    y_vals = np.full_like(x_vals, y_vals)
                data = list(zip(x_vals, y_vals))
            except Exception as e:
                return f"Error evaluating formula '{data_clean}': {e}"
        else:
            try:
                import json
                parsed = json.loads(data_clean)
                if isinstance(parsed, list):
                    data = parsed
            except Exception:
                cleaned = data_clean.replace('[', '').replace(']', '').replace('"', '').replace("'", "")
                if ',' in cleaned:
                    data = [float(val.strip()) for val in cleaned.split(',') if val.strip()]
                else:
                    data = [float(val.strip()) for val in cleaned.split() if val.strip()]

    if not data or len(data) == 0:
        raise ValueError("The data list is empty.")

    # Determine types and extract x, y
    if not isinstance(data[0], (list, tuple)):
        y = data
        x = list(range(len(data)))
        marker_style = "o"  # Use markers for discrete list of points
    else:
        x, y = zip(*data)
        marker_style = ""   # No markers for dense curves (like formulas)

    fig, ax = plt.subplots()
    ax.plot(x, y, marker=marker_style, color="#0284c7", linewidth=2)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.grid(True, linestyle="--", alpha=0.5)

    # Ensure output dir exists
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    safe_title = re.sub(r'[^a-zA-Z0-9_]', '_', title).strip('_') or 'plot'
    filename = os.path.join(output_dir, f"{safe_title}.png")
    
    fig.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close(fig)

    return f"Plot created successfully and saved to: output/{os.path.basename(filename)}"

AVAILABLE_TOOLS = [get_location, get_weather, web_search, read_url, ask_user, list_directory, read_text, read_pdf, calculator, write_to_pdf, write_to_md, search_agents, call_agent, speech_to_text, create_1d_plot]

def run_code_with_auto_install(python_code: str, name: str) -> Dict[str, Any]:
    import sys
    import subprocess
    max_retries = 5
    
    # Pre-compile to catch syntax errors immediately
    compiled = compile(python_code, "<string>", "exec")
    
    for attempt in range(max_retries):
        try:
            local_scope = {}
            exec(compiled, local_scope)
            return local_scope
        except ModuleNotFoundError as mne:
            missing_module = mne.name
            if not missing_module:
                raise
            
            package_map = {
                "bs4": "beautifulsoup4",
                "fitz": "pymupdf",
                "PIL": "pillow",
                "yaml": "pyyaml",
                "cv2": "opencv-python",
                "sklearn": "scikit-learn",
                "skimage": "scikit-image",
                "dotenv": "python-dotenv"
            }
            package_to_install = package_map.get(missing_module, missing_module)
            print(f"Dynamically installing missing module '{package_to_install}'...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_to_install])
    raise RuntimeError("Failed to resolve missing dependencies after several attempts.")

def load_custom_tools() -> Dict[str, Any]:
    import sys
    import os
    from sqlmodel import Session, select
    from database.db import engine
    from core.models import CustomTool

    custom_tools_map = {}
    try:
        with Session(engine) as session:
            custom_tools = session.exec(select(CustomTool)).all()
            for ct in custom_tools:
                try:
                    local_scope = run_code_with_auto_install(ct.python_code, ct.name)
                    func = local_scope.get(ct.name)
                    if func:
                        func.__name__ = ct.name
                        # Override docstring with description if function lacks docstring
                        func.__doc__ = func.__doc__ or ct.description
                        custom_tools_map[ct.name] = func
                except Exception as e:
                    print(f"Error compiling custom tool {ct.name}: {e}")
    except Exception as e:
        print(f"Error loading custom tools from database: {e}")
    return custom_tools_map

def get_all_compiled_tools() -> list:
    custom_tools = load_custom_tools()
    return AVAILABLE_TOOLS + list(custom_tools.values())

def execute_tool(name: str, arguments: Dict[str, Any]) -> str:
    tool_map = {
        "get_location": get_location,
        "get_weather": get_weather,
        "web_search": web_search,
        "read_url": read_url,
        "ask_user": ask_user,
        "list_directory": list_directory,
        "read_text": read_text,
        "read_pdf": read_pdf,
        "calculator": calculator,
        "write_to_pdf": write_to_pdf,
        "write_to_md": write_to_md,
        "speech_to_text": speech_to_text,
        "create_1d_plot": create_1d_plot
    }

    func = tool_map.get(name)
    if not func:
        # Check if it's a dynamic custom tool
        custom_tools = load_custom_tools()
        func = custom_tools.get(name)

    if not func:
        return f"Error: Tool '{name}' not found."

    try:
        return str(func(**arguments))
    except Exception as e:
        return f"Error executing {name}: {e}"

