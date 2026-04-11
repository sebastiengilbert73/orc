import asyncio
from uuid import UUID
from sqlmodel import Session
from database.db import engine
from core.models import Agent, Task
from engine.llm_client import LLMClient
from engine.memory_manager import MemoryManager

from tools.registry import AVAILABLE_TOOLS, execute_tool

async def run_agent_loop(task_id: UUID, agent_id: UUID, stop_event: asyncio.Event):
    # fetch context
    with Session(engine) as session:
        agent = session.get(Agent, agent_id)
        task = session.get(Task, task_id)
        if not agent or not task:
            raise ValueError("Agent or Task not found")
            
        client = LLMClient(model_name=agent.model_name or "llama3.2")
        
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        system_prompt = f"You are {agent.name}. {agent.persona}\n\nThe current date and time is: {now}."
        if agent.specializations:
            system_prompt += f"\nYour specializations are: {', '.join(agent.specializations)}"
            
        task_desc = task.description

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Here is your task: {task_desc}"}
    ]
    
    while not stop_event.is_set():
        await asyncio.sleep(1) 
        
        MemoryManager.add_memory(
            agent_id=agent_id, 
            task_id=task_id, 
            interaction_type="Action", 
            content="Thinking..."
        )
        
        agent_tools = [t for t in AVAILABLE_TOOLS if t.__name__ in agent.tools]
        
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

        
        # for a continuous loop, normally it would wait for an observation.
        # for now, if it responded, we'll mark this iteration complete and just yield or wait.
        # This will spin and keep generating if not careful. Let's add an arbitrary stop condition.
        # Or wait longer. 
        await asyncio.sleep(5) 
