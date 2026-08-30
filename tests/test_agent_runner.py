import pytest
from engine.agent_runner import prune_context_window, MAX_RECENT_MESSAGES, MAX_TOOL_RESULT_LENGTH

def test_prune_context_window_under_limit():
    # 2 header messages + 5 interaction messages = 7 total <= 12
    messages = [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "initial task"}
    ] + [{"role": "assistant", "content": f"msg {i}"} for i in range(5)]

    pruned = prune_context_window(messages)
    assert len(pruned) == 7
    assert pruned == messages

def test_prune_context_window_over_limit():
    # 2 header messages + 20 interaction messages = 22 total > 12
    header = [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "initial task"}
    ]
    old_messages = [{"role": "assistant", "content": f"old msg {i}"} for i in range(10)]
    recent_messages = [{"role": "assistant", "content": f"recent msg {i}"} for i in range(10)]

    full_messages = header + old_messages + recent_messages
    assert len(full_messages) == 22

    pruned = prune_context_window(full_messages)

    # Must preserve header (0 and 1) + last 10 messages = 12 messages total
    assert len(pruned) == 2 + MAX_RECENT_MESSAGES
    assert pruned[0]["content"] == "system prompt"
    assert pruned[1]["content"] == "initial task"
    assert pruned[2]["content"] == "recent msg 0"
    assert pruned[-1]["content"] == "recent msg 9"
