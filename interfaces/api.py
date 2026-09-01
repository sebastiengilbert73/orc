from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional, Dict
from uuid import UUID
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from database.db import get_session, create_db_and_tables
from database.seed import seed_default_agents
from core.models import Agent, Task, Memory, CustomTool
from engine.task_manager import task_manager
from engine.memory_manager import MemoryManager
from contextlib import asynccontextmanager
from tools.registry import AVAILABLE_TOOLS, run_code_with_auto_install
import ollama
from core.config import get_ollama_host, set_ollama_host

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    seed_default_agents()
    yield
    # Any cleanup

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development, typically you'd restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
from fastapi.staticfiles import StaticFiles
os.makedirs("output", exist_ok=True)
app.mount("/output", StaticFiles(directory="output"), name="output")

@app.get("/models", response_model=List[str])
def list_models():
    try:
        client = ollama.Client(host=get_ollama_host())
        response = client.list()
        return [m.get('model', m.get('name', '')) for m in response.get('models', [])]
    except Exception as e:
        print(f"Error fetching models: {e}")
        return []

@app.get("/tools", response_model=List[str])
def list_tools(session: Session = Depends(get_session)):
    custom_tools = session.exec(select(CustomTool)).all()
    static = [t.__name__ for t in AVAILABLE_TOOLS]
    custom = [ct.name for ct in custom_tools]
    try:
        from tools.mcp_manager import get_mcp_server_names
        mcp_servers = get_mcp_server_names()
    except Exception as e:
        print(f"Error fetching MCP server names for API: {e}")
        mcp_servers = []
    return static + custom + mcp_servers

class MCPServerCreate(BaseModel):
    name: str
    command: str = "npx"
    args: List[str] = []
    env: Dict[str, str] = {}
    enabled: bool = True
    is_local: bool = False


class OllamaHostConfig(BaseModel):
    host: str

@app.get("/config/ollama-host", response_model=OllamaHostConfig)
def get_host():
    return OllamaHostConfig(host=get_ollama_host())

@app.put("/config/ollama-host")
def set_host(config: OllamaHostConfig):
    set_ollama_host(config.host)
    return {"status": "success", "host": config.host}

@app.get("/memory", response_model=List[Memory])
def get_all_memory(limit: int = 200, session: Session = Depends(get_session)):
    statement = select(Memory).order_by(Memory.timestamp.desc()).limit(limit)
    return session.exec(statement).all()
# --- Models ---
class AgentCreate(BaseModel):
    name: str
    persona: str = ""
    model_name: str = ""
    specializations: List[str] = []
    tools: List[str] = []

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    persona: Optional[str] = None
    model_name: Optional[str] = None
    tools: Optional[List[str]] = None

class TaskCreate(BaseModel):
    agent_id: UUID
    description: str
    duration_limit: int = None

class TaskUpdate(BaseModel):
    agent_id: Optional[UUID] = None
    description: Optional[str] = None
    duration_limit: Optional[int] = None

class UserReply(BaseModel):
    answer: str

# --- Agent Endpoints ---

@app.post("/agents", response_model=Agent)
def create_agent(agent: Agent, session: Session = Depends(get_session)):
    session.add(agent)
    session.commit()
    session.refresh(agent)
    return agent

@app.get("/agents", response_model=List[Agent])
def get_agents(session: Session = Depends(get_session)):
    agents = session.exec(select(Agent)).all()
    return agents

@app.post("/agents/{agent_id}/toggle", response_model=Agent)
def toggle_agent(agent_id: UUID, session: Session = Depends(get_session)):
    agent = session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.is_active = not agent.is_active
    session.add(agent)
    session.commit()
    session.refresh(agent)
    return agent

@app.delete("/agents/{agent_id}")
def delete_agent(agent_id: UUID, session: Session = Depends(get_session)):
    agent = session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    session.delete(agent)
    session.commit()
    return {"status": "deleted"}

