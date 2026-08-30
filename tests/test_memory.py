import pytest
import uuid
from engine.memory_manager import MemoryManager

def test_memory_manager_crud():
    agent_id = uuid.uuid4()
    task_id = uuid.uuid4()

    # 1. Add memory
    mem1 = MemoryManager.add_memory(agent_id, task_id, "Action", "Test action memory")
    assert mem1.id is not None
    assert mem1.agent_id == agent_id
    assert mem1.task_id == task_id
    assert mem1.content == "Test action memory"

    mem2 = MemoryManager.add_memory(agent_id, task_id, "Observation", "Test observation memory")
    assert mem2.id is not None

    # 2. Get task memory
    task_memories = MemoryManager.get_task_memory(task_id)
    assert len(task_memories) == 2
    assert task_memories[0].content == "Test action memory"
    assert task_memories[1].content == "Test observation memory"

    # 3. Get agent memory
    agent_memories = MemoryManager.get_agent_memory(agent_id)
    assert len(agent_memories) == 2

    # 4. Erase agent memory
    erased = MemoryManager.erase_agent_memory(agent_id)
    assert erased is True

    # 5. Verify erased
    agent_memories_after = MemoryManager.get_agent_memory(agent_id)
    assert len(agent_memories_after) == 0
