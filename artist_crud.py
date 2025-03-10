import sqlite3
import csv
import io
# user_crud.py
from security import verify_password
from datetime import datetime

def create_artist(name, dob, address,gender,first_release_year,no_of_albums_released):
    connection_obj = sqlite3.connect("ams.db")
    cursor_obj = connection_obj.cursor()
    current_datetime = datetime.now()
    now = current_datetime.isoformat()

    # print("current datetime",now)
    cursor_obj.execute("""
    INSERT INTO artist (name, dob, gender, address, first_release_year, no_of_albums_released, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, dob, gender, address, first_release_year, no_of_albums_released, now, now)
    )
    connection_obj.commit()
    user_id = cursor_obj.lastrowid
    print(user_id,"user_id")
    connection_obj.close()
    return user_id

def update_artist(**kwargs):
    """
    Update fields in the artist record. For example:
      update_artist(3, name="NewName")
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
    sql_initial = "SELECT artist.id FROM artist JOIN user ON artist.name = (user.first_name || ' ' || user.last_name) WHERE user.role = 'Artist'"
    cursor_obj.execute(sql_initial)
    connection_obj.commit()
    artist_id = cursor_obj.fetchone()
    print("artist_id",artist_id)
    sql = f"UPDATE artist SET {set_str} WHERE id = ?"
    print(sql)
    values.append(artist_id)
    try:
        cursor_obj.execute(sql, tuple(values))
        connection_obj.commit()
    finally:
        connection_obj.close()

def delete_artist(artist_id):
    connection_obj = sqlite3.connect("ams.db")
    cursor_obj = connection_obj.cursor()
    try:
        cursor_obj.execute("DELETE FROM artist WHERE id = ?", (artist_id,))
        connection_obj.commit()
    finally:
        connection_obj.close()

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

def list_artists_paginated(page=1, limit=10):
    offset = (page - 1) * limit
    connection_obj = sqlite3.connect("ams.db")
    cursor_obj = connection_obj.cursor()
    cursor_obj.execute("""
        SELECT id, user_id, name, gender, first_release_year, no_of_albums_released
        FROM artist
        ORDER BY id ASC
        LIMIT ? OFFSET ?
    """, (limit, offset))
    rows = cursor_obj.fetchall()
    connection_obj.close()
    return rows

def list_songs_for_artist(artist_id):
    """
    Return all songs for a particular artist.
    We'll join with the music table in music_crud (or do it here).
    """
    connection_obj = sqlite3.connect("ams.db")
    cursor_obj = connection_obj.cursor()
    cursor_obj.execute("""
        SELECT m.id, m.album_name, m.genre
        FROM song AS m
        WHERE m.artist_id = ?
    """, (artist_id,))
    rows = cursor_obj.fetchall()
    connection_obj.close()
    return rows

def get_artist_by_id(artist_id):
    connection_obj = sqlite3.connect("ams.db")
    cursor_obj = connection_obj.cursor()
    cursor_obj.execute("""
        SELECT id, user_id, name, gender, first_release_year, no_of_albums_released
        FROM artist
        WHERE id = ?
    """, (artist_id,))
    row = cursor_obj.fetchone()
    connection_obj.close()
    return row

def get_user_by_id(user_id):
    connection_obj = sqlite3.connect("ams.db")
    cursor_obj = connection_obj.cursor()
    cursor_obj.execute("SELECT id, first_name, last_name, email, role FROM user WHERE id = ?", (user_id,))
    row = cursor_obj.fetchone()
    connection_obj.close()
    return row

# (Add to artist_crud.py)


def export_artists_csv():
    """
    Return a CSV string containing all artists.
    Each row: id, user_id, stage_name, gender, first_release_year, no_of_albums_released
    """
    output = io.StringIO()
    writer = csv.writer(output)
    # Write header
    writer.writerow(["id","user_id","name","gender","first_release_year","no_of_albums_released"])
    
    conn = sqlite3.connect("ams.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, user_id, name, gender, first_release_year, no_of_albums_released
        FROM artist
        ORDER BY id ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    
    for row in rows:
        writer.writerow(row)
    
    return output.getvalue()

def import_artists_csv(csv_content):
    """
    Parse CSV content and insert rows into the artist table.
    CSV columns: id, user_id, stage_name, gender, first_release_year, no_of_albums_released
    *Ignore 'id' from CSV if you want to autoincrement, or handle accordingly.
    """
    f = io.StringIO(csv_content)
    reader = csv.DictReader(f)
    conn = sqlite3.connect("ams.db")
    cursor = conn.cursor()
    now = datetime.now()
    
    for row in reader:
        # If you want to let 'id' autoincrement, skip row['id']
        user_id = row['user_id']
        name = row['name']
        gender = row['gender']
        first_release_year = row['first_release_year']
        no_of_albums = row['no_of_albums_released']
        cursor.execute("""
            INSERT INTO artist (user_id, name, gender, first_release_year, no_of_albums_released, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, name, gender, first_release_year, no_of_albums, now, now))
    
    conn.commit()
    conn.close()
