const API_BASE = "http://localhost:8000";

export const getModels = async () => {
    const res = await fetch(`${API_BASE}/models`);
    if (!res.ok) throw new Error("Failed to fetch models");
    return res.json();
};

export const getOllamaHost = async () => {
    const res = await fetch(`${API_BASE}/config/ollama-host`);
    if (!res.ok) throw new Error("Failed to fetch ollama host");
    return res.json();
};

export const setOllamaHost = async (host) => {
    const res = await fetch(`${API_BASE}/config/ollama-host`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ host })
    });
    if (!res.ok) throw new Error("Failed to set ollama host");
    return res.json();
};

export const getAllMemory = async () => {
    const res = await fetch(`${API_BASE}/memory`);
    if (!res.ok) throw new Error("Failed to fetch memory");
    return res.json();
};

export const getAgents = async () => {
    const res = await fetch(`${API_BASE}/agents`);
    if (!res.ok) throw new Error("Failed to fetch agents");
    return res.json();
};

export const createAgent = async (agentData) => {
    const res = await fetch(`${API_BASE}/agents`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(agentData)
    });
    if (!res.ok) throw new Error("Failed to create agent");
    return res.json();
};

export const updateAgent = async (agentId, agentData) => {
    const res = await fetch(`${API_BASE}/agents/${agentId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(agentData)
    });
    if (!res.ok) throw new Error("Failed to update agent");
    return res.json();
};

export const toggleAgent = async (agentId) => {
    const res = await fetch(`${API_BASE}/agents/${agentId}/toggle`, { method: "POST" });
    if (!res.ok) throw new Error("Failed to toggle agent");
    return res.json();
};

export const deleteAgent = async (agentId) => {
    const res = await fetch(`${API_BASE}/agents/${agentId}`, { method: "DELETE" });
    if (!res.ok) throw new Error("Failed to delete agent");
    return res.json();
};

export const getTools = async () => {
    const res = await fetch(`${API_BASE}/tools`);
    if (!res.ok) throw new Error("Failed to fetch tools");
    return res.json();
};

export const getTasks = async () => {
    const res = await fetch(`${API_BASE}/tasks`);
    if (!res.ok) throw new Error("Failed to fetch tasks");
    return res.json();
};

export const createTask = async (taskData) => {
    const res = await fetch(`${API_BASE}/tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(taskData)
    });
    return res.json();
};

export const startTask = async (taskId) => {
    const res = await fetch(`${API_BASE}/tasks/${taskId}/start`, { method: "POST" });
    return res.json();
};

export const stopTask = async (taskId) => {
    const res = await fetch(`${API_BASE}/tasks/${taskId}/stop`, { method: "POST" });
    return res.json();
};

export const updateTask = async (taskId, taskData) => {
    const res = await fetch(`${API_BASE}/tasks/${taskId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(taskData)
    });
    if (!res.ok) throw new Error("Failed to update task");
    return res.json();
};

export const getTaskMemory = async (taskId) => {
    const res = await fetch(`${API_BASE}/tasks/${taskId}/memory`);
    if (!res.ok) throw new Error("Failed to fetch task memory");
    return res.json();
};

export const replyToTask = async (taskId, answer) => {
    const res = await fetch(`${API_BASE}/tasks/${taskId}/reply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer })
    });
    if (!res.ok) throw new Error("Failed to reply to task");
    return res.json();
};
