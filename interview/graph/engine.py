"""StateGraph implementation: real LangGraph when installed, the stdlib stand-in when not.

    INTERVIEW_GRAPH_ENGINE=auto       # default: langgraph if importable
    INTERVIEW_GRAPH_ENGINE=stdlib     # force the stand-in

Loaded lazily, on the first question rather than at app start. Measured locally,
`import langgraph.graph` takes ~1.8 s against ~0.46 s for the entire Flask app, so
importing it eagerly would add that to every cold page load -- including visitors
who never ask anything. Deferred, only the first question on a cold instance pays.
"""

from __future__ import annotations

import os
import time
from functools import lru_cache


@lru_cache(maxsize=1)
def load():
    """Return (StateGraph, START, END, engine name, import milliseconds)."""
    started = time.perf_counter()
    if os.environ.get("INTERVIEW_GRAPH_ENGINE", "auto").lower() != "stdlib":
        try:
            from langgraph.graph import END, START, StateGraph

            return StateGraph, START, END, "langgraph", round((time.perf_counter() - started) * 1000)
        except ImportError:
            pass
    from interview.compat.stategraph import END, START, StateGraph

    return StateGraph, START, END, "stdlib", round((time.perf_counter() - started) * 1000)
