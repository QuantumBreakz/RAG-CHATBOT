import os
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional


ANALYTICS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'log', 'analytics')
EVENTS_FILE = os.path.join(ANALYTICS_DIR, 'events.jsonl')


def _ensure_dir() -> None:
    os.makedirs(ANALYTICS_DIR, exist_ok=True)


def emit_event(
    *,
    event: str,
    session_id: Optional[str],
    provider: Optional[str],
    latency_ms: Optional[float],
    tokens: Optional[int],
    status: str,
    question: Optional[str] = None,
    docs: Optional[List[str]] = None,
    domains: Optional[List[str]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """Append a telemetry event to rolling JSONL file."""
    try:
        _ensure_dir()
        record = {
            'ts': datetime.utcnow().isoformat() + 'Z',
            'event': event,
            'session_id': session_id,
            'provider': provider,
            'latency_ms': latency_ms,
            'tokens': tokens,
            'status': status,
            'question': question,
            'docs': docs or [],
            'domains': domains or [],
        }
        if extra:
            record.update({'extra': extra})
        with open(EVENTS_FILE, 'a') as f:
            f.write(json.dumps(record) + '\n')
    except Exception:
        # Best-effort logging; never block request path
        pass


def read_events(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    _ensure_dir()
    if not os.path.exists(EVENTS_FILE):
        return []
    events: List[Dict[str, Any]] = []
    with open(EVENTS_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except Exception:
                continue
    if limit is not None and len(events) > limit:
        return events[-limit:]
    return events


