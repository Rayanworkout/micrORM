from microrm import MicrORMDatabase
from .models import User

class MyDatabase(MicrORMDatabase):
    def __init__(self, db_name="db.sqlite3", db_path=None):
        super().__init__(db_name, db_path)

    def get_all_users(self, limit: int = None):
        users = User.all