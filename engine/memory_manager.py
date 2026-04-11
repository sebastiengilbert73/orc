from sqlmodel import Session, select
from core.models import Memory
from database.db import engine
from typing import List
from uuid import UUID

class MemoryManager:
    @staticmethod
    def add_memory(agent_id: UUID, task_id: UUID, interaction_type: str, content: str) -> Memory:
        with Session(engine) as session:
            memory = Memory(
                agent_id=agent_id,
                task_id=task_id,
                interaction_type=interaction_type,
                content=content
            )
            session.add(memory)
            session.commit()
            session.refresh(memory)
            return memory

    @staticmethod
    def get_agent_memory(agent_id: UUID) -> List[Memory]:
        with Session(engine) as session:
            statement = select(Memory).where(Memory.agent_id == agent_id).order_by(Memory.timestamp)
            results = session.exec(statement).all()
            return results

    @staticmethod
    def get_task_memory(task_id: UUID) -> List[Memory]:
        with Session(engine) as session:
            statement = select(Memory).where(Memory.task_id == task_id).order_by(Memory.timestamp)
            results = session.exec(statement).all()
            return results

    @staticmethod
    def erase_agent_memory(agent_id: UUID) -> bool:
        with Session(engine) as session:
            statement = select(Memory).where(Memory.agent_id == agent_id)
            results = session.exec(statement).all()
            for memory in results:
                session.delete(memory)
            session.commit()
            return True
