from microrm.models import BaseModel
from microrm import SQLiteDatabase
from dataclasses import dataclass
from typing import Optional


@dataclass
class User(BaseModel):
    name: str
    email: Optional[str] = None


db = SQLiteDatabase(db_name="examples.sqlite3")
user = User(name="Alice", email="alice@example.com")

db.register_model(User)
user.save()

print(db.fetch_all("SELECT id, name, email FROM user"))
