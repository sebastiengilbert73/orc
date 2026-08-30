import pytest
from fastapi.testclient import TestClient
from interfaces.api import app

client = TestClient(app)

def test_api_config_ollama_host():
    res = client.get("/config/ollama-host")
    assert res.status_code == 200
    assert "host" in res.json()

    put_res = client.put("/config/ollama-host", json={"host": "http://localhost:11434"})
    assert put_res.status_code == 200
    assert put_res.json()["host"] == "http://localhost:11434"

def test_api_list_tools():
    res = client.get("/tools")
    assert res.status_code == 200
    tools = res.json()
    assert "calculator" in tools
    assert "write_to_md" in tools

def test_api_agents_crud():
    # 1. Create Agent
    new_agent = {
        "name": "TestAgentAPI",
        "persona": "Tester persona",
        "model_name": "llama3.2",
        "specializations": ["testing"],
        "tools": ["calculator"]
    }
    create_res = client.post("/agents", json=new_agent)
    assert create_res.status_code == 200
    agent_data = create_res.json()
    agent_id = agent_data["id"]
    assert agent_data["name"] == "TestAgentAPI"

    # 2. Get Agents
    get_res = client.get("/agents")
    assert get_res.status_code == 200
    assert any(a["id"] == agent_id for a in get_res.json())

    # 3. Toggle Agent
    toggle_res = client.post(f"/agents/{agent_id}/toggle")
    assert toggle_res.status_code == 200
    assert toggle_res.json()["is_active"] is False

    # 4. Wipe Agent Memory
    wipe_res = client.post(f"/agents/{agent_id}/wipe_memory")
    assert wipe_res.status_code == 200

    # 5. Delete Agent
    del_res = client.delete(f"/agents/{agent_id}")
    assert del_res.status_code == 200

def test_api_tasks_crud():
    # Fetch existing agent or create temporary one
    get_agents = client.get("/agents")
    agents = get_agents.json()
    if agents:
        agent_id = agents[0]["id"]
    else:
        create_res = client.post("/agents", json={"name": "TempAgentTask", "persona": "Test"})
        agent_id = create_res.json()["id"]

    # 1. Create Task
    task_payload = {
        "agent_id": agent_id,
        "description": "API Test Task",
        "duration_limit": 30
    }
    create_task = client.post("/tasks", json=task_payload)
    assert create_task.status_code == 200
    task_data = create_task.json()
    task_id = task_data["id"]
    assert task_data["description"] == "API Test Task"
    assert task_data["status"] == "Pending"

    # 2. Get Tasks
    get_tasks = client.get("/tasks")
    assert get_tasks.status_code == 200
    assert any(t["id"] == task_id for t in get_tasks.json())

    # 3. Update Pending Task
    update_task = client.put(f"/tasks/{task_id}", json={"description": "Updated API Test Task"})
    assert update_task.status_code == 200
    assert update_task.json()["description"] == "Updated API Test Task"

def test_api_custom_tools_rejection():
    # Test creating custom tool with security violation (e.g. import os)
    bad_tool = {
        "name": "bad_tool_test",
        "description": "Bad tool attempting os import",
        "python_code": "import os\ndef bad_tool_test(): pass"
    }
    res = client.post("/custom-tools", json=bad_tool)
    assert res.status_code == 400
    assert "Validation failed" in res.json()["detail"]
