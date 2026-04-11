import { useState, useEffect } from 'react';
import { getAgents, createAgent, getTasks, createTask, startTask, stopTask, getModels, getTaskMemory, toggleAgent, getTools, deleteAgent, updateAgent, replyToTask } from './api';
import './index.css';

function App() {
  const [agents, setAgents] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [models, setModels] = useState([]);
  const [availableTools, setAvailableTools] = useState([]);
  const [taskMemories, setTaskMemories] = useState({});
  
  // Forms states
  const [newAgentName, setNewAgentName] = useState("");
  const [newAgentPersona, setNewAgentPersona] = useState("");
  const [newAgentModel, setNewAgentModel] = useState("");
  const [selectedTools, setSelectedTools] = useState({});
  
  // Edit states
  const [editingAgentId, setEditingAgentId] = useState(null);
  const [editPersona, setEditPersona] = useState("");
  const [editTools, setEditTools] = useState({});

  const [newTaskDesc, setNewTaskDesc] = useState("");
  const [selectedAgentId, setSelectedAgentId] = useState("");
  const [newTaskTimeout, setNewTaskTimeout] = useState("");
  const [timeNow, setTimeNow] = useState(Date.now());
  const [replyTexts, setReplyTexts] = useState({});

  const loadData = async () => {
    try {
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
      
      const memories = {};
      for (const task of t) {
          try {
              memories[task.id] = await getTaskMemory(task.id);
          } catch(e) {}
      }
      setTaskMemories(memories);
    } catch (e) {
      console.error(e);
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
      setEditPersona(agent.persona);
      const toolsObj = {};
      if (agent.tools) {
          agent.tools.forEach(t => toolsObj[t] = true);
      }
      setEditTools(toolsObj);
  };
  
  const handleEditToolCheck = (toolName) => {
      setEditTools(prev => ({...prev, [toolName]: !prev[toolName]}));
  };

  const handleCancelEdit = () => {
      setEditingAgentId(null);
  };

  const handleSaveEdit = async (agentId) => {
      const activeTools = Object.keys(editTools).filter(k => editTools[k]);
      await updateAgent(agentId, { persona: editPersona, tools: activeTools });
      setEditingAgentId(null);
      loadData();
  };

  const handleCreateTask = async (e) => {
    e.preventDefault();
    if (!newTaskDesc || !selectedAgentId) return;
    
    const payload = { agent_id: selectedAgentId, description: newTaskDesc };
    if (newTaskTimeout) payload.duration_limit = parseInt(newTaskTimeout, 10);
    
    await createTask(payload);
    setNewTaskDesc("");
    setNewTaskTimeout("");
    loadData();
  };

  const handleReply = async (taskId) => {
      const answer = replyTexts[taskId];
      if (!answer) return;
      await replyToTask(taskId, answer);
      setReplyTexts(prev => ({...prev, [taskId]: ""}));
      loadData();
  };

  const statusClass = (status) => {
    const s = status.toLowerCase();
    if(s === 'running') return 'badge running';
    if(s === 'completed') return 'badge completed';
    if(s === 'stopped' || s === 'failed') return 'badge stopped';
    if(s === 'waiting') return 'badge waiting';
    return 'badge';
  };

  return (
    <div className="dashboard-container">
      <header>
        <h1>orc</h1>
        <p>Agentic AI Orchestration Engine</p>
      </header>

      <div className="grid">
        {/* Agents Card */}
        <div className="card">
          <h2>
            Agents <span className="badge">{agents.length}</span>
          </h2>
          
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
              <input 
                placeholder="Task description..." 
                value={newTaskDesc} 
                onChange={(e) => setNewTaskDesc(e.target.value)} 
              />
            </div>
            <div className="form-group">
              <input 
                type="number"
                placeholder="Timeout in seconds (e.g. 60) [Optional]" 
                value={newTaskTimeout} 
                onChange={(e) => setNewTaskTimeout(e.target.value)} 
              />
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
              return (
                <li key={t.id} className="item-card">
                  <div className="flex-row">
                    <span className={statusClass(t.status)}>{t.status}{countdownText}</span>
                    <span style={{fontSize: '0.75rem', color: 'var(--text-secondary)'}}>Agent: {agent?.name || 'Unknown'}</span>
                  </div>
                  <div style={{marginTop: "0.5rem", fontWeight: "600"}}>{t.description}</div>
                  
                  {memories.length > 0 && (
                      <div style={{marginTop: "1rem", padding: "1rem", background: "rgba(0,0,0,0.4)", borderRadius: "8px", fontSize: "0.9rem", maxHeight: "150px", overflowY: "auto"}}>
                          {memories.map((m, i) => (
                              <div key={i} style={{marginBottom: "0.5rem", borderBottom: i !== memories.length - 1 ? "1px solid rgba(255,255,255,0.05)" : "none", paddingBottom: "0.5rem"}}>
                                  <span style={{color: "var(--text-accent)", fontSize: "0.75rem", display: "block", marginBottom: "0.2rem"}}>{m.interaction_type}</span>
                                  <span style={{whiteSpace: "pre-wrap"}}>{m.content}</span>
                              </div>
                          ))}
                      </div>
                  )}

                  <div className="actions">
                    {t.status === "Pending" && (
                      <button className="btn btn-sm btn-primary" onClick={() => startTask(t.id)}>
                        Start
                      </button>
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
                  </div>

                  {t.status === "Waiting" && (
                    <div style={{marginTop: "1rem", padding: "1rem", background: "rgba(255, 200, 50, 0.1)", border: "1px solid rgba(255, 200, 50, 0.3)", borderRadius: "8px"}}>
                      <div style={{fontSize: "0.85rem", color: "#ffc832", marginBottom: "0.5rem", fontWeight: "600"}}>🤚 The agent is waiting for your reply:</div>
                      <div style={{display: "flex", gap: "0.5rem"}}>
                        <input
                          placeholder="Type your answer..."
                          value={replyTexts[t.id] || ""}
                          onChange={(e) => setReplyTexts(prev => ({...prev, [t.id]: e.target.value}))}
                          onKeyDown={(e) => { if (e.key === 'Enter') handleReply(t.id); }}
                          style={{flex: 1}}
                        />
                        <button className="btn btn-sm btn-primary" onClick={() => handleReply(t.id)}>Send</button>
                      </div>
                    </div>
                  )}
                </li>
              );
            })}
             {tasks.length === 0 && <p style={{color: 'var(--text-secondary)'}}>No tasks in queue.</p>}
          </ul>
        </div>
      </div>
    </div>
  );
}

export default App;
