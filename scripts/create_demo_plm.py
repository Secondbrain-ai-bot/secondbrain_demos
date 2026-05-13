"""create_demo_plm.py

Creates an empty PLM SQLite database with the required schema.
Run this once before seed_demo_plm.py.

Usage:
    python scripts/create_demo_plm.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine
from app.plm.models import Base


def create_database() -> Path:
    db_path = PROJECT_ROOT / "data" / "demo_plm.sqlite"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure drawing directories exist
    (PROJECT_ROOT / "data" / "drawings" / "pdf").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "data" / "drawings" / "png").mkdir(parents=True, exist_ok=True)

    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    engine.dispose()

    print(f"[OK] Database created : {db_path}")
    print("[OK] Tables created   : parts, drawings")
    print("[OK] Directories ready: data/drawings/pdf  data/drawings/png")
    return db_path


if __name__ == "__main__":
    create_database()
