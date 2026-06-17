"""Smoke check for local frontend origins used by Vite dev and preview."""

from main import allowed_origins


for origin in (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
):
    assert origin in allowed_origins, f"missing local CORS origin: {origin}"

print("local CORS smoke test passed")
