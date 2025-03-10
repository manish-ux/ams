import sqlite3

# user_crud.py
from security import hash_password, verify_password
from datetime import datetime

def create_user(first_name, last_name, email, plain_password, gender, role):
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

def update_user(user_id, **kwargs):
    """
    Update fields in the user record. For example:
      update_user(3, first_name="NewName", last_name="NewLast")
    """
    connection_obj = sqlite3.connect("ams.db")
    cursor_obj = connection_obj.cursor()
    set_clauses = []
    values = []
    for field, value in kwargs.items():
        set_clauses.append(f"{field} = ?")
        values.append(value)
    if not set_clauses:
        connection_obj.close()
        return
    set_clauses.append("updated_at = ?")
    now = datetime.now()
    values.append(now)
    set_str = ", ".join(set_clauses)
    sql = f"UPDATE user SET {set_str} WHERE id = ?"
    print(sql,user_id,type(user_id))
    values.append(user_id)
    try:
        cursor_obj.execute(sql, (values))
        connection_obj.commit()
    finally:
        connection_obj.close()

def delete_user(user_id):
    connection_obj = sqlite3.connect("ams.db")
    cursor_obj = connection_obj.cursor()
    try:
        cursor_obj.execute("DELETE FROM user WHERE id = ?", (user_id,))
        connection_obj.commit()
    finally:
        connection_obj.close()

def list_users_paginated(page=1, limit=10):
    """
    Return a paginated list of users.
    page: 1-based page index
    limit: how many records per page
    """
    offset = (page - 1) * limit
    connection_obj = sqlite3.connect('ams.db')
    cursor_obj = connection_obj.cursor()
    cursor_obj.execute("""
        SELECT id, first_name, last_name, email, role
        FROM user
        ORDER BY id ASC
        LIMIT ? OFFSET ?
    """, (limit, offset))
    rows = cursor_obj.fetchall()
    connection_obj.close()
    return rows


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

# def get_user_object_with_id(self,id):
#         connection_object = sqlite3.connect("ams.db")
#         cursor_obj = connection_object.cursor()
#         sql = """SELECT * from user where id = ?"""
#         cursor_obj.execute(sql,id)
#         row = cursor_obj.fetchone()
#         connection_object.close()
#         return row