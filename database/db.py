from sqlmodel import create_engine, Session, SQLModel
from core.models import Agent, Task, Memory  # Ensure models are registered

sqlite_file_name = "orc.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
