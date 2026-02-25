from dataclasses import fields
from enum import Enum


class BaseModel:
    class DoesNotExist(LookupError):
        pass

    class MultipleObjectsReturned(LookupError):
        pass

    __table__: str
    __pk__: str | None = "id"
    __unique__: tuple[str, ...] | None = None
    _db = None  # inject your SQLiteDatabase/AttachmentsDatabase

    def _as_db_dict(self):
        out = {}
        for f in fields(self):
            v = getattr(self, f.name)
            out[f.name] = v.value if isinstance(v, Enum) else v
        if self.__pk__ and self.__pk__ not in out:
            out[self.__pk__] = getattr(self, self.__pk__, None)
        return out

    def save(self, update_fields: list[str] | None = None):
        data = self._as_db_dict()

        # PK style (Django-like)
        if self.__pk__ and data.get(self.__pk__) is not None:
            cols = update_fields or [c for c in data if c != self.__pk__]
            set_sql = ", ".join(f"{c}=?" for c in cols)
            params = tuple(data[c] for c in cols) + (data[self.__pk__],)
            q = f"UPDATE {self.__table__} SET {set_sql} WHERE {self.__pk__}=?"
            self._db.execute_query(q, params)
            return self

        # Unique tuple style (your FileToSend today)
        if self.__unique__:
            cols = list(data.keys())
            q = f"""
            INSERT INTO {self.__table__} ({", ".join(cols)})
            VALUES ({", ".join("?" for _ in cols)})
            ON CONFLICT({", ".join(self.__unique__)}) DO NOTHING
            """
            self._db.execute_query(q, tuple(data[c] for c in cols))
            return self

        # Plain insert
        cols = [c for c in data if c != self.__pk__]
        q = f"INSERT INTO {self.__table__} ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})"
        ok, _, last_id = self._db.execute_query(q, tuple(data[c] for c in cols))
        if ok and self.__pk__:
            setattr(self, self.__pk__, last_id)
        return self

    @classmethod
    def _build_model_instance_from_row(
        cls, row: tuple, select_columns: list[str], model_field_names: list[str]
    ):
        row_data = dict(zip(select_columns, row))
        instance = cls(**{name: row_data[name] for name in model_field_names})

        if cls.__pk__ and cls.__pk__ not in set(model_field_names):
            setattr(instance, cls.__pk__, row_data[cls.__pk__])

        return instance

    @classmethod
    def _query(cls, filters: dict[str, object], limit: int | None = None):
        """Run a SELECT on this model table and return matching model instances.

        Used internally by `filter()` and `get()` to avoid duplicating SQL
        construction and row-to-instance mapping logic.
        """
        if cls._db is None:
            raise RuntimeError("Model is not registered. Call db.register_model(YourModelClass) first.")

        model_field_names = [f.name for f in fields(cls)]
        model_field_name_set = set(model_field_names)

        valid_filter_fields = set(model_field_name_set)
        if cls.__pk__:
            valid_filter_fields.add(cls.__pk__)

        unknown_filters = [name for name in filters if name not in valid_filter_fields]
        if unknown_filters:
            raise ValueError(f"Unknown filter field(s): {', '.join(unknown_filters)}")

        select_columns = list(model_field_names)
        if cls.__pk__ and cls.__pk__ not in model_field_name_set:
            select_columns = [cls.__pk__, *select_columns]

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
    def get(cls, **filters):
        if not filters:
            raise ValueError("get() requires at least one keyword filter.")

        matches = cls._query(filters, limit=2)
        if not matches:
            raise cls.DoesNotExist(f"{cls.__name__} matching query does not exist.")
        if len(matches) > 1:
            raise cls.MultipleObjectsReturned(f"get() returned more than one {cls.__name__}.")
        return matches[0]
