# src/dashboard/models.py
from pydantic import BaseModel
from datetime import datetime
from typing import Any

class Trade(BaseModel):
    id: int
    timestamp: datetime
    data: Any

class Reflection(BaseModel):
    id: int | None = None
    timestamp: datetime
    data: Any
