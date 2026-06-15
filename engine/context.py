import contextvars

current_task_id = contextvars.ContextVar("current_task_id", default=None)
current_agent_id = contextvars.ContextVar("current_agent_id", default=None)
