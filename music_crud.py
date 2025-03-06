# music_crud.py
import sqlite3

def list_songs_for_user(user_id):
    """
    Example: if the 'Music' table references 'Artist' which references 'User',
    we need to join them so we only get music belonging to the user's artist record.
    """
    # This query depends on exact schema, but let's assume:
    # user -> artist (user_id) -> music (artist_id)
    connection_obj = sqlite3.connect("ams.db")
    cursor_obj = connection_obj.cursor()
    query = """
        SELECT song.album_name, song.genre, artist.name
        FROM song
        JOIN artist ON artist.id = song.artist_id
        WHERE artist.id = ?
    """
    cursor_obj.execute(query, (user_id,))
    rows = cursor_obj.fetchall()
    connection_obj.close()
    return rows
