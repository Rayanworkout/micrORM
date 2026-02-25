from dataclasses import dataclass
from typing import Optional

from microrm.models import BaseModel
from database import db


@dataclass
class User(BaseModel):
    name: str
    email: Optional[str] = None

    class Meta:
        database = db
