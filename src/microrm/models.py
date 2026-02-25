from dataclasses import fields
from enum import Enum


class BaseModel:
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
