import asyncio
import time
import json
from uuid import UUID
from datetime import datetime
from sqlmodel import Session, select
from database.db import engine
from core.models import Agent, Task
from engine.llm_client import LLMClient
from engine.memory_manager import MemoryManager
from tools.registry import AVAILABLE_TOOLS, execute_tool

def log_error(task_id: UUID, error: str):
    try:
        with open("error_log.txt", "a", encoding="utf-8") as f:
            f.write(f"[{task_id}] ERROR: {error}\n")
    except:
        pass

async def run_agent_loop(task_id: UUID, agent_id: UUID, stop_event: asyncio.Event, duration_limit: int = None):
    # Early logging to file
    log_error(task_id, "Attempting to start agent loop...")
    # Early logging
    MemoryManager.add_memory(
        agent_id=agent_id,
        task_id=task_id,
        interaction_type="Action",
        content="Starting agent loop..."
    )
    # fetch context
    with Session(engine) as session:
        agent = session.get(Agent, agent_id)
        task = session.get(Task, task_id)
        if not agent or not task:
            log_error(task_id, f"Agent {agent_id} or Task {task_id} not found in DB")
            raise ValueError("Agent or Task not found")
            
        client = LLMClient(model_name=agent.model_name or "llama3.2")
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        system_prompt = f"You are {agent.name}. {agent.persona}\n\nThe current date and time is: {now}."
        
        # Ensure specializations is a list and not empty
        specs = agent.specializations
        if isinstance(specs, str):
            import json
            try: specs = json.loads(specs)
            except: specs = []
        
        if specs and isinstance(specs, list):
            system_prompt += f"\nYour specializations are: {', '.join(specs)}"
        
        # Ensure tools is a list
        tools_list = agent.tools
        if isinstance(tools_list, str):
            import json
            try: tools_list = json.loads(tools_list)
            except: tools_list = []
        
        if tools_list and "ask_user" in tools_list:
            system_prompt += "\n\nIMPORTANT: When you need clarification or more information from the user, you MUST use the ask_user tool. Do NOT write questions as plain text responses. Always call ask_user(question='your question here') instead."
        
        if tools_list and "web_search" in tools_list and "read_url" in tools_list:
            system_prompt += "\n\nSTRATEGIC INSTRUCTION: When performing a news summary or factual research, snippets are never enough. You MUST use 'read_url' to consult AT LEAST 3 DIFFERENT SOURCES (different domains like .com, .ca, .org) to cross-reference information. Do not conclude your task until you have analyzed multiple perspectives from your search results."
        
        if tools_list and "search_agents" in tools_list:
            system_prompt += "\n\nSWARM MANAGER INSTRUCTION: Before asking the user for information that could be obtained via a tool (like current location, time, or file lists), you MUST first search if another agent in the swarm has a tool for it (e.g., search for 'location', 'time', or 'directory'). Prioritize automation over human interruption."
        
        if tools_list and "call_agent" in tools_list:
            # Fetch catalog of other active agents
            with Session(engine) as session:
                other_agents = session.exec(select(Agent).where(Agent.id != agent_id).where(Agent.is_active == True)).all()
                if other_agents:
                    catalog = "\n\nAVAILABLE COLLABORATORS IN THE SWARM:\n"
                    for oa in other_agents:
                        # Parse tools
                        oa_tools = oa.tools
                        if isinstance(oa_tools, str):
                            import json
                            try: oa_tools = json.loads(oa_tools)
                            except: oa_tools = []
                        catalog += f"- {oa.name}: {oa.persona}\n  Tools: {', '.join(oa_tools or [])}\n"
                    system_prompt += catalog
                    system_prompt += "\nUse 'call_agent' to delegate sub-tasks to these collaborators when their tools or personas match the needs of the task."
            
        task_desc = task.description

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Here is your task: {task_desc}"}
    ]
    
    # Track active running time (excludes paused time)
    active_start = time.monotonic()
    total_paused_seconds = 0.0
    
    while not stop_event.is_set():
        # Check timeout (excluding paused time)
        if duration_limit:
            elapsed_active = (time.monotonic() - active_start) - total_paused_seconds
            if elapsed_active >= duration_limit:
                raise asyncio.TimeoutError()
        
        await asyncio.sleep(1) 
        
        MemoryManager.add_memory(
            agent_id=agent_id, 
            task_id=task_id, 
            interaction_type="Action", 
            content="Thinking..."
        )
        
        agent_tools = [t for t in AVAILABLE_TOOLS if t.__name__ in tools_list]
        
        response = await client.generate_response(messages, tools=agent_tools if agent_tools else None)
        if not response:
            MemoryManager.add_memory(
                agent_id=agent_id, 
                task_id=task_id, 
                interaction_type="Error", 
                content="Failed to communicate with LLM."
            )
            break
            
        msg = response.get('message', {})
        
        if msg.get('tool_calls'):
            messages.append(msg) # Append the assistant's tool call request
            for tool_call in msg['tool_calls']:
                tool_name = tool_call['function']['name']
                tool_args = tool_call['function']['arguments']
                
                MemoryManager.add_memory(
                    agent_id=agent_id, 
                    task_id=task_id, 
                    interaction_type="Tool Call", 
                    content=f"Using tool '{tool_name}' with args {tool_args}"
                )
                
                # Special handling: ask_user pauses the task and waits for human input
                if tool_name == "ask_user":
                    question = tool_args.get("question", "")
                    
                    MemoryManager.add_memory(
                        agent_id=agent_id,
                        task_id=task_id,
                        interaction_type="Question",
                        content=question
                    )
                    
                    # Import here to avoid circular import
                    from engine.task_manager import task_manager
                    
                    pause_start = time.monotonic()
                    tool_result = await task_manager.request_user_input(task_id, question)
                    pause_end = time.monotonic()
                    total_paused_seconds += (pause_end - pause_start)
                    
                    MemoryManager.add_memory(
                        agent_id=agent_id,
                        task_id=task_id,
                        interaction_type="User Reply",
                        content=tool_result
                    )
                elif tool_name == "search_agents":
                    spec_query = tool_args.get("specialization", "").lower()
                    with Session(engine) as session:
                        all_agents = session.exec(select(Agent)).all()
                        found = []
                        for a in all_agents:
                            if a.id == agent_id: continue # Don't find self
                            
                            # Ensure tools is a list for searching
                            a_tools = a.tools
                            if isinstance(a_tools, str):
                                import json
                                try: a_tools = json.loads(a_tools)
                                except: a_tools = []
                            
                            specs = [s.lower() for s in (a.specializations or [])]
                            name_match = spec_query in a.name.lower()
                            spec_match = any(spec_query in s for s in specs)
                            tool_match = any(spec_query in t.lower() for t in (a_tools or []))
                            
                            if name_match or spec_match or tool_match:
                                tools_str = ", ".join(a_tools or [])
                                found.append(f"- Name: {a.name}\n  Persona: {a.persona}\n  Specializations: {', '.join(a.specializations or [])}\n  Tools: {tools_str}")
                        
                        if not found:
                            tool_result = f"No agents found with specialization '{spec_query}'."
                        else:
                            tool_result = "Found the following potential collaborators:\n" + "\n".join(found)
                
                elif tool_name == "call_agent":
                    target_name = tool_args.get("agent_name", "")
                    sub_task_desc = tool_args.get("task", "")
                    
                    with Session(engine) as session:
                        target_agent = session.exec(select(Agent).where(Agent.name == target_name)).first()
                        if not target_agent:
                            tool_result = f"Error: Agent '{target_name}' not found."
                        else:
                            # Create a sub-task in DB to track it
                            sub_task = Task(
                                agent_id=target_agent.id,
                                description=f"Sub-task from {agent.name}: {sub_task_desc}",
                                status="Running",
                                started_at=datetime.utcnow()
                            )
                            session.add(sub_task)
                            session.commit()
                            session.refresh(sub_task)
                            
                            MemoryManager.add_memory(
                                agent_id=agent_id,
                                task_id=task_id,
                                interaction_type="Collaboration",
                                content=f"Consulting {target_name} for task: {sub_task_desc}"
                            )
                            
                            # Run the sub-agent
                            sub_stop_event = asyncio.Event()
                            try:
                                # We run the loop directly. 
                                # Note: This might exceed recursion if agents keep calling each other, 
                                # but for a simple swarm it's fine.
                                await run_agent_loop(sub_task.id, target_agent.id, sub_stop_event)
                                
                                # Get the final response from memory
                                sub_memories = MemoryManager.get_task_memory(sub_task.id)
                                final_resp = "No response received."
                                for m in reversed(sub_memories):
                                    if m.interaction_type == "Completion":
                                        final_resp = m.content
                                        break
                                tool_result = f"Response from {target_name}: {final_resp}"
                                
                                # Mark sub-task as completed
                                sub_task.status = "Completed"
                                session.add(sub_task)
                                session.commit()
                                
                            except Exception as e:
                                tool_result = f"Communication with {target_name} failed: {e}"
                                sub_task.status = "Failed"
                                session.add(sub_task)
                                session.commit()

                else:
                    tool_result = execute_tool(tool_name, tool_args)
                
                    MemoryManager.add_memory(
                        agent_id=agent_id, 
                        task_id=task_id, 
                        interaction_type="Tool Result", 
                        content=str(tool_result)
                    )
                
                messages.append({
                    "role": "tool",
                    "content": str(tool_result),
                    "name": tool_name
                })
            
            # Re-prompt LLM with tool result immediately
            continue
            
        content = msg.get('content', '')
        if content:
            MemoryManager.add_memory(
                agent_id=agent_id, 
                task_id=task_id, 
                interaction_type="Completion", 
                content=f"LLM Response: {content}"
            )
            messages.append({"role": "assistant", "content": content})
            
            # Task is complete — the agent gave its final answer.
            # If it needed more info, it would have used ask_user.
            break
