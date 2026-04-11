import asyncio
from typing import Dict
from uuid import UUID
from sqlmodel import Session
from database.db import engine
from core.models import Task
from engine.agent_runner import run_agent_loop
from datetime import datetime

class TaskManager:
    def __init__(self):
        # Maps task UUID to its asyncio.Task
        self.running_tasks: Dict[UUID, asyncio.Task] = {}
        # Maps task UUID to a Cancellation Event
        self.stop_events: Dict[UUID, asyncio.Event] = {}

    def start_task(self, task_id: UUID, agent_id: UUID, duration_limit: int = None):
        """Starts a background asyncio task for the agent execution."""
        stop_event = asyncio.Event()
        self.stop_events[task_id] = stop_event
        
        # update DB status to running
        with Session(engine) as session:
            task = session.get(Task, task_id)
            if task:
                task.status = "Running"
                task.started_at = datetime.utcnow()
                session.add(task)
                session.commit()

        # create task
        coroutine = self._task_wrapper(task_id, agent_id, stop_event, duration_limit)
        task_ref = asyncio.create_task(coroutine)
        self.running_tasks[task_id] = task_ref

    async def _task_wrapper(self, task_id: UUID, agent_id: UUID, stop_event: asyncio.Event, duration_limit: int = None):
        try:
            if duration_limit:
                # Run with timeout
                await asyncio.wait_for(
                    run_agent_loop(task_id, agent_id, stop_event),
                    timeout=duration_limit
                )
            else:
                # Run indefinitely
                await run_agent_loop(task_id, agent_id, stop_event)
                
            self._update_task_status(task_id, "Completed")
            
        except asyncio.TimeoutError:
            self._update_task_status(task_id, "Stopped") # Stopped due to time
        except asyncio.CancelledError:
            self._update_task_status(task_id, "Stopped") 
        except Exception as e:
            print(f"Task {task_id} failed: {e}")
            self._update_task_status(task_id, "Failed")
        finally:
            self.running_tasks.pop(task_id, None)
            self.stop_events.pop(task_id, None)

    def stop_task(self, task_id: UUID):
        event = self.stop_events.get(task_id)
        if event:
            event.set() # Signals run_agent_loop to gracefully exit
            
        # Hard cancel just in case
        task = self.running_tasks.get(task_id)
        if task:
            task.cancel()

    def _update_task_status(self, task_id: UUID, status: str):
        with Session(engine) as session:
            task = session.get(Task, task_id)
            if task:
                task.status = status
                session.add(task)
                session.commit()

task_manager = TaskManager()
