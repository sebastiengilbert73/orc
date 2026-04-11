import asyncio
import time
from uuid import UUID
from sqlmodel import Session
from database.db import engine
from core.models import Agent, Task
from engine.llm_client import LLMClient
from engine.memory_manager import MemoryManager

from tools.registry import AVAILABLE_TOOLS, execute_tool

async def run_agent_loop(task_id: UUID, agent_id: UUID, stop_event: asyncio.Event, duration_limit: int = None):
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
        
        if "ask_user" in agent.tools:
            system_prompt += "\n\nIMPORTANT: When you need clarification or more information from the user, you MUST use the ask_user tool. Do NOT write questions as plain text responses. Always call ask_user(question='your question here') instead."
            
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
