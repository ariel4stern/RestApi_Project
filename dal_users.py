import sqlite3
from fastapi import HTTPException
from passlib.context import CryptContext
import hashlib
from db_functions import count_files,clear_folder
from dal_models import dm_recreate_table
from db_functions import read_db

DB_NAME_MODELS = "models.db"
DB_NAME_USERS = "users.db"
TABLE_MODELS = "models"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_connection(db_name) -> sqlite3.Connection:
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    return conn
def row_to_dict(row) -> dict|None:
    if row is None:
        return None
    return dict(row)

def hash_password(password: str) -> str:
    # Step 1: hash with SHA256 (no length limit)
    sha_password = hashlib.sha256(password.encode()).hexdigest()

    # Step 2: bcrypt the result
    return pwd_context.hash(sha_password)
def verify_password(plain_password:str, hashed_password:str)->bool:
    # First try bcrypt verification (for properly hashed passwords)
    sha_password = hashlib.sha256(plain_password.encode()).hexdigest()
    if pwd_context.verify(sha_password, hashed_password):
        return True

    # For backward compatibility, check if stored password is plain text
    # This is for existing accounts that were created before hashing was implemented
    if plain_password == hashed_password:
        return True

    return False

def du_create_table_users(db_name)->bool:
    query = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE ,       
        password TEXT NOT NULL,
        coins INTEGER NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """


    try:
        with get_connection(db_name) as conn:
            conn.execute(query)
            conn.commit()
            return True

    except sqlite3.OperationalError:
        raise HTTPException(status_code=500, detail="Database error")
def du_drop_table_users(db_name)->bool:
    query = """
    DROP TABLE IF EXISTS users
    """
    try:
        with get_connection(db_name) as conn:
            conn.execute(query)
            conn.commit()
            return True

    except sqlite3.OperationalError:
        raise HTTPException(status_code=500, detail="Database error")

def du_recreate_table_users(db_name)->bool:
    if count_files("models/saved_models")>0:
        clear_folder("models/saved_models")
    if read_db(TABLE_MODELS):
        dm_recreate_table(DB_NAME_MODELS)
    return du_drop_table_users(db_name) and du_create_table_users(db_name)

def du_get_all_users(db_name)->list[dict]|None:
    query = """
    SELECT id,user_name,email,coins,created_at FROM users
    ORDER BY id
    """
    with get_connection(db_name) as conn:
        rows = conn.execute(query).fetchall()
        return [row_to_dict(row) for row in rows]

def du_get_user_by_id(user_id: int, db_name) -> dict | None:
    query = """
    SELECT id,user_name,email,coins
    FROM users
    WHERE id = ?
    """
    with get_connection(db_name) as conn:
        row = conn.execute(query,(user_id,)).fetchone()
        return row_to_dict(row)
def du_get_user_by_user_name(user_name:str,db_name)->dict|None:
    query = """
    SELECT *
    FROM users
    WHERE user_name = ?
    """

    with get_connection(db_name) as conn:
        row = conn.execute(query ,(user_name,)).fetchone()
        return row_to_dict(row)
def du_get_user_by_user_name_public(user_name: str, db_name) -> dict | None:
    query = """
    SELECT id, user_name, email, coins, created_at
    FROM users WHERE user_name = ?
    """
    with get_connection(db_name) as conn:
        row = conn.execute(query, (user_name,)).fetchone()
        return row_to_dict(row)



def du_login_user(user_name: str, password: str, db_name) -> dict | None:
    user = du_get_user_by_user_name(user_name, db_name)
    if user is None:
        return None
    if verify_password(password, user['password']):
        # Return user data without password
        return {
            'id': user['id'],
            'user_name': user['user_name'],
            'email': user['email'],
            'coins': user['coins'],
            'created_at': user['created_at']
        }
    return None

def du_insert_user(user_name, email, password,db_name)->dict|None:
    c = 10
    query = """
    INSERT INTO users (user_name, email, password,coins)
    VALUES (?, ?, ?,?)
    """
    hashed_password = hash_password(password)

    try:
        with get_connection(db_name) as conn:
            cursor = conn.execute(query, (user_name, email, hashed_password,c))
            user_id = cursor.lastrowid
            conn.commit()
            return du_get_user_by_id(user_id,db_name)


    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="User already exists")


    except sqlite3.OperationalError:
        raise HTTPException(status_code=500, detail="Database error")
def du_update_user(user_id: int, user_name:str, email:str, password:str,db_name)->dict|None:
    updating_user = du_get_user_by_id(user_id,db_name)

    if updating_user is None:
        return None

    query = """
    UPDATE users 
    SET user_name = ?, email = ?, password = ?
    WHERE id = ?
    """

    hashed_password = hash_password(password)

    try:
        with get_connection(db_name) as conn:
            cursor = conn.execute(query, (user_name, email, hashed_password,user_id))
            if cursor.rowcount == 0:
                return None
            return du_get_user_by_id(user_id,db_name)

    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="user_name or email already exists")

    except sqlite3.OperationalError:
        raise HTTPException(status_code=500, detail="Database error")
def du_patch_user(user_id: int, user_name:str, email:str, password:str,db_name)->dict|None:
    user = du_get_user_by_id(user_id,db_name)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    query = """UPDATE users SET """
    values = []

    if user_name is not None:
        query += "user_name = ?, "
        values.append(user_name)

    if email is not None:
        query += "email = ?, "
        values.append(email)

    if password is not None:
        query += "password = ? "
        hashed_password = hash_password(password)
        values.append(hashed_password)

    if not values:
        return None

    query = query.rstrip(", ") + " WHERE id = ?"
    values.append(user_id)

    try:
        with get_connection(db_name) as conn:
            cursor = conn.execute(query, tuple(values))
            conn.commit()
            if cursor.rowcount == 0:
                return None
            return du_get_user_by_id(user_id,db_name)

    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="user_name or email already exists")

    except sqlite3.OperationalError:
        raise HTTPException(status_code=500, detail="Database error")
def du_delete_user(user_id: int,db_name) -> dict | None:
    existing_user = du_get_user_by_id(user_id,db_name)
    if existing_user is None:
        return None

    try:
        with get_connection(db_name) as conn:
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            return existing_user


    except sqlite3.OperationalError:
        raise HTTPException(status_code=500, detail="Database error")

def du_decrease_coins(user_name:str,db_name)->int|None:
    n_coins = du_coins_count(user_name,db_name)+10
    query = ("""UPDATE users SET coins = ? 
                WHERE user_name = ?""")
    try:
        with get_connection(db_name) as conn:
            cursor = conn.execute(query,(n_coins,user_name,))
            if cursor.rowcount == 0:
                return 0
            conn.commit()
            return n_coins

    except sqlite3.OperationalError:
        raise HTTPException(status_code=500, detail="Database error")
def du_coins_count(user_name:str,db_name)->int:
    query = """SELECT coins FROM users WHERE user_name = ?"""

    with get_connection(db_name) as conn:
        coins_row = conn.execute(query,(user_name,)).fetchone()
        return coins_row[0] if coins_row and coins_row[0] is not None else 0
def du_reset_coins(user_name:str,db_name)->None|dict:
    query = """UPDATE users SET coins = ?
                WHERE user_name = ?"""
    try:
        with get_connection(db_name) as conn:
            conn.execute(query,(0,user_name,))
            conn.commit()
            return du_get_user_by_user_name_public(user_name,db_name)

    except sqlite3.OperationalError:
        raise HTTPException(status_code=500, detail="Database error")
def du_reduce_coins(user_name:str,db_name)->dict|None:
    if du_coins_count(user_name,db_name) <= 0:
        return None

    n_coins = du_coins_count(user_name,db_name)-1
    query = """
    UPDATE users SET coins = ?
    WHERE user_name = ?
    """

    try:
        with get_connection(db_name) as conn:
            conn.execute(query,(n_coins,user_name,))
            conn.commit()
            return du_get_user_by_user_name_public(user_name,db_name)

    except sqlite3.OperationalError:
        raise HTTPException(status_code=500, detail="Database error")


