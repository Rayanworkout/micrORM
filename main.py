from microrm import SQLiteDatabase
from models import User


db = SQLiteDatabase(db_name="examples.sqlite3")
user = User(name="Alice", email="alice@example.com")

db.register_model(User)
user.save()
