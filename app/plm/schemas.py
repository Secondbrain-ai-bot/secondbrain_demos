"""Pydantic schemas for serialisation / validation of PLM records."""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class PartSchema(BaseModel):
    part_number: str
    part_name: str
    part_type: str
    revision: str
    lifecycle_state: str
    drawing_id: str

    model_config = {"from_attributes": True}


class DrawingSchema(BaseModel):
    drawing_id: str
    part_number: str
    drawing_number: str
    revision: str
    drawing_title: str
    file_path: str
    file_type: str
    sheet_count: int
    drawing_status: str

    model_config = {"from_attributes": True}


class PartWithDrawing(BaseModel):
    part: PartSchema
    drawing: Optional[DrawingSchema] = None
