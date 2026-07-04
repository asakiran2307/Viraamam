"""Vercel serverless entry point.

Vercel's Python runtime looks for an 'app' WSGI callable in this file.
We import the Flask app from the backend, then wrap it with WhiteNoise
so static files (CSS, JS, images) are served efficiently without a
separate CDN bucket or Nginx.
"""
import sys
import os

# ── Make backend package importable ──────────────────────────────────────────
# api/index.py → project root is one level up
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

# ── Import Flask app ──────────────────────────────────────────────────────────
from app import create_app  # noqa: E402

flask_app = create_app("production")

# ── WhiteNoise: serve /static/ files efficiently ──────────────────────────────
# This avoids needing Nginx or a separate CDN for static assets.
try:
    from whitenoise import WhiteNoise
    static_dir = os.path.join(ROOT_DIR, "frontend", "static")
    flask_app.wsgi_app = WhiteNoise(
        flask_app.wsgi_app,
        root=static_dir,
        prefix="static",
        max_age=31536000,         # 1 year browser cache for static assets
        add_headers_function=None,
    )
except ImportError:
    # WhiteNoise not installed — static files served by Flask (slower but works)
    pass

# ── Vercel expects the WSGI callable to be named 'app' ───────────────────────
app = flask_app
