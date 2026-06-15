from sqlmodel import create_engine, Session, SQLModel
from core.models import Agent, Task, Memory, CustomTool  # Ensure models are registered

sqlite_file_name = "orc.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

from sqlalchemy import event

engine = create_engine(
    sqlite_url, 
    echo=False, 
    connect_args={"check_same_thread": False}
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
