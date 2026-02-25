# micrORM
A tiny Python ORM with the minimal requirements to interact with a SQLite database using Python classes.

## Quick Start

```python
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

You do not need to call a manual `register_model()` in normal usage.

## Basic Usage

```python
# Insert
user = User(name="Alice", email="alice@example.com")
user.save()

# Get one row
found = User.get(id=user.id)
print(found)

# Filter rows
rows = User.filter(name="Alice")
print(rows)
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
