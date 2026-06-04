import json
import sys
from datetime import UTC, datetime
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent.parent / "logs" / "claude_agent.jsonl"
MAX_LEN = 500


def _summarize(tool_input: object) -> object:
    if not isinstance(tool_input, dict):
        return str(tool_input)[:MAX_LEN]
    summary = {}
    for k, v in tool_input.items():
        if isinstance(v, str):
            summary[k] = v[:MAX_LEN] + f"… [truncated {len(v) - MAX_LEN} chars]" if len(v) > MAX_LEN else v
        elif isinstance(v, list):
            summary[k] = f"[list, {len(v)} items]"
        elif isinstance(v, (int, float, bool)) or v is None:
            summary[k] = v
        else:
            summary[k] = f"<{type(v).__name__}>"
    return summary


def main() -> None:
    raw = sys.stdin.read()
    if not raw.strip():
        return

    data = json.loads(raw)
    entry: dict = {
        "timestamp": datetime.now(UTC).isoformat(),
        "hook_event_name": data.get("hook_event_name", "Unknown"),
        "tool_name": data.get("tool_name", "Unknown"),
        "tool_input": _summarize(data.get("tool_input")),
    }

    if data.get("hook_event_name") == "PostToolUse":
        response = data.get("tool_response", "")
        s = str(response) if not isinstance(response, str) else response
        entry["tool_response"] = s[:MAX_LEN] + f"… [truncated]" if len(s) > MAX_LEN else s

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
