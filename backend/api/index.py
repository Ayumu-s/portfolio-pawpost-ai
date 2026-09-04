"""Vercel entrypoint for the PawPost FastAPI portfolio demo."""

import os


# This file is the Vercel-only entrypoint. The Vercel Python runtime may not
# expose the `VERCEL` system variable during module import, so configure the
# disposable path unconditionally here. Local development starts app.main
# directly and therefore keeps using the repository's normal data directory.
os.environ.setdefault("PAWPOST_TEMPLATE_DB_PATH", "/tmp/pawpost-ai.db")

from app.main import app

__all__ = ["app"]
