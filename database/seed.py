from sqlmodel import Session, select
from database.db import engine
from core.models import Agent
import uuid

def seed_default_agents():
    with Session(engine) as session:
        # Check existing names to avoid duplicates
        statement = select(Agent)
        existing_names = {a.name for a in session.exec(statement).all()}

        default_agents = [
            Agent(
                name="Orion",
                persona="You are a professional researcher. Your goal is to gather accurate information from the web or provided files and summarize it clearly.",
                model_name="llama3.2",
                is_active=True,
                tools=["web_search", "read_url", "read_text", "read_pdf", "list_directory"]
            ),
            Agent(
                name="Logic",
                persona="You are a mathematical analyst. You excel at complex calculations and logical reasoning. Always double-check your math.",
                model_name="llama3.2",
                is_active=True,
                tools=["calculator"]
            ),
            Agent(
                name="Scribe",
                persona="You are a technical writer. You specialize in creating well-formatted reports, documentation, and summaries in Markdown or PDF.",
                model_name="llama3.2",
                is_active=True,
                tools=["write_to_md", "write_to_pdf", "read_text", "read_pdf", "list_directory"]
            ),
            Agent(
                name="Nova",
                persona="You are a versatile generalist assistant. You can handle a wide variety of tasks using all available tools at your disposal.",
                model_name="llama3.2",
                is_active=True,
                tools=["get_location", "get_weather", "web_search", "read_url", "list_directory", "read_text", "read_pdf", "calculator", "write_to_pdf", "write_to_md", "ask_user"]
            )
        ]

        for agent in default_agents:
            if agent.name not in existing_names:
                session.add(agent)
        
        session.commit()
        print("Default agents seeded successfully.")
