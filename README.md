# micrORM
A tiny Python ORM with the minimal requirements to interact with a SQLite database using Python classes.

## Quick Start

```python
from dataclasses import dataclass
from typing import Optional

from microrm import SQLiteDatabase
from microrm.models import BaseModel

db = SQLiteDatabase(db_name="example.sqlite3")


@dataclass
class User(BaseModel):
    name: str
    email: Optional[str] = None

    class Meta:
        database = db
```

### Table Name Inference

By default, the table name is inferred from the model class name in lowercase.

- `User` -> `user`
- `BlogPost` -> `blogpost`

You can override it:

```python
@dataclass
class User(BaseModel):
    name: str

    class Meta:
        database = db
        table = "users"
        # or: __table__ = "users"
```

### When Tables Are Created

Tables are created lazily, on the first ORM operation on the model.

Examples of operations that trigger table creation:

- `instance.save()`
- `Model.get(...)`
- `Model.filter(...)`


## Basic Usage

```python
from dataclasses import dataclass
from typing import Optional

from microrm import SQLiteDatabase
from microrm.models import BaseModel

db = SQLiteDatabase(db_name="hello_world.sqlite")


@dataclass
class User(BaseModel):
    name: str
    email: Optional[str] = None

    class Meta:
        database = db


# ORM methods (core usage)
user = User(name="Alice", email="alice@example.com").save()
all_users = User.all()
filtered = User.filter(name="Alice")
found = User.get(id=user.id)
```

## Optional: Extend the Database Class

If you need app-specific helpers, subclass `MicrORMDatabase` and add your own methods.

```python
from typing import Optional

from microrm import MicrORMDatabase


class MyDatabase(MicrORMDatabase):
    def create_user(self, name: str, email: Optional[str] = None):
        from models import User
        return User(name=name, email=email).save()

    def get_all_users(self, limit: int | None = None):
        from models import User
        users = User.all()
        return users if limit is None else users[:limit]


db = MyDatabase(db_name="hello_world.sqlite")

# Use custom DB helpers
db.create_user(name="Bob", email="bob@example.com")
users = db.get_all_users(limit=10)
```

## Meta Directives

Model directives are declared in `Meta`:

- `database`: database instance to bind the model
- `pk`: primary key column name (default: `"id"`)
- `unique`: unique constraint column(s) (`str` or `tuple/list[str]`)

Example:

```python
@dataclass
class Account(BaseModel):
    email: str

    class Meta:
        database = db
        pk = "id"
        unique = "email"
```
