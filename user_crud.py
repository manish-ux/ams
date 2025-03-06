import sqlite3

# user_crud.py
from security import hash_password, verify_password
from datetime import datetime

def create_user(first_name, last_name, email, plain_password, gender, role):
    connection_obj = sqlite3.connect("ams.db")
    cursor_obj = connection_obj.cursor()
    connection_obj = sqlite3.connect("ams.db")
    cursor_obj = connection_obj.cursor()
    hashed_pw = hash_password(plain_password)
    current_datetime = datetime.now()
    now = current_datetime.isoformat()

    # print("current datetime",now)
    cursor_obj.execute("""
    INSERT INTO user (first_name, last_name, email, password, gender, role, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (first_name, last_name, email, hashed_pw, gender, role, now, now)
    )
    connection_obj.commit()
    user_id = cursor_obj.lastrowid
    connection_obj.close()
    return user_id

def login(email, plain_password):
    connection_obj = sqlite3.connect("ams.db")
    cursor_obj = connection_obj.cursor()
    cursor_obj.execute("SELECT id, email, password, role FROM user WHERE email = ?", (email,))
    row = cursor_obj.fetchone()
    connection_obj.close()
    if not row:
        return None
    user_id, user_email, stored_hash, user_role = row
    if verify_password(stored_hash, plain_password):
        return {"id": user_id, "email": user_email, "role": user_role}
    else:
        return None                                                                                                                                                                                                  

def get_user_by_id(user_id):
    connection_obj = sqlite3.connect("ams.db")
    cursor_obj = connection_obj.cursor()
    cursor_obj.execute("SELECT id, first_name, last_name, email, role FROM user WHERE id = ?", (user_id,))
    row = cursor_obj.fetchone()
    connection_obj.close()
    return row
