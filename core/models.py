from typing import List, Optional
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Column, JSON
from datetime import datetime

class Agent(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    persona: str
    model_name: Optional[str] = Field(default=None) # The LLM Model
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Store list of strings as JSON in the database
    specializations: List[str] = Field(default=[], sa_column=Column(JSON))
    tools: List[str] = Field(default=[], sa_column=Column(JSON))

class Task(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    agent_id: UUID = Field(foreign_key="agent.id")
    description: str
    status: str = Field(default="Pending") # Pending, Running, Completed, Failed, Stopped
    execution_mode: str = Field(default="Indefinite") # Time-boxed or Indefinite
    duration_limit: Optional[int] = Field(default=None) # Time in seconds
    started_at: Optional[datetime] = Field(default=None)
    paused_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Memory(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    agent_id: UUID = Field(foreign_key="agent.id")
    task_id: Optional[UUID] = Field(default=None, foreign_key="task.id")
    interaction_type: str # "Action", "Observation", "Error", "Completion"
    content: str # Details of action or thought
    timestamp: datetime = Field(default_factory=datetime.utcnow)
