import inspect
import sqlite3
from dataclasses import fields, is_dataclass
from enum import Enum
from pathlib import Path
from types import NoneType, UnionType
from typing import Any, Tuple, get_args, get_origin


class SQLiteDatabase:
    def __init__(
        self, db_name: str = "db.sqlite3", db_path: str | Path | None = None
    ) -> None:
        resolved_db_path = self.__resolve_db_path(db_name=db_name, db_path=db_path)
        resolved_db_path.parent.mkdir(parents=True, exist_ok=True)

        self.db_path = str(resolved_db_path)
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.connection.execute("PRAGMA foreign_keys = ON")

    ############ GLOBALS ############
    def __close_connection(self):
        if self.connection:
            self.connection.close()

    ############ FILESYSTEM ############
    def __caller_script_dir(self) -> Path:
        current_file = Path(__file__).resolve()
        frame = inspect.currentframe()
        try:
            frame = frame.f_back
            while frame:
                filename = frame.f_code.co_filename
                if filename and filename != "<stdin>":
                    frame_path = Path(filename).resolve()
                    if frame_path != current_file:
                        return frame_path.parent
                frame = frame.f_back
        finally:
            del frame

        return Path.cwd()

    def __resolve_db_path(self, db_name: str, db_path: str | Path | None) -> Path:
        if db_path is None:
            return (self.__caller_script_dir() / db_name).resolve()

        base_path = Path(db_path).expanduser()
        raw_path = str(db_path)

        if (base_path.exists() and base_path.is_dir()) or raw_path.endswith(
            ("/", "\\")
        ):
            return (base_path / db_name).resolve()

        return base_path.resolve()

    ############ QUERIES ############
    def __execute_query(self, query, params=None) -> Tuple[bool, int, int]:
        cursor = self.connection.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.connection.commit()
            return True, cursor.rowcount, cursor.lastrowid
        except sqlite3.Error as e:
            print(f"An error occurred executing query: {e}")
            return False, cursor.rowcount, cursor.lastrowid

    ############ TABLES ############
    def __create_table(
        self, table_name: str, columns: list[str]
    ) -> Tuple[bool, int, int]:
        columns_sql = ", ".join(columns)
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_sql})"
        return self.__execute_query(query)

    def __sqlite_type_from_annotation(self, annotation: Any) -> str:
        origin = get_origin(annotation)
        if origin in (UnionType,):
            args = [arg for arg in get_args(annotation) if arg is not NoneType]
            if len(args) == 1:
                annotation = args[0]
        elif origin is not None and type(None) in get_args(annotation):
            args = [arg for arg in get_args(annotation) if arg is not type(None)]
            if len(args) == 1:
                annotation = args[0]

        if annotation in (int, bool):
            return "INTEGER"
        if annotation is float:
            return "REAL"
        if annotation is bytes:
            return "BLOB"
        if annotation is str:
            return "TEXT"
        if isinstance(annotation, type) and issubclass(annotation, Enum):
            return "TEXT"
        return "TEXT"

    def __create_tables_from_model_class(self, model_cls: type):
        # We infer the table name from the __table__ attribute if it exists, otherwise we use model name
        table_name = getattr(model_cls, "__table__", None) or model_cls.__name__.lower()
        model_cls.__table__ = table_name
        model_cls._db = self  # enable model methods to call database methods

        primary_key = getattr(
            model_cls, "__pk__", "id"
        )  # We use the __pk__ attribute if set
        unique_columns = tuple(getattr(model_cls, "__unique__", None) or ())

        model_fields = fields(model_cls)
        field_names = {f.name for f in model_fields}

        # If no __pk__ is mentionned, we use the implicit id field as pk
        has_implicit_id_pk = primary_key == "id" and primary_key not in field_names
        if primary_key and primary_key not in field_names and not has_implicit_id_pk:
            raise ValueError(f"Primary key '{primary_key}' is not a model field.")
        if unique_columns:
            missing_unique = [
                name
                for name in unique_columns
                if name not in field_names
                and not (has_implicit_id_pk and name == primary_key)
            ]
            if missing_unique:
                raise ValueError(
                    f"Unique columns not found on model: {', '.join(missing_unique)}"
                )

        column_defs: list[str] = []
        if has_implicit_id_pk:
            column_defs.append("id INTEGER PRIMARY KEY AUTOINCREMENT")

        for field in model_fields:
            col_name = field.name
            col_type = self.__sqlite_type_from_annotation(field.type)

            if primary_key and col_name == primary_key:
                if col_type == "INTEGER":
                    column_defs.append(f"{col_name} INTEGER PRIMARY KEY AUTOINCREMENT")
                else:
                    column_defs.append(f"{col_name} {col_type} PRIMARY KEY")
            else:
                column_defs.append(f"{col_name} {col_type}")

        if unique_columns:
            column_defs.append(f"UNIQUE ({', '.join(unique_columns)})")

        return self.__create_table(table_name, column_defs)

    ############ PUBLIC ############
    def close(self):
        self.__close_connection()

    def execute_query(self, query, params=None) -> Tuple[bool, int, int]:
        return self.__execute_query(query, params)

    def fetch_all(self, query, params=None):
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
            return []

    def fetch_one(self, query, params=None):
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
            return None

    def register_model(self, model_cls: type):
        if not isinstance(model_cls, type) or not is_dataclass(model_cls):
            raise TypeError(
                "The SQLiteDatabase.register_model() method expects a dataclass model class."
            )
        return self.__create_tables_from_model_class(model_cls)
