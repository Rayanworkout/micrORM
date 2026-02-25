from microrm.models import BaseModel
from microrm import SQLiteDatabase
from dataclasses import dataclass
from typing import Optional


@dataclass
class User(BaseModel):
    name: str
    email: Optional[str] = None


db = SQLiteDatabase(db_name="examples.sqlite3")