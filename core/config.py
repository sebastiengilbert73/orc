import json
import os

CONFIG_FILE = "config.json"

def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"ollama_host": "http://localhost:11434"}

def save_config(config_data: dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config_data, f, indent=4)

def get_ollama_host() -> str:
    return load_config().get("ollama_host", "http://localhost:11434")

def set_ollama_host(host: str):
    config = load_config()
    config["ollama_host"] = host
    save_config(config)