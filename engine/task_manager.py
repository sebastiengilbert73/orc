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
        self.running_tasks: Dict[UUID, asyncio.Task] = {}
        self.stop_events: Dict[UUID, asyncio.Event] = {}
        self.pending_inputs: Dict[UUID, asyncio.Event] = {}
        self.input_data: Dict[UUID, str] = {}

    def start_task(self, task_id: UUID, agent_id: UUID, duration_limit: int = None):
        stop_event = asyncio.Event()
        self.stop_events[task_id] = stop_event
        
        with Session(engine) as session:
            task = session.get(Task, task_id)
            if task:
                task.status = "Running"
                task.started_at = datetime.utcnow()
                task.paused_at = None
                session.add(task)
                session.commit()

        coroutine = self._task_wrapper(task_id, agent_id, stop_event, duration_limit)
        task_ref = asyncio.create_task(coroutine)
        self.running_tasks[task_id] = task_ref

    async def request_user_input(self, task_id: UUID, question: str) -> str:
        with Session(engine) as session:
            task = session.get(Task, task_id)
            if task:
                task.status = "Waiting"
                task.paused_at = datetime.utcnow()
                session.add(task)
                session.commit()
                
        event = asyncio.Event()
        self.pending_inputs[task_id] = event
        await event.wait()
        
        answer = self.input_data.pop(task_id, "")
        
        with Session(engine) as session:
            task = session.get(Task, task_id)
            if task:
                task.status = "Running"
                if task.started_at and task.paused_at:
                    pause_duration = datetime.utcnow() - task.paused_at
                    task.started_at += pause_duration
                task.paused_at = None
                session.add(task)
                session.commit()
                
        return answer

    def provide_input(self, task_id: UUID, answer: str):
        if task_id in self.pending_inputs:
            self.input_data[task_id] = answer
            self.pending_inputs[task_id].set()
            del self.pending_inputs[task_id]

    async def _task_wrapper(self, task_id: UUID, agent_id: UUID, stop_event: asyncio.Event, duration_limit: int = None):
        try:
            await run_agent_loop(task_id, agent_id, stop_event, duration_limit)
            self._update_task_status(task_id, "Completed")
        except asyncio.TimeoutError:
            self._update_task_status(task_id, "Stopped")
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
            event.set()
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
