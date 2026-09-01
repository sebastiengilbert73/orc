import { useState, useEffect, memo } from 'react';
import { getAgents, createAgent, getTasks, createTask, startTask, stopTask, updateTask, getModels, getTaskMemory, toggleAgent, getTools, deleteAgent, updateAgent, replyToTask, getAllMemory, getOllamaHost, setOllamaHost, getCustomTools, createCustomTool, deleteCustomTool, generateCustomTool, getMCPServers, createMCPServer, deleteMCPServer, toggleMCPServer } from './api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import './index.css';

const MemoizedMarkdown = memo(({ content, className }) => {
  return (
    <div className={className}>
      <ReactMarkdown 
        remarkPlugins={[remarkGfm, remarkMath]} 
        rehypePlugins={[rehypeKatex]}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
});

function App() {
  const [agents, setAgents] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [models, setModels] = useState([]);
  const [availableTools, setAvailableTools] = useState([]);
  const [taskMemories, setTaskMemories] = useState({});
  const [allMemory, setAllMemory] = useState([]);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [memoryFilter, setMemoryFilter] = useState('all');
  
  // MCP Servers States
  const [toolsSubTab, setToolsSubTab] = useState('mcp'); // 'mcp' | 'custom'
  const [mcpServers, setMcpServers] = useState({});

  const [newMcpName, setNewMcpName] = useState("");
  const [newMcpCommand, setNewMcpCommand] = useState("npx");
  const [newMcpArgs, setNewMcpArgs] = useState("");
  const [newMcpEnv, setNewMcpEnv] = useState("");
  const [mcpError, setMcpError] = useState("");
  const [mcpSuccess, setMcpSuccess] = useState("");

  // Custom Tools States
  const [customTools, setCustomTools] = useState([]);

  const [newToolName, setNewToolName] = useState("");
  const [newToolDesc, setNewToolDesc] = useState("");
  const [newToolCode, setNewToolCode] = useState(
    `def my_custom_tool(param1: str) -> str:\n    \"\"\"\n    Description of the tool.\n    \"\"\"\n    # Your python code here\n    return f"Processed: {param1}"`
  );
  const [newToolError, setNewToolError] = useState("");
  const [newToolSuccess, setNewToolSuccess] = useState("");
  const [generatingToolCode, setGeneratingToolCode] = useState(false);
  
  // Forms states
  const [newAgentName, setNewAgentName] = useState("");
  const [newAgentPersona, setNewAgentPersona] = useState("");
  const [newAgentModel, setNewAgentModel] = useState("");
  const [selectedTools, setSelectedTools] = useState({});
  
  // Edit states
  const [editingAgentId, setEditingAgentId] = useState(null);
  const [editName, setEditName] = useState("");
  const [editPersona, setEditPersona] = useState("");
  const [editModel, setEditModel] = useState("");
  const [editTools, setEditTools] = useState({});

  const [editingTaskId, setEditingTaskId] = useState(null);
  const [editTaskDesc, setEditTaskDesc] = useState("");
  const [editTaskAgent, setEditTaskAgent] = useState("");
  const [editTaskTimeout, setEditTaskTimeout] = useState("");

  const [newTaskDesc, setNewTaskDesc] = useState("");
  const [selectedAgentId, setSelectedAgentId] = useState("");
  const [newTaskTimeout, setNewTaskTimeout] = useState("60");
  const [timeNow, setTimeNow] = useState(Date.now());
  const [replyTexts, setReplyTexts] = useState({});
  const [attachedFiles, setAttachedFiles] = useState([]);
  const [fileInput, setFileInput] = useState("");
  const [attachedDirs, setAttachedDirs] = useState([]);
  const [dirInput, setDirInput] = useState("");
  const [ollamaHostInput, setOllamaHostInput] = useState("http://localhost:11434");
  const [showModal, setShowModal] = useState(false);
  const [modalTitle, setModalTitle] = useState("");
  const [modalText, setModalText] = useState({ description: "", response: "", agent: "", status: "", start: "", end: "", duration: 0, history: [] });
  const [activeModalTab, setActiveModalTab] = useState("summary");
  const [copySuccess, setCopySuccess] = useState(false);

  const extractImages = () => {
    const images = [];
    const pattern = /output[\\/][a-zA-Z0-9_\-\.]+\.(?:png|jpg|jpeg|gif)/gi;
    
    if (modalText.response) {
      const matches = modalText.response.match(pattern);
      if (matches) {
        matches.forEach(m => {
          if (!images.includes(m)) images.push(m);
        });
      }
    }
    
    if (modalText.history) {
      modalText.history.forEach(h => {
        if (h.content) {
          const matches = h.content.match(pattern);
          if (matches) {
            matches.forEach(m => {
              if (!images.includes(m)) images.push(m);
            });
          }
        }
      });
    }
    
    return images;
  };

  const handleCopy = () => {
    let textToCopy = "";
    if (activeModalTab === 'summary') {
      textToCopy = `### AGENT: ${modalText.agent}\n### STATUS: ${modalText.status}\n### TIMING: ${modalText.start} to ${modalText.end} (${modalText.duration}s)\n\n--- DETAILED PROMPT ---\n${modalText.description}\n\n--- AGENT RESPONSE ---\n${modalText.response}`;
    } else {
      textToCopy = modalText.history.map(m => {
        const ts = m.timestamp ? new Date(m.timestamp + 'Z').toLocaleTimeString('fr-CA', {hour12: false}) : '';
        return `[${ts}] ${m.interaction_type.toUpperCase()}\n${m.content}\n${'-'.repeat(20)}`;
      }).join('\n\n');
    }

    navigator.clipboard.writeText(textToCopy);
    setCopySuccess(true);
    setTimeout(() => setCopySuccess(false), 2000);
  };

  const loadData = async () => {
    try {
      const hostRes = await getOllamaHost();
      if (hostRes && hostRes.host) {
          setOllamaHostInput(hostRes.host);
      }

      const ms = await getModels();
      setModels(ms);
      if (ms.length > 0) {
          setNewAgentModel(prev => prev ? prev : ms[0]);
      }
      
      const tls = await getTools();
      setAvailableTools(tls);

      const a = await getAgents();
      setAgents(a);
      
      const activeAgents = a.filter(ag => ag.is_active);
      if (activeAgents.length > 0) {
          setSelectedAgentId(prev => {
              if (prev && activeAgents.some(x => x.id === prev)) return prev;
              return activeAgents[0].id;
          });
      } else {
          setSelectedAgentId("");
      }
      
      const t = await getTasks();
      setTasks(t);
      
      const mem = await getAllMemory();
      setAllMemory(mem);

      const memories = {};
      for (const task of t) {
          memories[task.id] = [];
      }
      const reversedMem = [...mem].reverse();
      for (const m of reversedMem) {
          if (m.task_id && memories[m.task_id]) {
              memories[m.task_id].push(m);
          }
      }
      setTaskMemories(memories);

      const ct = await getCustomTools();
      setCustomTools(ct);

      const mcpSrv = await getMCPServers();
      setMcpServers(mcpSrv || {});
    } catch (e) {
      console.error(e);
    }
  };

  const handleCreateMCPServer = async (e) => {
    e.preventDefault();
    setMcpError("");
    setMcpSuccess("");
    if (!newMcpName.trim()) {
      setMcpError("Please specify a server name (e.g. memory).");
      return;
    }
    try {
      const argsArray = newMcpArgs.trim() ? newMcpArgs.trim().split(/\s+/) : [];
      let envObj = {};
      if (newMcpEnv.trim()) {
        try {
          envObj = JSON.parse(newMcpEnv.trim());
        } catch {
          newMcpEnv.trim().split('\n').forEach(line => {
            const parts = line.split('=');
            if (parts.length >= 2) {
              envObj[parts[0].trim()] = parts.slice(1).join('=').trim();
            }
          });
        }
      }
      await createMCPServer({
        name: newMcpName.trim(),
        command: newMcpCommand.trim() || "npx",
        args: argsArray,
        env: envObj,
        enabled: true
      });
      setMcpSuccess(`MCP Server '${newMcpName}' added successfully!`);
      setNewMcpName("");
      setNewMcpArgs("");
      setNewMcpEnv("");
      await loadData();
    } catch (err) {
      setMcpError(err.message || "Failed to add MCP server.");
    }
  };

  const handleToggleMCPServer = async (name) => {
    try {
      await toggleMCPServer(name);
      await loadData();
    } catch (err) {
      alert(err.message || "Failed to toggle MCP server");
    }
  };

  const handleDeleteMCPServer = async (name) => {
    if (!window.confirm(`Are you sure you want to delete MCP server '${name}'?`)) return;
    try {
      await deleteMCPServer(name);
      await loadData();
    } catch (err) {
      alert(err.message || "Failed to delete MCP server");
    }
  };


  useEffect(() => {
    loadData();
    const int = setInterval(loadData, 3000); // Polling for task updates
    const timer = setInterval(() => setTimeNow(Date.now()), 1000);
    return () => {
        clearInterval(int);
        clearInterval(timer);
    };
  }, []);

  const handleToolNameChange = (val) => {
    setNewToolName(val);
    const sanitized = val.replace(/[^a-zA-Z0-9_]/g, "");
    setNewToolCode(prev => {
      return prev.replace(/def \w+/, `def ${sanitized || "my_custom_tool"}`);
    });
  };

  const handleGenerateToolCode = async () => {
    if (!newToolName.trim()) {
      setNewToolError("Please provide a name for your tool before generating code.");
      return;
    }
    if (!newToolDesc.trim()) {
      setNewToolError("Please describe what the tool should do in the Capabilities/Description field before generating code.");
      return;
    }
    
    setGeneratingToolCode(true);
    setNewToolError("");
    setNewToolSuccess("");
    
    try {
      const result = await generateCustomTool(newToolName, newToolDesc);
      setNewToolCode(result.python_code);
      setNewToolSuccess("Code generated successfully by LLM! Make sure to review the code before creating the tool.");
    } catch (err) {
      setNewToolError(err.message || "Failed to generate code with LLM.");
    } finally {
      setGeneratingToolCode(false);
    }
  };

  const handleCreateCustomTool = async (e) => {
    e.preventDefault();
    setNewToolError("");
    setNewToolSuccess("");
    try {
      await createCustomTool({
        name: newToolName,
        description: newToolDesc,
        python_code: newToolCode
      });
      setNewToolSuccess(`Tool '${newToolName}' created successfully!`);
      setNewToolName("");
      setNewToolDesc("");
      setNewToolCode(
        `def my_custom_tool(param1: str) -> str:\n    \"\"\"\n    Description of the tool.\n    \"\"\"\n    # Your python code here\n    return f"Processed: {param1}"`
      );
      await loadData();
    } catch (err) {
      setNewToolError(err.message || "Failed to create tool");
    }
  };

  const handleDeleteCustomTool = async (toolId) => {
    if (!window.confirm("Are you sure you want to delete this custom tool?")) return;
    try {
      await deleteCustomTool(toolId);
      await loadData();
    } catch (err) {
      alert(err.message || "Failed to delete tool");
    }
  };

  const handleCreateAgent = async (e) => {
    e.preventDefault();
    if (!newAgentName || !newAgentModel) return;
    const activeTools = Object.keys(selectedTools).filter(k => selectedTools[k]);
    await createAgent({ name: newAgentName, persona: newAgentPersona, model_name: newAgentModel, tools: activeTools });
    setNewAgentName("");
    setNewAgentPersona("");
    setSelectedTools({});
    loadData();
  };
  
  const handleToolCheck = (toolName) => {
      setSelectedTools(prev => ({...prev, [toolName]: !prev[toolName]}));
  };

  const handleToggleAgent = async (agentId) => {
      await toggleAgent(agentId);
      loadData();
  };

  const handleDeleteAgent = async (agentId) => {
      if (window.confirm("Are you sure you want to delete this agent? This action cannot be undone.")) {
          await deleteAgent(agentId);
          loadData();
      }
  };

  const handleEditClick = (agent) => {
      setEditingAgentId(agent.id);
      setEditName(agent.name);
      setEditPersona(agent.persona);
      setEditModel(agent.model_name || "");
      const toolsObj = {};
      agent.tools.forEach(t => toolsObj[t] = true);
      setEditTools(toolsObj);
  };
  
  const handleEditToolCheck = (toolName) => {
      setEditTools(prev => ({...prev, [toolName]: !prev[toolName]}));
  };

  const handleCancelEdit = () => {
      setEditingAgentId(null);
  };



  const handleTaskEditClick = (task) => {
    setEditingTaskId(task.id);
    setEditTaskDesc(task.description);
    setEditTaskAgent(task.agent_id);
    setEditTaskTimeout(task.duration_limit?.toString() || "");
  };

  const handleSaveTaskEdit = async (taskId) => {
    await updateTask(taskId, {
      description: editTaskDesc,
      agent_id: editTaskAgent,
      duration_limit: editTaskTimeout ? parseInt(editTaskTimeout, 10) : null
    });
    setEditingTaskId(null);
    loadData();
  };

  const handleSaveEdit = async (agentId) => {
      const toolsList = Object.keys(editTools).filter(t => editTools[t]);
      await updateAgent(agentId, { 
          name: editName,
          persona: editPersona, 
          model_name: editModel,
          tools: toolsList 
      });
      setEditingAgentId(null);
      loadData();
  };

  const handleCreateTask = async (e) => {
    e.preventDefault();
    if (!newTaskDesc || !selectedAgentId) return;
    
    let desc = newTaskDesc;
    if (attachedFiles.length > 0) {
      desc += '\n\n' + attachedFiles.map(f => `[Attached file: ${f}]`).join('\n');
    }
    if (attachedDirs.length > 0) {
      desc += '\n\n' + attachedDirs.map(d => `[Attached directory: ${d}]`).join('\n');
    }
    const payload = { agent_id: selectedAgentId, description: desc };
    if (newTaskTimeout) payload.duration_limit = parseInt(newTaskTimeout, 10);
    
    await createTask(payload);
    setNewTaskDesc("");
    setNewTaskTimeout("60");
    setAttachedFiles([]);
    setFileInput("");
    setAttachedDirs([]);
    setDirInput("");
    loadData();
  };

  const handleSaveHost = async () => {
      try {
          await setOllamaHost(ollamaHostInput);
          const ms = await getModels();
          setModels(ms);
      } catch (e) {
          console.error("Error saving host", e);
      }
  };

  const handleReply = async (taskId) => {
      const answer = replyTexts[taskId];
      if (!answer) return;
      await replyToTask(taskId, answer);
      setReplyTexts(prev => ({...prev, [taskId]: ""}));
      loadData();
  };

  const openTaskModal = (task, memories, agentName) => {
    setModalTitle("Task Summary");
    
    const lastCompletion = [...memories].reverse().find(m => m.interaction_type === 'Completion');
    
    // Calculate timing
    const startTime = task.started_at ? new Date(task.started_at + "Z") : null;
    const lastMemory = memories.length > 0 ? new Date(memories[memories.length - 1].timestamp + "Z") : null;
    let duration = 0;
    if (startTime && lastMemory) {
        duration = Math.round((lastMemory - startTime) / 1000);
    }

    const formatTime = (date) => date ? date.toLocaleTimeString('fr-CA', { hour12: false }) : "--:--:--";
    
    setModalText({
      description: task.description,
      response: lastCompletion ? lastCompletion.content : "No completion response found.",
      agent: agentName || "Unknown",
      status: task.status,
      start: formatTime(startTime),
      end: formatTime(lastMemory),
      duration: duration,
      history: memories
    });
    setActiveModalTab("summary");
    setShowModal(true);
  };

  const statusClass = (status) => {
    const s = status.toLowerCase();
    if(s === 'running') return 'badge running';
    if(s === 'completed') return 'badge completed';
    if(s === 'stopped' || s === 'failed') return 'badge stopped';
    if(s === 'waiting') return 'badge waiting';
    return 'badge';
  };

  const memoryTypeColor = (type) => {
    switch(type) {
      case 'Action': return '#38bdf8';
      case 'Tool Call': return '#a78bfa';
      case 'Tool Result': return '#818cf8';
      case 'Completion': return '#10b981';
      case 'Error': return '#ef4444';
      case 'Question': return '#ffc832';
      case 'User Reply': return '#f59e0b';
      default: return '#94a3b8';
    }
  };

  const filteredMemory = memoryFilter === 'all' 
    ? allMemory 
    : allMemory.filter(m => m.agent_id === memoryFilter);

  return (
    <div className="dashboard-container">
      <header>
        <div style={{display: "flex", alignItems: "center", gap: "1rem"}}>
          <img src="/orc_full.png" alt="orc logo" style={{height: "150px", objectFit: "contain"}} />
          <div>
            <h1>orc</h1>
            <p>Agentic AI Orchestration Engine</p>
          </div>
        </div>
        <nav style={{marginTop: '1rem', display: 'flex', gap: '0.5rem'}}>
          <button 
            className={`btn btn-sm ${activeTab === 'dashboard' ? 'btn-primary' : ''}`} 
            onClick={() => setActiveTab('dashboard')}
          >Dashboard</button>
          <button 
            className={`btn btn-sm ${activeTab === 'memory' ? 'btn-primary' : ''}`} 
            onClick={() => setActiveTab('memory')}
          >Memory <span className="badge" style={{marginLeft: '0.25rem', fontSize: '0.7rem'}}>{allMemory.length}</span></button>
          <button 
            className={`btn btn-sm ${activeTab === 'tools' ? 'btn-primary' : ''}`} 
            onClick={() => setActiveTab('tools')}
          >Tools <span className="badge" style={{marginLeft: '0.25rem', fontSize: '0.7rem'}}>{customTools.length}</span></button>
        </nav>
      </header>

      {activeTab === 'dashboard' && <div className="grid">
        {/* Agents Card */}
        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h2>
              Agents <span className="badge">{agents.length}</span>
            </h2>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.85rem" }}>
              <label>Ollama Core Node:</label>
              <input 
                  type="text" 
                  value={ollamaHostInput} 
                  onChange={e => setOllamaHostInput(e.target.value)} 
                  placeholder="http://localhost:11434"
                  style={{ padding: "0.3rem", borderRadius: "4px", border: "1px solid var(--border-color)", background: "rgba(0,0,0,0.3)", color: "white" }}
              />
              <button className="btn btn-sm" onClick={handleSaveHost}>Save</button>
            </div>
          </div>
          
          <form onSubmit={handleCreateAgent} style={{marginBottom: "2rem"}}>
            <div className="form-group">
              <input 
                placeholder="Agent Name... (e.g. CodeBot)" 
                value={newAgentName} 
                onChange={(e) => setNewAgentName(e.target.value)} 
              />
            </div>
            <div className="form-group">
              <select 
                value={newAgentModel} 
                onChange={(e) => setNewAgentModel(e.target.value)}
                style={{width: "100%", padding: "0.75rem", marginBottom: "1rem", background: "rgba(0,0,0,0.3)", color: "white", border: "1px solid var(--border-color)", borderRadius: "8px"}}
              >
                <option value="" disabled>Select model</option>
                {models.map(m => <option key={m} value={m}>{m}</option>)}
                {newAgentModel && !models.includes(newAgentModel) && (
                  <option value={newAgentModel}>{newAgentModel} (Not installed)</option>
                )}
              </select>
            </div>
            <div className="form-group">
              <textarea 
                placeholder="Persona/Instructions..." 
                value={newAgentPersona} 
                onChange={(e) => setNewAgentPersona(e.target.value)} 
              />
            </div>
            {availableTools.length > 0 && (
              <div className="form-group" style={{ marginBottom: "1rem" }}>
                <label style={{display:"block", marginBottom: "0.5rem", fontSize: "0.9rem", color: "var(--text-secondary)"}}>Authorized Tools:</label>
                {availableTools.map(t => (
                  <div key={t} style={{display: "inline-flex", alignItems: "center", marginRight: "1rem", fontSize: "0.9rem"}}>
                     <input type="checkbox" id={`tool-${t}`} checked={!!selectedTools[t]} onChange={() => handleToolCheck(t)} style={{marginRight: "0.5rem"}}/>
                     <label htmlFor={`tool-${t}`} style={{color: "var(--text-color)"}}>{t}</label>
                  </div>
                ))}
              </div>
            )}
            <button className="btn btn-primary" type="submit">Deploy Agent</button>
          </form>

          <ul className="item-list">
            {agents.map(a => (
              <li key={a.id} className="item-card">
                <div className="flex-row">
                  <strong>{a.name}</strong>
                  <span className={`badge ${!a.is_active ? 'stopped' : ''}`}>{a.is_active ? 'Online' : 'Offline'}</span>
                </div>
                
                {editingAgentId === a.id ? (
                  <div style={{marginTop: "1rem"}}>
                    <div className="form-group">
                      <input 
                        value={editName} 
                        onChange={(e) => setEditName(e.target.value)} 
                        placeholder="Agent Name"
                        style={{marginBottom: "0.5rem"}}
                      />
                    </div>
                    <div className="form-group">
                      <select 
                        value={editModel} 
                        onChange={(e) => setEditModel(e.target.value)}
                        style={{width: "100%", padding: "0.5rem", marginBottom: "0.5rem", background: "rgba(0,0,0,0.3)", color: "white", border: "1px solid var(--border-color)", borderRadius: "4px"}}
                      >
                        <option value="" disabled>Select model</option>
                        {models.map(m => <option key={m} value={m}>{m}</option>)}
                        {editModel && !models.includes(editModel) && (
                          <option value={editModel}>{editModel} (Not installed)</option>
                        )}
                      </select>
                    </div>
                    <div className="form-group">
                      <textarea 
                        value={editPersona} 
                        onChange={(e) => setEditPersona(e.target.value)} 
                        rows={4}
                      />
                    </div>
                    {availableTools.length > 0 && (
                      <div className="form-group" style={{ marginBottom: "1rem" }}>
                        <label style={{display:"block", marginBottom: "0.5rem", fontSize: "0.85rem", color: "var(--text-secondary)"}}>Authorized Tools:</label>
                        {availableTools.map(t => (
                          <div key={t} style={{display: "inline-flex", alignItems: "center", marginRight: "1rem", fontSize: "0.85rem"}}>
                             <input type="checkbox" id={`edit-tool-${a.id}-${t}`} checked={!!editTools[t]} onChange={() => handleEditToolCheck(t)} style={{marginRight: "0.5rem"}}/>
                             <label htmlFor={`edit-tool-${a.id}-${t}`} style={{color: "var(--text-color)"}}>{t}</label>
                          </div>
                        ))}
                      </div>
                    )}
                    <div className="actions" style={{display: "flex", gap: "0.5rem"}}>
                      <button className="btn btn-sm btn-primary" style={{flex: 1}} onClick={() => handleSaveEdit(a.id)}>Save</button>
                      <button className="btn btn-sm" style={{flex: 1, background: "rgba(255,255,255,0.1)"}} onClick={handleCancelEdit}>Cancel</button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div style={{fontSize: '0.75rem', color: 'var(--text-accent)', marginBottom: '0.3rem'}}>Model: {a.model_name}</div>
                    <div style={{fontSize: '0.85rem', color: 'var(--text-secondary)'}}>
                      {a.persona}
                    </div>
                    {a.tools && a.tools.length > 0 && (
                      <div style={{marginTop: "0.5rem"}}>
                        {a.tools.map(tool => (
                          <span key={tool} className="badge" style={{marginRight: "0.25rem", fontSize: "0.7rem", opacity: 0.8}}>{tool}</span>
                        ))}
                      </div>
                    )}
                    <div className="actions" style={{marginTop: "0.5rem", display: "flex", gap: "0.5rem"}}>
                        <button className={`btn btn-sm ${a.is_active ? 'btn-danger' : 'btn-primary'}`} style={{flex: 1}} onClick={() => handleToggleAgent(a.id)}>
                            {a.is_active ? 'Disable' : 'Enable'}
                        </button>
                        <button className="btn btn-sm" style={{flex: 1, backgroundColor: "#555"}} onClick={() => handleEditClick(a)}>
                            Edit
                        </button>
                        <button className="btn btn-sm btn-danger" style={{flex: 1}} onClick={() => handleDeleteAgent(a.id)}>
                            Delete
                        </button>
                    </div>
                  </>
                )}
              </li>
            ))}
            {agents.length === 0 && <p style={{color: 'var(--text-secondary)'}}>No agents deployed.</p>}
          </ul>
        </div>

        {/* Tasks Card */}
        <div className="card">
          <h2>
            Tasks <span className="badge">{tasks.length}</span>
          </h2>
          
          <form onSubmit={handleCreateTask} style={{marginBottom: "2rem"}}>
             <div className="form-group">
              <select 
                value={selectedAgentId} 
                onChange={(e) => setSelectedAgentId(e.target.value)}
                style={{width: "100%", padding: "0.75rem", marginBottom: "1rem", background: "rgba(0,0,0,0.3)", color: "white", border: "1px solid var(--border-color)", borderRadius: "8px"}}
              >
                <option value="" disabled>Select agent</option>
                {agents.filter(a => a.is_active).map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
              </select>
            </div>
            <div className="form-group">
              <textarea 
                placeholder="Task description... (Shift+Enter for new line)" 
                value={newTaskDesc} 
                onChange={(e) => setNewTaskDesc(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); e.target.form.requestSubmit(); } }}
                rows={2}
                style={{minHeight: "50px", resize: "vertical"}}
              />
            </div>
            <div className="form-group">
              <input 
                type="number"
                placeholder="Duration limit in seconds (empty = no limit)" 
                value={newTaskTimeout} 
                onChange={(e) => setNewTaskTimeout(e.target.value)} 
              />
            </div>
            <div className="form-group">
              <div style={{display: "flex", gap: "0.5rem"}}>
                <input 
                  placeholder="File path to attach (e.g. ./output/report.md)" 
                  value={fileInput} 
                  onChange={(e) => setFileInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); if (fileInput.trim()) { setAttachedFiles(prev => [...prev, fileInput.trim()]); setFileInput(''); } } }}
                  style={{flex: 1}}
                />
                <button type="button" className="btn btn-sm" onClick={() => { if (fileInput.trim()) { setAttachedFiles(prev => [...prev, fileInput.trim()]); setFileInput(''); } }}>+ File</button>
              </div>
              {attachedFiles.length > 0 && (
                <div style={{display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginTop: '0.5rem'}}>
                  {attachedFiles.map((f, i) => (
                    <span key={i} style={{fontSize: '0.75rem', padding: '0.2rem 0.6rem', background: 'rgba(56, 189, 248, 0.15)', color: 'var(--text-accent)', borderRadius: '6px', display: 'inline-flex', alignItems: 'center', gap: '0.3rem'}}>
                      📎 {f.split(/[/\\]/).pop()}
                      <span onClick={() => setAttachedFiles(prev => prev.filter((_, j) => j !== i))} style={{cursor: 'pointer', opacity: 0.6, fontSize: '0.9rem'}}>×</span>
                    </span>
                  ))}
                </div>
              )}
            </div>

            <div className="form-group">
              <div style={{display: "flex", gap: "0.5rem"}}>
                <input 
                  placeholder="Directory path to attach (e.g. ./output)" 
                  value={dirInput} 
                  onChange={(e) => setDirInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); if (dirInput.trim()) { setAttachedDirs(prev => [...prev, dirInput.trim()]); setDirInput(''); } } }}
                  style={{flex: 1}}
                />
                <button type="button" className="btn btn-sm" onClick={() => { if (dirInput.trim()) { setAttachedDirs(prev => [...prev, dirInput.trim()]); setDirInput(''); } }}>+ Dir</button>
              </div>
              {attachedDirs.length > 0 && (
                <div style={{display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginTop: '0.5rem'}}>
                  {attachedDirs.map((d, i) => (
                    <span key={i} style={{fontSize: '0.75rem', padding: '0.2rem 0.6rem', background: 'rgba(16, 185, 129, 0.15)', color: '#10b981', borderRadius: '6px', display: 'inline-flex', alignItems: 'center', gap: '0.3rem'}}>
                      📁 {d.split(/[/\\]/).filter(x => x).pop() || d}
                      <span onClick={() => setAttachedDirs(prev => prev.filter((_, j) => j !== i))} style={{cursor: 'pointer', opacity: 0.6, fontSize: '0.9rem'}}>×</span>
                    </span>
                  ))}
                </div>
              )}
            </div>
            <button className="btn btn-primary" type="submit">Assign Task</button>
          </form>

          <ul className="item-list">
            {tasks.map(t => {
              const agent = agents.find(a => a.id === t.agent_id);
              const memories = taskMemories[t.id] || [];
              let countdownText = "";
              if (t.status === "Running" && t.duration_limit && t.started_at) {
                const startMs = new Date(t.started_at + "Z").getTime();
                const elapsed = Math.floor((timeNow - startMs) / 1000);
                const remaining = Math.max(0, t.duration_limit - elapsed);
                countdownText = ` (${remaining}s remaining)`;
              }
              
              const attachedNames = [];
              for (const m of t.description.matchAll(/\[Attached file:\s*(.+?)\]/g)) {
                attachedNames.push(m[1].split(/[/\\]/).pop());
              }
              const attachedDirs = [];
              for (const m of t.description.matchAll(/\[Attached directory:\s*(.+?)\]/g)) {
                attachedDirs.push(m[1].split(/[/\\]/).filter(x => x).pop() || m[1]);
              }
              const descOnly = t.description
                .replace(/\n*\[Attached file:\s*.+?\]/g, '')
                .replace(/\n*\[Attached directory:\s*.+?\]/g, '')
                .trim();

              return (
                <li key={t.id} className="item-card">
                  <div className="flex-row">
                    <span className={statusClass(t.status)}>{t.status}{countdownText}</span>
                    <span style={{fontSize: '0.75rem', color: 'var(--text-secondary)'}}>Agent: {agent?.name || 'Unknown'}</span>
                  </div>
                  {editingTaskId === t.id ? (
                    <div style={{marginTop: "1rem", padding: "1rem", background: "rgba(0,0,0,0.2)", borderRadius: "8px", border: "1px solid var(--border-color)"}}>
                      <div className="form-group">
                        <select 
                          value={editTaskAgent} 
                          onChange={(e) => setEditTaskAgent(e.target.value)}
                          style={{width: "100%", padding: "0.5rem", marginBottom: "0.5rem", background: "rgba(0,0,0,0.3)", color: "white", border: "1px solid var(--border-color)", borderRadius: "4px"}}
                        >
                          {agents.filter(a => a.is_active).map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
                        </select>
                      </div>
                      <div className="form-group">
                        <textarea 
                          value={editTaskDesc} 
                          onChange={(e) => setEditTaskDesc(e.target.value)} 
                          rows={3}
                          style={{marginBottom: "0.5rem"}}
                        />
                      </div>
                      <div className="form-group">
                        <input 
                          type="number"
                          placeholder="Timeout (s)" 
                          value={editTaskTimeout} 
                          onChange={(e) => setEditTaskTimeout(e.target.value)} 
                          style={{marginBottom: "0.5rem"}}
                        />
                      </div>
                      <div className="actions" style={{marginTop: "0.5rem"}}>
                        <button className="btn btn-sm btn-primary" onClick={() => handleSaveTaskEdit(t.id)}>Save</button>
                        <button className="btn btn-sm" onClick={() => setEditingTaskId(null)}>Cancel</button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div style={{marginTop: "0.5rem", fontWeight: "600", wordBreak: "break-word"}}>{descOnly}</div>
                      
                      {(attachedNames.length > 0 || attachedDirs.length > 0) && (
                        <div style={{display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginTop: "0.4rem"}}>
                          {attachedNames.map((name, i) => (
                            <span key={i} style={{fontSize: "0.75rem", padding: "0.2rem 0.6rem", background: "rgba(56, 189, 248, 0.15)", color: "var(--text-accent)", borderRadius: "6px"}}>📎 {name}</span>
                          ))}
                          {attachedDirs.map((name, i) => (
                            <span key={i} style={{fontSize: "0.75rem", padding: "0.2rem 0.6rem", background: "rgba(16, 185, 129, 0.15)", color: "#10b981", borderRadius: "6px"}}>📁 {name}</span>
                          ))}
                        </div>
                      )}
                    </>
                  )}
                  
                  {memories.length > 0 && (
                      <div style={{marginTop: "1rem", padding: "1rem", background: "rgba(0,0,0,0.4)", borderRadius: "8px", fontSize: "0.9rem", maxHeight: "150px", overflowY: "auto"}}>
                          {memories.map((m, i) => (
                              <div key={i} style={{marginBottom: "0.5rem", borderBottom: i !== memories.length - 1 ? "1px solid rgba(255,255,255,0.05)" : "none", paddingBottom: "0.5rem"}}>
                                  <span style={{color: "var(--text-accent)", fontSize: "0.75rem", display: "block", marginBottom: "0.2rem"}}>{m.interaction_type}</span>
                                  <MemoizedMarkdown className="markdown-content mini" content={m.content} />
                              </div>
                          ))}
                      </div>
                  )}

                  <div className="actions">
                    {t.status === "Pending" && !editingTaskId && (
                      <>
                        <button className="btn btn-sm btn-primary" onClick={() => startTask(t.id)}>
                          Start
                        </button>
                        <button className="btn btn-sm" onClick={() => handleTaskEditClick(t)}>
                          Edit
                        </button>
                      </>
                    )}
                    {t.status === "Running" && (
                      <button className="btn btn-sm btn-danger" onClick={() => stopTask(t.id)}>
                        Stop
                      </button>
                    )}
                    {t.status === "Waiting" && (
                      <button className="btn btn-sm btn-danger" onClick={() => stopTask(t.id)}>
                        Stop
                      </button>
                    )}
                    {(t.status === "Completed" || t.status === "Failed" || t.status === "Stopped") && (
                      <button className="btn btn-sm" onClick={async (e) => {
                        const btn = e.currentTarget;
                        const originalText = btn.innerHTML;
                        btn.innerHTML = "⏳ Loading...";
                        btn.disabled = true;
                        try {
                          const fullMem = await getTaskMemory(t.id);
                          const sortedMem = [...fullMem].sort((a,b) => new Date(a.timestamp) - new Date(b.timestamp));
                          openTaskModal(t, sortedMem, agent?.name);
                        } catch(e) {
                          openTaskModal(t, memories, agent?.name);
                        } finally {
                          btn.innerHTML = originalText;
                          btn.disabled = false;
                        }
                      }}>
                        🔍 View Result
                      </button>
                    )}
                  </div>

                  {t.status === "Waiting" && (
                    <div style={{marginTop: "1rem", padding: "1rem", background: "rgba(255, 200, 50, 0.1)", border: "1px solid rgba(255, 200, 50, 0.3)", borderRadius: "8px"}}>
                      <div style={{fontSize: "0.85rem", color: "#ffc832", marginBottom: "0.5rem", fontWeight: "600"}}>🤚 The agent is waiting for your reply:</div>
                      <div style={{display: "flex", gap: "0.5rem", alignItems: "flex-end"}}>
                        <textarea
                          placeholder="Type your answer... (Shift+Enter for new line)"
                          value={replyTexts[t.id] || ""}
                          onChange={(e) => setReplyTexts(prev => ({...prev, [t.id]: e.target.value}))}
                          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleReply(t.id); } }}
                          rows={2}
                          style={{flex: 1, minHeight: "50px", resize: "vertical", marginBottom: 0}}
                        />
                        <button className="btn btn-sm btn-primary" onClick={() => handleReply(t.id)} style={{alignSelf: "flex-end"}}>Send</button>
                      </div>
                    </div>
                  )}
                </li>
              );
            })}
             {tasks.length === 0 && <p style={{color: 'var(--text-secondary)'}}>No tasks in queue.</p>}
          </ul>
        </div>
      </div>}

      {activeTab === 'memory' && (
        <div className="card" style={{marginTop: '0'}}>
          <h2>Memory Explorer <span className="badge">{filteredMemory.length} entries</span></h2>
          
          <div style={{marginBottom: '1.5rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap'}}>
            <button 
              className={`btn btn-sm ${memoryFilter === 'all' ? 'btn-primary' : ''}`}
              onClick={() => setMemoryFilter('all')}
            >All Agents</button>
            {agents.map(a => (
              <button 
                key={a.id}
                className={`btn btn-sm ${memoryFilter === a.id ? 'btn-primary' : ''}`}
                onClick={() => setMemoryFilter(a.id)}
              >{a.name}</button>
            ))}
          </div>

          <div style={{maxHeight: '70vh', overflowY: 'auto'}}>
            {filteredMemory.length === 0 && <p style={{color: 'var(--text-secondary)'}}>No memory entries.</p>}
            {filteredMemory.map((m, i) => {
              const agent = agents.find(a => a.id === m.agent_id);
              const ts = m.timestamp ? new Date(m.timestamp + 'Z').toLocaleString('fr-CA', {hour12: false}) : '';
              return (
                <div key={m.id || i} style={{
                  padding: '0.75rem',
                  borderBottom: '1px solid var(--border-color)',
                  display: 'flex',
                  gap: '1rem',
                  alignItems: 'flex-start'
                }}>
                  <div style={{minWidth: '140px', flexShrink: 0}}>
                    <span style={{fontSize: '0.7rem', color: 'var(--text-secondary)', display: 'block'}}>{ts}</span>
                    <span style={{fontSize: '0.8rem', fontWeight: 600, color: memoryTypeColor(m.interaction_type)}}>{m.interaction_type}</span>
                    {agent && <span style={{fontSize: '0.7rem', color: 'var(--text-secondary)', display: 'block', marginTop: '0.2rem'}}>{agent.name}</span>}
                  </div>
                  <MemoizedMarkdown className="markdown-content mini" style={{flex: 1}} content={m.content} />
                </div>
              );
            })}
          </div>
        </div>
      )}

      {activeTab === 'tools' && (
        <div style={{display: "flex", flexDirection: "column", gap: "1.5rem"}}>
          {/* Sub-tabs Selector */}
          <div style={{display: "flex", gap: "1rem", borderBottom: "1px solid var(--border-color)", paddingBottom: "1rem"}}>
            <button 
              type="button"
              className={`btn ${toolsSubTab === 'mcp' ? 'btn-primary' : ''}`}
              onClick={() => setToolsSubTab('mcp')}
              style={{
                background: toolsSubTab === 'mcp' ? 'var(--text-accent)' : 'rgba(255,255,255,0.05)', 
                color: toolsSubTab === 'mcp' ? '#0f172a' : 'var(--text-primary)', 
                fontWeight: "600",
                fontSize: "0.95rem",
                padding: "0.6rem 1.2rem",
                borderRadius: "8px",
                border: "1px solid var(--border-color)",
                cursor: "pointer"
              }}
            >
              🔌 Serveurs MCP (Model Context Protocol)
            </button>
            <button 
              type="button"
              className={`btn ${toolsSubTab === 'custom' ? 'btn-primary' : ''}`}
              onClick={() => setToolsSubTab('custom')}
              style={{
                background: toolsSubTab === 'custom' ? 'var(--text-accent)' : 'rgba(255,255,255,0.05)', 
                color: toolsSubTab === 'custom' ? '#0f172a' : 'var(--text-primary)', 
                fontWeight: "600",
                fontSize: "0.95rem",
                padding: "0.6rem 1.2rem",
                borderRadius: "8px",
                border: "1px solid var(--border-color)",
                cursor: "pointer"
              }}
            >
              🐍 Outils Python Personnalisés
            </button>
          </div>

          {/* MCP Servers Sub-tab */}
          {toolsSubTab === 'mcp' && (
            <div className="card" style={{marginTop: '0'}}>
              <h2>🔌 MCP Servers Manager (Model Context Protocol)</h2>
              <p style={{color: 'var(--text-secondary)', marginBottom: '1.5rem'}}>
                Configure external or local Model Context Protocol (MCP) servers (e.g. filesystem, sqlite, github, memory). Tools provided by active MCP servers are automatically exposed to agents under server alias (e.g. mcp_filesystem).
              </p>

              <div className="grid" style={{gridTemplateColumns: "1fr 1fr", gap: "2rem"}}>
                <div>
                  <h3>Add MCP Server</h3>
                  <form onSubmit={handleCreateMCPServer}>
                    <div className="form-group" style={{marginBottom: "1rem"}}>
                      <label style={{display: "block", marginBottom: "0.25rem", fontWeight: "600"}}>Server Alias / Name</label>
                      <input 
                        type="text"
                        placeholder="e.g. memory or github"
                        value={newMcpName}
                        onChange={(e) => setNewMcpName(e.target.value)}
                        required
                        style={{width: "100%", padding: "0.75rem", background: "rgba(0,0,0,0.3)", color: "white", border: "1px solid var(--border-color)", borderRadius: "8px"}}
                      />
                    </div>

                    <div className="form-group" style={{marginBottom: "1rem"}}>
                      <label style={{display: "block", marginBottom: "0.25rem", fontWeight: "600"}}>Command</label>
                      <input 
                        type="text"
                        placeholder="npx or uvx"
                        value={newMcpCommand}
                        onChange={(e) => setNewMcpCommand(e.target.value)}
                        required
                        style={{width: "100%", padding: "0.75rem", background: "rgba(0,0,0,0.3)", color: "white", border: "1px solid var(--border-color)", borderRadius: "8px"}}
                      />
                    </div>

                    <div className="form-group" style={{marginBottom: "1rem"}}>
                      <label style={{display: "block", marginBottom: "0.25rem", fontWeight: "600"}}>Arguments</label>
                      <input 
                        type="text"
                        placeholder="e.g. -y @modelcontextprotocol/server-memory"
                        value={newMcpArgs}
                        onChange={(e) => setNewMcpArgs(e.target.value)}
                        style={{width: "100%", padding: "0.75rem", background: "rgba(0,0,0,0.3)", color: "white", border: "1px solid var(--border-color)", borderRadius: "8px"}}
                      />
                    </div>

                    <div className="form-group" style={{marginBottom: "1.5rem"}}>
                      <label style={{display: "block", marginBottom: "0.25rem", fontWeight: "600"}}>Environment Variables (Optional)</label>
                      <textarea 
                        placeholder="e.g. GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxx or JSON format"
                        value={newMcpEnv}
                        onChange={(e) => setNewMcpEnv(e.target.value)}
                        rows={2}
                        style={{width: "100%", padding: "0.75rem", background: "rgba(0,0,0,0.3)", color: "white", border: "1px solid var(--border-color)", borderRadius: "8px"}}
                      />
                    </div>

                    {mcpError && (
                      <div style={{color: "#ef4444", background: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.3)", padding: "0.75rem", borderRadius: "6px", marginBottom: "1rem", fontSize: "0.85rem"}}>
                        ❌ {mcpError}
                      </div>
                    )}

                    {mcpSuccess && (
                      <div style={{color: "#10b981", background: "rgba(16, 185, 129, 0.1)", border: "1px solid rgba(16, 185, 129, 0.3)", padding: "0.75rem", borderRadius: "6px", marginBottom: "1rem", fontSize: "0.85rem"}}>
                        ✅ {mcpSuccess}
                      </div>
                    )}

                    <button type="submit" className="btn btn-primary">Add MCP Server</button>
                  </form>
                </div>

                <div>
                  <h3>Configured MCP Servers</h3>
                  <ul className="item-list" style={{maxHeight: "450px", overflowY: "auto"}}>
                    {Object.entries(mcpServers).map(([srvName, srvData]) => (
                      <li key={srvName} className="item-card" style={{border: "1px solid rgba(255,255,255,0.1)", background: "rgba(255,255,255,0.02)", marginBottom: "1rem", padding: "1rem", borderRadius: "8px"}}>
                        <div className="flex-row" style={{display: "flex", justifyContent: "space-between", alignItems: "center"}}>
                          <div style={{display: "flex", alignItems: "center", gap: "0.5rem"}}>
                            <strong style={{color: "var(--text-accent)", fontSize: "1.1rem"}}>🔌 mcp_{srvName}</strong>
                            <span className={`badge ${!srvData.enabled ? 'stopped' : 'completed'}`}>{srvData.enabled ? 'Enabled' : 'Disabled'}</span>
                          </div>
                          <div style={{display: "flex", gap: "0.5rem"}}>
                            <button className={`btn btn-sm ${srvData.enabled ? 'btn-danger' : 'btn-primary'}`} onClick={() => handleToggleMCPServer(srvName)}>
                              {srvData.enabled ? 'Disable' : 'Enable'}
                            </button>
                            <button className="btn btn-sm btn-danger" onClick={() => handleDeleteMCPServer(srvName)}>Delete</button>
                          </div>
                        </div>
                        <div style={{fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: "0.5rem", wordBreak: "break-all"}}>
                          Command: <code>{srvData.command} {Array.isArray(srvData.args) ? srvData.args.join(" ") : ""}</code>
                        </div>
                      </li>
                    ))}
                    {Object.keys(mcpServers).length === 0 && (
                      <p style={{color: "var(--text-secondary)", fontStyle: "italic"}}>No MCP servers configured.</p>
                    )}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Custom Tools Sub-tab */}
          {toolsSubTab === 'custom' && (
            <div className="card" style={{marginTop: '0'}}>
              <h2>Python Custom Tools</h2>
              <p style={{color: 'var(--text-secondary)', marginBottom: '1.5rem'}}>
                Create custom python tools that can be bound to any agent. The agent runner will load and execute the python scripts.
              </p>

              <div className="grid" style={{gridTemplateColumns: "1fr 1fr", gap: "2rem"}}>
                <div>
                  <h3>Create a Tool</h3>
                  <form onSubmit={handleCreateCustomTool}>
                    <div className="form-group" style={{marginBottom: "1rem"}}>
                      <label style={{display: "block", marginBottom: "0.25rem", fontWeight: "600"}}>Tool/Function Name</label>
                      <input 
                        type="text"
                        placeholder="e.g. get_stock_price"
                        value={newToolName}
                        onChange={(e) => handleToolNameChange(e.target.value)}
                        required
                        style={{width: "100%", padding: "0.75rem", background: "rgba(0,0,0,0.3)", color: "white", border: "1px solid var(--border-color)", borderRadius: "8px"}}
                      />
                      <small style={{color: "var(--text-secondary)", fontSize: "0.75rem", display: "block", marginTop: "0.25rem"}}>
                        Must be a valid Python identifier (alphanumeric and underscores, no spaces).
                      </small>
                    </div>

                    <div className="form-group" style={{marginBottom: "1rem"}}>
                      <label style={{display: "block", marginBottom: "0.25rem", fontWeight: "600"}}>Capabilities / Description</label>
                      <textarea 
                        placeholder="Describe what the tool does and its parameters. The LLM uses this description to decide when to call the tool."
                        value={newToolDesc}
                        onChange={(e) => setNewToolDesc(e.target.value)}
                        rows={3}
                        required
                        style={{width: "100%", padding: "0.75rem", background: "rgba(0,0,0,0.3)", color: "white", border: "1px solid var(--border-color)", borderRadius: "8px", resize: "vertical"}}
                      />
                    </div>

                    <div className="form-group" style={{marginBottom: "1.5rem"}}>
                      <div style={{display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem"}}>
                        <label style={{fontWeight: "600", margin: 0}}>Python Script</label>
                        <button 
                          type="button" 
                          onClick={handleGenerateToolCode} 
                          className="btn btn-sm" 
                          style={{background: "rgba(56, 189, 248, 0.1)", border: "1px solid rgba(56, 189, 248, 0.3)", color: "var(--text-accent)"}}
                          disabled={generatingToolCode}
                        >
                          {generatingToolCode ? "⏳ Generating..." : "✨ Ask LLM to generate"}
                        </button>
                      </div>
                      <textarea 
                        value={newToolCode}
                        onChange={(e) => setNewToolCode(e.target.value)}
                        rows={12}
                        style={{width: "100%", padding: "0.75rem", fontFamily: "monospace", fontSize: "0.85rem", background: "rgba(0,0,0,0.5)", color: "#10b981", border: "1px solid var(--border-color)", borderRadius: "8px", resize: "vertical"}}
                        required
                      />
                      <small style={{color: "var(--text-secondary)", fontSize: "0.75rem", display: "block", marginTop: "0.25rem"}}>
                        Define a single Python function matching the tool name above. Make sure it uses type hints!
                      </small>
                    </div>

                    {newToolError && (
                      <div style={{color: "#ef4444", background: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.3)", padding: "0.75rem", borderRadius: "6px", marginBottom: "1rem", whiteSpace: "pre-wrap", fontSize: "0.85rem"}}>
                        ❌ {newToolError}
                      </div>
                    )}

                    {newToolSuccess && (
                      <div style={{color: "#10b981", background: "rgba(16, 185, 129, 0.1)", border: "1px solid rgba(16, 185, 129, 0.3)", padding: "0.75rem", borderRadius: "6px", marginBottom: "1rem", fontSize: "0.85rem"}}>
                        ✅ {newToolSuccess}
                      </div>
                    )}

                    <button type="submit" className="btn btn-primary">Create Tool</button>
                  </form>
                </div>

                <div>
                  <h3>Deployed Custom Tools</h3>
                  <ul className="item-list" style={{maxHeight: "600px", overflowY: "auto"}}>
                    {customTools.map(ct => (
                      <li key={ct.id} className="item-card" style={{border: "1px solid rgba(255,255,255,0.1)", background: "rgba(255,255,255,0.02)", marginBottom: "1rem", padding: "1rem", borderRadius: "8px"}}>
                        <div className="flex-row" style={{display: "flex", justifyContent: "space-between", alignItems: "center"}}>
                          <strong style={{color: "var(--text-accent)", fontSize: "1.1rem"}}>🛠️ {ct.name}</strong>
                          <button className="btn btn-sm btn-danger" onClick={() => handleDeleteCustomTool(ct.id)}>Delete</button>
                        </div>
                        <p style={{fontSize: "0.85rem", margin: "0.5rem 0", color: "var(--text-secondary)"}}>
                          {ct.description}
                        </p>
                        <details style={{marginTop: "0.5rem"}}>
                          <summary style={{fontSize: "0.75rem", color: "var(--text-accent)", cursor: "pointer"}}>View python script</summary>
                          <pre style={{fontSize: "0.75rem", background: "rgba(0,0,0,0.3)", padding: "0.75rem", borderRadius: "4px", marginTop: "0.5rem", overflowX: "auto", border: "1px solid rgba(255,255,255,0.05)"}}>
                            <code>{ct.python_code}</code>
                          </pre>
                        </details>
                      </li>
                    ))}
                    {customTools.length === 0 && (
                      <p style={{color: "var(--text-secondary)", fontStyle: "italic"}}>No custom tools created yet.</p>
                    )}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      )}


      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header" style={{flexDirection: "column", alignItems: "flex-start", gap: "1rem"}}>
              <div style={{display: "flex", justifyContent: "space-between", width: "100%", alignItems: "center"}}>
                <h3>{modalTitle}</h3>
                <button className="close-btn" onClick={() => setShowModal(false)}>&times;</button>
              </div>
              <div style={{display: "flex", gap: "0.5rem"}}>
                <button className={`btn btn-sm ${activeModalTab === 'summary' ? 'btn-primary' : ''}`} onClick={() => setActiveModalTab('summary')}>Summary</button>
                <button className={`btn btn-sm ${activeModalTab === 'details' ? 'btn-primary' : ''}`} onClick={() => setActiveModalTab('details')}>Log Details</button>
              </div>
            </div>
            <div className="modal-body">
              {activeModalTab === 'summary' ? (
                <>
                  <div style={{display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1rem", marginBottom: "2rem", padding: "1rem", background: "rgba(255,255,255,0.03)", borderRadius: "12px", border: "1px solid var(--border-color)"}}>
                    <div>
                      <div style={{fontSize: "0.7rem", color: "var(--text-secondary)", textTransform: "uppercase"}}>Agent</div>
                      <div style={{fontWeight: "600", color: "var(--text-accent)"}}>{modalText.agent}</div>
                    </div>
                    <div>
                      <div style={{fontSize: "0.7rem", color: "var(--text-secondary)", textTransform: "uppercase"}}>Status</div>
                      <div style={{fontWeight: "600", color: modalText.status === 'Completed' ? 'var(--success-color)' : 'var(--danger-color)'}}>{modalText.status}</div>
                    </div>
                    <div>
                      <div style={{fontSize: "0.7rem", color: "var(--text-secondary)", textTransform: "uppercase"}}>Execution Time</div>
                      <div style={{fontWeight: "600"}}>
                        <span style={{fontSize: "0.85rem"}}>{modalText.start} ⮕ {modalText.end}</span>
                        <span style={{marginLeft: "0.5rem", color: "var(--text-secondary)"}}>({modalText.duration}s)</span>
                      </div>
                    </div>
                  </div>

                  <div style={{marginBottom: "2rem"}}>
                    <h4 style={{color: "var(--text-secondary)", fontSize: "0.8rem", textTransform: "uppercase", marginBottom: "0.5rem", letterSpacing: "0.1em"}}>Detailed Prompt</h4>
                    <MemoizedMarkdown 
                        className="markdown-content" 
                        style={{background: "rgba(0,0,0,0.2)", padding: "1rem", borderRadius: "8px", border: "1px solid var(--border-color)"}}
                        content={modalText.description}
                    />
                  </div>
                  <div>
                    <h4 style={{color: "var(--text-accent)", fontSize: "0.8rem", textTransform: "uppercase", marginBottom: "0.5rem", letterSpacing: "0.1em"}}>Agent Response</h4>
                    <MemoizedMarkdown 
                        className="markdown-content response" 
                        style={{background: "rgba(56, 189, 248, 0.05)", padding: "1.5rem", borderRadius: "8px", border: "1px solid rgba(56, 189, 248, 0.2)"}}
                        content={modalText.response}
                    />
                  </div>

                  {extractImages().length > 0 && (
                    <div style={{marginTop: "2rem"}}>
                      <h4 style={{color: "var(--text-accent)", fontSize: "0.8rem", textTransform: "uppercase", marginBottom: "0.5rem", letterSpacing: "0.1em"}}>Generated Graphics</h4>
                      <div style={{display: "flex", flexDirection: "column", gap: "1rem"}}>
                        {extractImages().map((imgSrc, idx) => {
                          const safeSrc = imgSrc.replace(/\\/g, '/');
                          const filename = safeSrc.split('/').pop();
                          return (
                            <div key={idx} style={{background: "rgba(255, 255, 255, 0.02)", border: "1px solid var(--border-color)", borderRadius: "8px", padding: "1rem", display: "flex", flexDirection: "column", alignItems: "center"}}>
                              <img 
                                src={`http://localhost:8000/${safeSrc}`} 
                                alt={filename} 
                                style={{maxWidth: "100%", maxHeight: "450px", borderRadius: "4px", border: "1px solid rgba(255,255,255,0.1)"}}
                                onError={(e) => {
                                  e.target.style.display = 'none';
                                }}
                              />
                              <div style={{fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "0.5rem"}}>
                                Saved to: <code>{safeSrc}</code>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div style={{display: "flex", flexDirection: "column", gap: "1rem"}}>
                  {modalText.history.map((m, i) => (
                    <div key={i} style={{padding: "1rem", background: "rgba(0,0,0,0.2)", border: "1px solid var(--border-color)", borderLeft: `4px solid ${memoryTypeColor(m.interaction_type)}`, borderRadius: "4px 8px 8px 4px"}}>
                       <div style={{display: "flex", justifyContent: "space-between", marginBottom: "0.5rem"}}>
                          <span style={{color: memoryTypeColor(m.interaction_type), fontWeight: "bold", fontSize: "0.8rem", textTransform: "uppercase"}}>{m.interaction_type}</span>
                          <span style={{fontSize: "0.7rem", color: "var(--text-secondary)"}}>{m.timestamp ? new Date(m.timestamp + 'Z').toLocaleTimeString('fr-CA', {hour12: false}) : ''}</span>
                       </div>
                       <MemoizedMarkdown className="markdown-content small" content={m.content} />
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="modal-footer" style={{display: "flex", justifyContent: "space-between", alignItems: "center"}}>
              <button className={`btn btn-sm ${copySuccess ? 'btn-success' : ''}`} onClick={handleCopy} style={{background: copySuccess ? 'var(--success-color)' : 'rgba(255,255,255,0.1)'}}>
                {copySuccess ? '✅ Copied!' : '📋 Copy Content'}
              </button>
              <button className="btn btn-primary" onClick={() => setShowModal(false)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
