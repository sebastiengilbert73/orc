# 🧌 orc: Agentic AI Orchestration Engine 🚀

Welcome to **orc**, a powerful orchestration platform designed to manage and empower autonomous AI agents. Whether you're building a personal assistant, a research bot, or a complex automation workflow, **orc** provides the foundation to bring your agents to life!

---

## 🌟 Overview

**orc** is a modular system that allows you to create, manage, and monitor AI agents. Each agent can be customized with a unique persona, specific skills, and a suite of tools. From web browsing to PDF analysis, **orc** agents are built to *do* things, not just talk.

### ✨ Key Features

*   **👥 Persona-Driven Agents**: Create agents with distinct personalities and specializations.
*   **🛠️ Rich Toolset**: Agents have access to a variety of tools like web search, weather reports, calculators, and document readers.
*   **🧠 Persistent Memory**: Agents remember their past tasks, successful actions, and even their failures, allowing them to learn and adapt.
*   **📊 Live Dashboard**: A sleek, modern interface to monitor all your running tasks and agents in real-time.
*   **📄 Professional Reporting**: Generate beautiful PDF and Markdown reports automatically from agent findings.
*   **❓ Human-in-the-Loop**: Agents can stop to ask the user for clarification when they hit a roadblock.

---

## 🛠️ Built With

| Component | Technology |
| :--- | :--- |
| **Backend** | [FastAPI](https://fastapi.tiangolo.com/) + [SQLModel](https://sqlmodel.tiangolo.com/) |
| **Frontend** | [React](https://reactjs.org/) + [Vite](https://vitejs.dev/) |
| **Logic** | [Python 3.10+](https://www.python.org/) |
| **Database** | [SQLite](https://www.sqlite.org/) |

---

## 🚀 Getting Started

### 📋 Prerequisites

*   Python 3.10 or higher
*   Node.js & npm (for the dashboard)
*   Ollama (running locally for LLM support)

### 🔧 Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/sebastiengilbert73/orc.git
    cd orc
    ```

2.  **Setup the Backend**:
    ```powershell
    # Create and activate a virtual environment
    python -m venv .venv
    .\.venv\Scripts\Activate

    # Install dependencies
    pip install -r requirements.txt
    ```

3.  **Setup the Frontend**:
    ```powershell
    cd dashboard
    npm install
    ```

### 🏃 Running the Project

You'll need two terminals open:

**Terminal 1: Backend**
```powershell
python main.py
```

**Terminal 2: Frontend**
```powershell
cd dashboard
npm run dev
```

---

## 🧰 The Agent's Toolbox

Current agents come equipped with:

*   🌐 **Web Search**: DuckDuckGo integration for real-time internet access.
*   🌦️ **Weather**: Get current conditions and forecasts for any city.
*   📂 **File System**: List directories and read text/PDF files.
*   🧮 **Calculator**: Precise mathematical expression evaluation.
*   📍 **Geo-location**: Detection of the current environment.
*   📝 **Report Generator**: Create professional-grade `.pdf` and `.md` files.

---

## 🗺️ Roadmap

- [ ] 🧪 Multi-agent collaboration (Swarm mode)
- [ ] 🗣️ Voice interface for the dashboard
- [ ] 🔌 Plugin system for custom tool registration
- [ ] 🐳 Docker support for easy deployment

---

## ⚖️ License

Distributed under the MIT License. See `LICENSE` for more information.

---

*Made with ❤️ for the world of Agentic AI.*