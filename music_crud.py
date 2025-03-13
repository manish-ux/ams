# music_crud.py
import sqlite3

# def list_songs_for_user(user_id):
#     """
#     Example: if the 'Music' table references 'Artist' which references 'User',
#     we need to join them so we only get music belonging to the user's artist record.
#     """
#     # This query depends on exact schema, but let's assume:
#     # user -> artist (user_id) -> music (artist_id)
#     connection_obj = sqlite3.connect("ams.db")
#     cursor_obj = connection_obj.cursor()
#     query = """
#         SELECT song.album_name, song.genre, artist.name
#         FROM song
#         JOIN artist ON artist.id = song.artist_id
#         WHERE artist.id = ?
#     """
#     cursor_obj.execute(query, (user_id,))
#     rows = cursor_obj.fetchall()
#     connection_obj.close()
#     return rows

# music_crud.py
from datetime import datetime

def create_song(artist_id, title, album_name, genre):
    connection_obj = sqlite3.connect("ams.db")
    cursor_obj = connection_obj.cursor()
    now = datetime.now()
    cursor_obj.execute("""
        INSERT INTO song (artist_id, title, album_name, genre, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?,?)
    """, (artist_id, title, album_name, genre, now, now))
    connection_obj.commit()
    music_id = cursor_obj.lastrowid
    connection_obj.close()
    return music_id

def get_song_by_id(music_id):
    connection_obj = sqlite3.connect("ams.db")
    cursor_obj = connection_obj.cursor()
    cursor_obj.execute("""
        SELECT id, artist_id, title, album_name, genre
        FROM song
        WHERE id = ?
    """, (music_id,))
    row = cursor_obj.fetchone()
    connection_obj.close()
    return row

def update_song(music_id, **kwargs):
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
    sql = f"UPDATE song SET {set_str} WHERE id = ?"
    values.append(music_id)
    cursor_obj.execute(sql, tuple(values))
    connection_obj.commit()
    connection_obj.close()

def delete_song(music_id):
    connection_obj = sqlite3.connect("ams.db")
    cursor_obj = connection_obj.cursor()
    cursor_obj.execute("DELETE FROM song WHERE id = ?", (music_id,))
    connection_obj.commit()
    connection_obj.close()

def list_songs_paginated(page=1, limit=10):
    offset = (page - 1) * limit
    connection_obj = sqlite3.connect("ams.db")
    cursor_obj = connection_obj.cursor()
    cursor_obj.execute("""
        SELECT m.id, m.artist_id, m.album_name, m.genre
        FROM song AS m
        ORDER BY m.id ASC
        LIMIT ? OFFSET ?
    """, (limit, offset))
    rows = cursor_obj.fetchall()
    connection_obj.close()
    return rows

def list_songs_for_user(user_id):
    """
    Return songs for the given user, by joining user->artist->music.
    """
    connection_obj = sqlite3.connect("ams.db")
    cursor_obj = connection_obj.cursor()
    query = """
        SELECT s.id, s.album_name, s.genre
        FROM song s
        JOIN artist a ON a.id = s.artist_id
        WHERE a.user_id = ?
    """
    cursor_obj.execute(query, (user_id,))
    rows = cursor_obj.fetchall()
    connection_obj.close()
    return rows
