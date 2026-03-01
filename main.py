from dataclasses import dataclass
from typing import Optional

from microrm import MicrORMDatabase
from microrm.models import BaseModel

db = MicrORMDatabase(db_name="example.sqlite3")


@dataclass
class User(BaseModel):
    name: str
    email: Optional[str] = None

    class Meta:
        database = db


u = User(name="rayan").save()