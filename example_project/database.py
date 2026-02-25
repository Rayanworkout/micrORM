from typing import Optional

from microrm import MicrORMDatabase


class MyDatabase(MicrORMDatabase):
    def __init__(self, db_name: str = "db.sqlite3", db_path: str = None):
        super().__init__(db_name, db_path)

    def get_all_users(self, limit: int = None):
        from models import User

        users = User.all()

        if users:
            if limit is None:
                return users

            return users[:limit]

    def create_user(
        self, name: str, email: Optional[str] = None, ignore_conflicts: bool = False
    ):
        from models import User

        return User(name=name, email=email).save(ignore_conflicts=ignore_conflicts)


# Shared database instance used by models and application code.
db = MyDatabase(db_name="hello_world.sqlite")
