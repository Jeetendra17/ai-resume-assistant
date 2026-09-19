"""LCEL building blocks: real LangChain when installed, the stdlib stand-in when not.

    INTERVIEW_CHAIN_ENGINE=auto       # default: langchain_core if importable
    INTERVIEW_CHAIN_ENGINE=stdlib     # force the stand-in

`ENGINE` names whichever was chosen, and every answer's trace reports it, so a
visitor can see which one actually produced their answer rather than trusting a
claim. langchain_core's runnables import in ~0.2 s, cheap enough to load eagerly.
"""

import os

_choice = os.environ.get("INTERVIEW_CHAIN_ENGINE", "auto").lower()

if _choice != "stdlib":
    try:
        from langchain_core.runnables import (  # noqa: F401
            RunnableLambda,
            RunnableParallel,
            RunnablePassthrough,
        )

        ENGINE = "langchain_core"
    except ImportError:
        _choice = "stdlib"

if _choice == "stdlib":
    from interview.compat.runnable import (  # noqa: F401
        RunnableLambda,
        RunnableParallel,
        RunnablePassthrough,
    )

    ENGINE = "stdlib"
