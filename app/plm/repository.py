"""PLM repository — all database queries go through this class."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Allow running from any working directory
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.plm.models import Part, Drawing
from app.plm.schemas import DrawingSchema, PartSchema, PartWithDrawing


class PLMRepository:
    """Thin read-only repository over the PLM SQLite database."""

    def __init__(self, db_path: str):
        engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Session = sessionmaker(bind=engine)
        self._session = Session()

    # ── public API ──────────────────────────────────────────────────────────

    def get_part(self, part_number: str) -> Optional[PartSchema]:
        """Return a part record by its part number, or None if not found."""
        row = (
            self._session.query(Part)
            .filter(Part.part_number == part_number)
            .first()
        )
        return PartSchema.model_validate(row) if row else None

    def get_drawing(self, part_number: str) -> Optional[DrawingSchema]:
        """Return the primary drawing for a part number, or None."""
        part = (
            self._session.query(Part)
            .filter(Part.part_number == part_number)
            .first()
        )
        if part is None:
            return None
        row = (
            self._session.query(Drawing)
            .filter(Drawing.part_number == part_number)
            .first()
        )
        return DrawingSchema.model_validate(row) if row else None

    def list_top_level_assemblies(self) -> List[PartSchema]:
        """Return all parts whose part_type is 'assembly'."""
        rows = (
            self._session.query(Part)
            .filter(Part.part_type == "assembly")
            .order_by(Part.part_number)
            .all()
        )
        return [PartSchema.model_validate(r) for r in rows]

    def get_part_with_drawing(self, part_number: str) -> Optional[PartWithDrawing]:
        """Convenience: return part + its drawing in one call."""
        part = self.get_part(part_number)
        if part is None:
            return None
        return PartWithDrawing(part=part, drawing=self.get_drawing(part_number))

    def list_all_parts(self) -> List[PartSchema]:
        """Return every part in the database."""
        rows = self._session.query(Part).order_by(Part.part_number).all()
        return [PartSchema.model_validate(r) for r in rows]

    def list_all_drawings(self) -> List[DrawingSchema]:
        """Return every drawing record."""
        rows = self._session.query(Drawing).order_by(Drawing.drawing_id).all()
        return [DrawingSchema.model_validate(r) for r in rows]

    def close(self):
        self._session.close()
