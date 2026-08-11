"""Vercel serverless entry point.

Vercel's Python runtime looks for a WSGI callable named `app` in this module.
Everything else lives in the normal Flask app at the project root.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: E402  -- import must follow the sys.path fix
