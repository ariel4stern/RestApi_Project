from fastapi import HTTPException
from db_functions import clear_folder,count_files,read_db,remove_model_from_dir
import sqlite3

DB_NAME_MODELS = "models.db"
DB_NAME_USERS = "users.db"

def get_connection(db_name) -> sqlite3.Connection:
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    return conn
def row_to_dict(row)->None|dict:
    if row is None:
        return None
    return dict(row)

def dm_create_table(db_name)->bool:
    if count_files(r"models\saved_models") > 0 and len(read_db("users")) == 0 :
        clear_folder(r"models\saved_models")

    query = """CREATE TABLE IF NOT EXISTS models(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )"""

    try:
        with get_connection(db_name) as conn:
            conn.execute(query)
            conn.commit()
            return True

    except sqlite3.OperationalError:
        raise HTTPException(status_code=500, detail="Database error")
def dm_drop_table(db_name)->bool:
    query = """
    DROP TABLE IF EXISTS models
    """

    try:
        with get_connection(db_name) as conn:
            conn.execute(query)
            conn.commit()
            return True

    except sqlite3.OperationalError:
        raise HTTPException(status_code=500, detail="Database error")

def dm_recreate_table(db_name)->bool:
    return dm_drop_table(db_name) and dm_create_table(db_name)

def dm_get_table(db_name) -> list[dict]|None:
    query = """SELECT *
                FROM models ORDER BY id DESC"""
    with get_connection(db_name) as conn:
        rows = conn.execute(query).fetchall()
        return [row_to_dict(row) for row in rows]
def dm_get_model_by_model_name(user_name:str,db_name)->dict|None:

    query = """
    SELECT *
    FROM models
    WHERE model_name = ?
    """

    with get_connection(db_name) as conn:
        row = conn.execute(query ,(user_name,)).fetchone()
        return row_to_dict(row)
def dm_get_model_by_id(model_id:int,db_name)->dict|None:
    query = """SELECT * FROM models
                WHERE id = ?"""
    with get_connection(db_name) as conn:
        row = conn.execute(query ,(model_id,)).fetchone()
        return row_to_dict(row)
def dm_change_model_name(old_model_name: str, new_model_name: str, db_name: str) -> dict | None:
    m = dm_get_model_by_model_name(old_model_name, db_name)

    if m is None:
        return None

    old_model_id = m["id"]
    query = """
    UPDATE models SET model_name = ?
    WHERE id = ?
    """

    try:
        with get_connection(db_name) as conn:
            cursor = conn.execute(query, (new_model_name, old_model_id))
            if cursor.rowcount == 0:
                return None
            conn.commit()

            return dm_get_model_by_id(old_model_id, db_name)

    except sqlite3.OperationalError:
        raise HTTPException(status_code=500, detail="Database error")

def dm_delete_model_by_model_name(user_name:str,db_name)->dict|None:
    existing_model = dm_get_model_by_model_name(user_name,db_name)
    if existing_model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    query = """DELETE FROM models WHERE model_name = ?"""
    try:
        with get_connection(db_name) as conn:
            conn.execute(query, (user_name,))
            conn.commit()
            remove_model_from_dir(user_name)
            return existing_model

    except sqlite3.OperationalError:
        raise HTTPException(status_code=500, detail="Database error")
def dm_insert_model(model_name:str,db_name)->dict|None:
    query = """
        INSERT INTO models (model_name)
        VALUES (?)
    """

    try:
        with get_connection(db_name) as conn:
            cursor = conn.execute(query, (model_name,))
            new_id = cursor.lastrowid
            conn.commit()
            return dm_get_model_by_id(new_id,db_name)

    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Model already exists,Delete your Current Model and train again")

    except sqlite3.OperationalError:
        raise HTTPException(status_code=500, detail="Database error")









