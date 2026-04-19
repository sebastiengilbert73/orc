import { useState, useEffect } from 'react';
import { getAgents, createAgent, getTasks, createTask, startTask, stopTask, getModels, getTaskMemory, toggleAgent, getTools, deleteAgent, updateAgent, replyToTask, getAllMemory, getOllamaHost, setOllamaHost } from './api';
import './index.css';

function App() {
  const [agents, setAgents] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [models, setModels] = useState([]);
  const [availableTools, setAvailableTools] = useState([]);
  const [taskMemories, setTaskMemories] = useState({});
  const [allMemory, setAllMemory] = useState([]);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [memoryFilter, setMemoryFilter] = useState('all');
  
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
      
      const memories = {};
      for (const task of t) {
          try {
              memories[task.id] = await getTaskMemory(task.id);
          } catch(e) {}
      }
      setTaskMemories(memories);

      const mem = await getAllMemory();
      setAllMemory(mem);
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
                    {(t.status === "Completed" || t.status === "Failed" || t.status === "Stopped") && (
                      <button className="btn btn-sm" onClick={() => openTaskModal(t, memories, agent?.name)}>
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
                  <div style={{fontSize: '0.85rem', whiteSpace: 'pre-wrap', wordBreak: 'break-word', flex: 1, lineHeight: 1.5}}>
                    {m.content}
                  </div>
                </div>
              );
            })}
          </div>
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
                    <div style={{color: "var(--text-primary)", background: "rgba(0,0,0,0.2)", padding: "1rem", borderRadius: "8px", border: "1px solid var(--border-color)"}}>
                      {modalText.description}
                    </div>
                  </div>
                  <div>
                    <h4 style={{color: "var(--text-accent)", fontSize: "0.8rem", textTransform: "uppercase", marginBottom: "0.5rem", letterSpacing: "0.1em"}}>Agent Response</h4>
                    <div style={{color: "var(--text-primary)", background: "rgba(56, 189, 248, 0.05)", padding: "1.5rem", borderRadius: "8px", border: "1px solid rgba(56, 189, 248, 0.2)", fontSize: "1.1rem", lineHeight: "1.6"}}>
                      {modalText.response}
                    </div>
                  </div>
                </>
              ) : (
                <div style={{display: "flex", flexDirection: "column", gap: "1rem"}}>
                  {modalText.history.map((m, i) => (
                    <div key={i} style={{padding: "1rem", background: "rgba(0,0,0,0.2)", border: "1px solid var(--border-color)", borderLeft: `4px solid ${memoryTypeColor(m.interaction_type)}`, borderRadius: "4px 8px 8px 4px"}}>
                       <div style={{display: "flex", justifyContent: "space-between", marginBottom: "0.5rem"}}>
                          <span style={{color: memoryTypeColor(m.interaction_type), fontWeight: "bold", fontSize: "0.8rem", textTransform: "uppercase"}}>{m.interaction_type}</span>
                          <span style={{fontSize: "0.7rem", color: "var(--text-secondary)"}}>{m.timestamp ? new Date(m.timestamp + 'Z').toLocaleTimeString('fr-CA', {hour12: false}) : ''}</span>
                       </div>
                       <div style={{fontSize: "0.9rem", whiteSpace: "pre-wrap", color: "var(--text-primary)"}}>{m.content}</div>
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
