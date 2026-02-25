from dataclasses import dataclass
from typing import Optional

from microrm import SQLiteDatabase
from microrm.models import BaseModel


db = SQLiteDatabase(db_name="examples.sqlite3")


@dataclass
class User(BaseModel):
    name: str
    email: Optional[str] = None

    class Meta:
        database = db