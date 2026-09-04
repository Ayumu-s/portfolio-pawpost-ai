"""Vercel entrypoint for the PawPost FastAPI portfolio demo."""

import os


# Template edits are disposable in the public Mock demo.  Keep the bundled
# repository read-only and use Vercel's temporary writable directory instead.
# Keep local imports on Windows unchanged so this entrypoint can be smoke-tested.
if os.getenv("VERCEL") == "1":
    os.environ.setdefault("PAWPOST_TEMPLATE_DB_PATH", "/tmp/pawpost-ai.db")

from app.main import app

__all__ = ["app"]