@app.post("/agents/{agent_id}/wipe_memory")
def wipe_agent_memory(agent_id: UUID, session: Session = Depends(get_session)):
    agent = session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    MemoryManager.erase_agent_memory(agent_id)
    return {"status": "success"}

@app.get("/agents/{agent_id}/memory", response_model=List[Memory])
def get_agent_memory(agent_id: UUID, session: Session = Depends(get_session)):
    return MemoryManager.get_agent_memory(agent_id)

@app.put("/agents/{agent_id}", response_model=Agent)
def update_agent(agent_id: UUID, agent_update: AgentUpdate, session: Session = Depends(get_session)):
    agent = session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    update_data = agent_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(agent, key, value)
        
    session.add(agent)
    session.commit()
    session.refresh(agent)
    return agent

# --- Task Endpoints ---

@app.post("/tasks", response_model=Task)
def create_task(task_in: TaskCreate, session: Session = Depends(get_session)):
    task = Task(
        agent_id=task_in.agent_id, 
        description=task_in.description, 
        duration_limit=task_in.duration_limit
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

@app.get("/tasks", response_model=List[Task])
def get_tasks(session: Session = Depends(get_session)):
    tasks = session.exec(select(Task).order_by(Task.created_at.desc())).all()
    return tasks

@app.get("/tasks/{task_id}/memory", response_model=List[Memory])
def get_task_memory(task_id: UUID, session: Session = Depends(get_session)):
    return MemoryManager.get_task_memory(task_id)

@app.post("/tasks/{task_id}/start")
async def start_task(task_id: UUID, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task_manager.start_task(task_id, task.agent_id, task.duration_limit)
    return {"status": "started"}

@app.post("/tasks/{task_id}/stop")
async def stop_task(task_id: UUID):
    task_manager.stop_task(task_id)
    return {"status": "stop signal sent"}

@app.post("/tasks/{task_id}/reply")
async def reply_to_task(task_id: UUID, reply: UserReply):
    task_manager.provide_input(task_id, reply.answer)
    return {"status": "reply sent"}
@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: UUID, task_update: TaskUpdate, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status != "Pending":
        raise HTTPException(status_code=400, detail="Only Pending tasks can be edited")
    
    update_data = task_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

class CustomToolCreate(BaseModel):
    name: str
    description: str
    python_code: str

@app.post("/custom-tools", response_model=CustomTool)
def create_custom_tool(tool_create: CustomToolCreate, session: Session = Depends(get_session)):
    import re
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', tool_create.name):
        raise HTTPException(status_code=400, detail="Tool name must be a valid Python identifier (alphanumeric/underscores, starting with a letter/underscore).")

    static_names = [t.__name__ for t in AVAILABLE_TOOLS]
    if tool_create.name in static_names:
        raise HTTPException(status_code=400, detail="Cannot override built-in static tools.")

    try:
        local_scope = run_code_with_auto_install(tool_create.python_code, tool_create.name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Validation failed: {e}")
        
    if tool_create.name not in local_scope:
        raise HTTPException(status_code=400, detail=f"The python code must define a function named '{tool_create.name}'")

    existing = session.exec(select(CustomTool).where(CustomTool.name == tool_create.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="A custom tool with this name already exists.")
        
    db_tool = CustomTool(
        name=tool_create.name,
        description=tool_create.description,
        python_code=tool_create.python_code
    )
    session.add(db_tool)
    session.commit()
    session.refresh(db_tool)
    return db_tool

@app.get("/custom-tools", response_model=List[CustomTool])
def list_custom_tools(session: Session = Depends(get_session)):
    return session.exec(select(CustomTool)).all()

@app.delete("/custom-tools/{tool_id}")
def delete_custom_tool(tool_id: UUID, session: Session = Depends(get_session)):
    tool = session.get(CustomTool, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Custom tool not found")
    session.delete(tool)
    session.commit()
    return {"status": "success", "message": f"Tool '{tool.name}' deleted."}

class ToolGenerateRequest(BaseModel):
    name: str
    description: str

@app.post("/custom-tools/generate")
async def generate_custom_tool_code(req: ToolGenerateRequest):
    import ollama
    from core.config import get_ollama_host
    try:
        client = ollama.Client(host=get_ollama_host())
        response = client.list()
        models = [m.get('model', m.get('name', '')) for m in response.get('models', [])]
        
        # Check if there is an active model already loaded in memory to avoid swapping/thrashing
        try:
            active = client.ps()
            active_models = [m.model for m in getattr(active, 'models', [])]
        except Exception:
            active_models = []
    except Exception:
        models = []
        active_models = []

    if not models:
        model_name = "llama3.2"
    else:
        # 1. Prefer active models already loaded in memory
        # 2. Prefer coder models
        # 3. Fallback to first available model
        coder_models = [m for m in models if "coder" in m or "code" in m]
        
        if active_models:
            model_name = active_models[0]
        elif coder_models:
            model_name = coder_models[0]
        else:
            model_name = models[0]

    prompt = f"""You are an expert Python coder.
Generate a Python function for a custom tool with the name '{req.name}'.
The tool capabilities/description are as follows:
"{req.description}"

Requirements:
1. The function name MUST be exactly '{req.name}'.
2. You MUST use type hints for all arguments and the return type.
3. Keep the function self-contained, import any necessary standard library or popular packages (e.g. requests, matplotlib, urllib, beautifulsoup4, numpy, pandas, etc.) INSIDE the script.
4. If the tool creates a plot, save it as a PNG in the 'output/' directory and return the file path/success message (similar to `create_1d_plot`).
5. Respond ONLY with the Python code block (inside a markdown python code block starting with ```python). Do not include any other conversational text or explanations outside of the code block.

Example structure:
```python
def {req.name}(param1: str, param2: int) -> str:
    \"\"\"
    Docstring explaining the tool.
    \"\"\"
    # code here
    return "result"
```"""

    try:
        from ollama import AsyncClient
        async_client = AsyncClient(host=get_ollama_host())
        chat_response = await async_client.chat(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0.1,
                "num_predict": 1024
            }
        )
        content = chat_response.get("message", {}).get("content", "")
        
        import re
        code_match = re.search(r"```python\s*(.*?)\s*```", content, re.DOTALL)
        if code_match:
            code = code_match.group(1)
        else:
            code = content.strip()
            
        return {"python_code": code}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM generation failed: {e}")

@app.get("/mcp-servers")

def list_mcp_servers():
    from tools.mcp_manager import get_all_mcp_servers
    return get_all_mcp_servers()

@app.post("/mcp-servers")
def create_mcp_server(srv: MCPServerCreate):
    import re
    if not srv.name.strip():
        raise HTTPException(status_code=400, detail="Server name cannot be empty.")
    sanitized_name = re.sub(r'[^a-zA-Z0-9_\-]', '', srv.name.strip())
    if not sanitized_name:
        raise HTTPException(status_code=400, detail="Invalid server name format.")
        
    from tools.mcp_manager import add_mcp_server
    return add_mcp_server(
        name=sanitized_name,
        command=srv.command,
        args=srv.args,
        env=srv.env,
        enabled=srv.enabled,
        is_local=srv.is_local
    )


@app.delete("/mcp-servers/{name}")
def remove_mcp_server(name: str):
    from tools.mcp_manager import delete_mcp_server
    success = delete_mcp_server(name)
    if not success:
        raise HTTPException(status_code=404, detail=f"MCP Server '{name}' not found.")
    return {"status": "success", "message": f"MCP Server '{name}' deleted."}

@app.post("/mcp-servers/{name}/toggle")
def toggle_mcp_server_status(name: str):
    from tools.mcp_manager import toggle_mcp_server
    try:
        updated = toggle_mcp_server(name)
        return updated
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))


