import pytest
import asyncio
from uuid import uuid4
from engine.task_manager import TaskManager

def test_task_manager_user_input():
    async def _run():
        tm = TaskManager()
        task_id = uuid4()
        
        async def simulate_user_input():
            await asyncio.sleep(0.05)
            tm.provide_input(task_id, "User answer response")

        user_task = asyncio.create_task(simulate_user_input())
        answer = await tm.request_user_input(task_id, "What is your preference?")
        await user_task

        assert answer == "User answer response"

    asyncio.run(_run())
