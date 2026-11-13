"""Shared database location for local and hosted execution."""
import os
from pathlib import Path

def database_path():
    path = Path(os.environ.get("BLUELINK_DB_PATH", str(Path(__file__).resolve().parent / "bluelink.sqlite3"))).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)
