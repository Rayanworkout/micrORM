from dataclasses import dataclass
from typing import Optional

from microrm.models import BaseModel

@dataclass
class User(BaseModel):
    name: str
    email: Optional[str] = None
