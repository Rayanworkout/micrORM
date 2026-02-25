from dataclasses import fields
from enum import Enum
from typing import Any


class BaseModel:
    class DoesNotExist(LookupError):
        pass

    class MultipleObjectsReturned(LookupError):
        pass

    __table__: str
    _db = None  # inject the MicrORMDatabase subclass instance
    __microrm_registered__ = False

    class Meta:
        database = None
        pk = "id"
        unique = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if "__pk__" in cls.__dict__ or "__unique__" in cls.__dict__:
            raise TypeError(
                "Use class Meta directives (`pk`, `unique`) instead of `__pk__` / `__unique__`."
            )

        meta = getattr(cls, "Meta", None)
        cls._db = getattr(meta, "database", None)
        cls.__microrm_registered__ = False

    @classmethod
    def _meta_pk(cls) -> str | None:
        pk = getattr(getattr(cls, "Meta", None), "pk", "id")
        if pk is not None and not isinstance(pk, str):
            raise TypeError("Meta.pk must be a string or None.")
        return pk

    @classmethod
    def _meta_unique(cls) -> tuple[str, ...]:
        unique = getattr(getattr(cls, "Meta", None), "unique", None)
        if unique is None:
            return ()
        if isinstance(unique, str):
            return (unique,)
        if isinstance(unique, (tuple, list)) and all(
            isinstance(c, str) for c in unique
        ):
            return tuple(unique)
        raise TypeError(
            "Meta.unique must be None, a string, or a tuple/list of strings."
        )

    @classmethod
    def _meta_database(cls):
        meta_db = getattr(getattr(cls, "Meta", None), "database", None)
        if meta_db is not None and meta_db is not cls._db:
            cls._db = meta_db
            cls.__microrm_registered__ = False
        return cls._db

    @classmethod
    def _ensure_registered(cls):
        db = cls._meta_database()
        if db is None:
            raise RuntimeError(
                "No database configured for this model. Set `class Meta: database = db`."
            )
        if not cls.__microrm_registered__:
            db._register_model(cls)
            cls.__microrm_registered__ = True

    def _as_db_dict(self):
        out = {}
        primary_key = self.__class__._meta_pk()
        for f in fields(self):
            v = getattr(self, f.name)
            out[f.name] = v.value if isinstance(v, Enum) else v
        if primary_key and primary_key not in out:
            out[primary_key] = getattr(self, primary_key, None)
        return out

    def save(self, update_fields: list[str] | None = None):
        self.__class__._ensure_registered()

        primary_key = self.__class__._meta_pk()
        unique_columns = self.__class__._meta_unique()
        data = self._as_db_dict()

        # PK style (Django-like)
        if primary_key and data.get(primary_key) is not None:
            cols = update_fields or [c for c in data if c != primary_key]
            set_sql = ", ".join(f"{c}=?" for c in cols)
            params = tuple(data[c] for c in cols) + (data[primary_key],)
            q = f"UPDATE {self.__table__} SET {set_sql} WHERE {primary_key}=?"
            self._db.execute_query(q, params)
            return self

        if unique_columns:
            cols = list(data.keys())
            q = f"""
            INSERT INTO {self.__table__} ({", ".join(cols)})
            VALUES ({", ".join("?" for _ in cols)})
            ON CONFLICT({", ".join(unique_columns)}) DO NOTHING
            """
            self._db.execute_query(q, tuple(data[c] for c in cols))
            return self

        # Plain insert
        cols = [c for c in data if c != primary_key]
        q = f"INSERT INTO {self.__table__} ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})"
        ok, _, last_id = self._db.execute_query(q, tuple(data[c] for c in cols))
        if ok and primary_key:
            setattr(self, primary_key, last_id)
        return self

    @classmethod
    def _build_model_instance_from_row(
        cls, row: tuple, select_columns: list[str], model_field_names: list[str]
    ):
        row_data = dict(zip(select_columns, row))
        instance = cls(**{name: row_data[name] for name in model_field_names})

        primary_key = cls._meta_pk()
        if primary_key and primary_key not in set(model_field_names):
            setattr(instance, primary_key, row_data[primary_key])

        return instance

    @classmethod
    def _query(cls, filters: dict[str, object], limit: int | None = None):
        """Run a SELECT on this model table and return matching model instances.

        Used internally by `filter()` and `get()` to avoid duplicating SQL
        construction and row-to-instance mapping logic.
        """
        cls._ensure_registered()
        primary_key = cls._meta_pk()

        model_field_names = [f.name for f in fields(cls)]
        model_field_name_set = set(model_field_names)

        valid_filter_fields = set(model_field_name_set)
        if primary_key:
            valid_filter_fields.add(primary_key)

        unknown_filters = [name for name in filters if name not in valid_filter_fields]
        if unknown_filters:
            raise ValueError(f"Unknown filter field(s): {', '.join(unknown_filters)}")

        select_columns = list(model_field_names)
        if primary_key and primary_key not in model_field_name_set:
            select_columns = [primary_key, *select_columns]

        where_sql = ""
        params = ()
        if filters:
            where_sql = " WHERE " + " AND ".join(f"{name}=?" for name in filters)
            params = tuple(filters.values())

        limit_sql = f" LIMIT {limit}" if limit is not None else ""
        query = f"SELECT {', '.join(select_columns)} FROM {cls.__table__}{where_sql}{limit_sql}"
        rows = cls._db.fetch_all(query, params if params else None)

        return [
            cls._build_model_instance_from_row(row, select_columns, model_field_names)
            for row in rows
        ]

    @classmethod
    def filter(cls, **filters):
        return cls._query(filters)

    @classmethod
    def all(cls):
        """Return all rows from this model table as model instances."""
        return cls._query({})

    @classmethod
    def get(
        cls, raise_if_not_found: bool = False, **filters
    ) -> Any | None | DoesNotExist:
        if not filters:
            raise ValueError("get() requires at least one keyword filter.")

        matches = cls._query(filters, limit=2)
        if not matches:
            if raise_if_not_found is True:
                raise cls.DoesNotExist(f"{cls.__name__} matching query does not exist.")
            else:
                return None

        if len(matches) > 1:
            raise cls.MultipleObjectsReturned(
                f"get() returned more than one {cls.__name__}."
            )
        return matches[0]
