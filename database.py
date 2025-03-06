import sqlite3


connection_obj = sqlite3.connect("ams.db")

def create_tables():

    cursor_obj = connection_obj.cursor()

    # create user table
    cursor_obj.execute("""
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password BLOB  NOT NULL,
        gender TEXT NOT NULL,
        address TEXT,
        role TEXT CHECK(role IN ('super_admin','artist_manager','artist')) NOT NULL,
        created_at TEXT,
        updated_at TEXT                      
    );
    """)

    # create Artist table
    cursor_obj.execute("""
    CREATE TABLE IF NOT EXISTS artist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        dob TEXT,
        gender TEXT NOT NULL,
        address TEXT,
        first_release_year INTEGER NOT NULL,
        no_of_albums_released INTEGER,
        created_at TEXT,
        updated_at TEXT                 
    );
    """)

    # create Song table
    cursor_obj.execute("""
    CREATE TABLE IF NOT EXISTS song (
        artist_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        album_name TEXT,
        genre TEXT,
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY(artist_id) REFERENCES artist(id)                         
    );
    """)

    connection_obj.commit()
    connection_obj.close()
    