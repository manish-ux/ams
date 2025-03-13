import http.server
import socketserver
import urllib.parse
import random, sqlite3
import string
from security import hash_password
from database import create_tables      
from user_crud import (
    create_user, 
    login, get_user_by_id, list_users_paginated,
    update_user, delete_user
    )
from music_crud import (
    list_songs_for_user,list_songs_paginated, 
    create_song, update_song, get_song_by_id,delete_song
    )
from artist_crud import (
    create_artist, update_artist, delete_artist,
    get_artist_by_id,list_artists_paginated,
    list_songs_for_artist,export_artists_csv,
    import_artists_csv
    )

# In-memory session store: { session_id: user_id }
SESSIONS = {}

def generate_session_id(length=32):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

class MyHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        # Parse the path
        parsed_path = urllib.parse.urlparse(self.path)   #Parses the self.path (the requested URL).
        path = parsed_path.path
        query = urllib.parse.parse_qs(parsed_path.query)  #Converts the query string into a Python dictionary.

        if path == '/':
            self.handle_home_page()
        elif path == '/register_user':
            self.handle_user_register_form()
        elif path == '/users':
            self.handle_list_users(query)
        elif path == '/update_user':
            self.handle_user_update_form()
        elif path == '/delete_user':
            self.handle_user_delete_form()
        elif path == '/artists':
            self.handle_list_artists(query)
        elif path == '/artist_songs':
            self.handle_artist_songs(query)
        elif path == '/register_artist':
            self.handle_artist_register_form()
        elif path == '/update_artist':
            self.handle_artist_update_form()
        elif path == '/delete_artist':
            self.handle_artist_delete_form()
        elif path == '/artist_export':
            self.handle_artist_export()
        elif path == '/artist_import_form':
            self.handle_artist_import_form()
        elif path == '/songs':
            self.handle_list_songs(query)
        elif path == '/register_song':
            self.handle_song_register_form()
        elif path == '/update_song':
            self.handle_song_update_form()
        elif path == '/delete_song':
            self.handle_song_delete_form()
        elif path == '/dashboard':
            self.handle_dashboard()
        elif path == '/login':
            self.handle_login_form()
        elif path == '/logout':
            self.handle_logout()
        else:
            self.send_error(404, "Not Found")
        
        # elif path == '/list_user':
        #     self.handle_user_list_form()
        # elif path == '/list_song':
        #     self.handle_song_list_form()
       
        

    def do_POST(self):
        # We'll parse form data from the body
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        form_data = urllib.parse.parse_qs(body.decode())
        
        if path == '/register_user':
            self.handle_register_submit(form_data)
        elif path == '/update_user':
            self.handle_update_user_submit(form_data)
        elif path == '/delete_user':
            self.handle_delete_user_submit(form_data)
        elif path == '/register_artist':
            self.handle_artist_register_submit(form_data)
        elif path == '/update_artist':
            self.handle_artist_update_submit(form_data)
        elif path == '/delete_artist':
            self.handle_delete_artist_submit(form_data)
        elif path == '/artist_import_form':
            self.handle_artist_import(form_data)
        elif path == '/register_song':
            self.handle_song_register_submit(form_data)
        elif path == '/update_song':
            self.handle_song_update_submit(form_data)
        elif path == '/delete_song':
            self.handle_song_delete_submit(form_data)
        elif path == '/login':
            self.handle_login_submit(form_data)
        else:
            self.send_error(404, "Not Found")

    # ------------------------
    # Helpers
    # ------------------------

    def get_current_user_id(self):
        """
        Check the cookie for a session_id, look it up in SESSIONS.
        Return the user_id if logged in, otherwise None.
        """
        cookie_header = self.headers.get('Cookie')
        if not cookie_header:
            return None

        # Cookie might look like: session_id=ABC123
        cookies = {}
        for kv in cookie_header.split(';'):
            kv = kv.strip()
            if '=' in kv:
                key, value = kv.split('=', 1)
                cookies[key] = value

        session_id = cookies.get('session_id')
        if session_id and session_id in SESSIONS:
            return SESSIONS[session_id]
        return None
    
    

    def get_current_user_role(self):
        user_id = self.get_current_user_id()
        if not user_id:
            return None
        row = get_user_by_id(user_id)
        if row:
            # row = (id, first_name, last_name, email, role)
            return row[4]
        return None
    
    def send_html_response(self, html, status=200):
        """Utility to send HTML with UTF-8 encoding."""
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def redirect(self, location):
        self.send_response(302)
        self.send_header('Location', location)
        self.end_headers()

    def check_role(self, allowed_roles):
        """Return True if current user role is in allowed_roles, else False."""
        role = self.get_current_user_role()
        return role in allowed_roles
    # ------------------------
    # Route Handlers (GET)
    # ------------------------

    def handle_home_page(self):
        user_id = self.get_current_user_id()
        role = self.get_current_user_role()
        
        # If admin user is already logged in, redirect to dashboard immediately
        if user_id and role in ('super_admin', 'artist_manager', 'artist'):
            self.redirect('/dashboard')
            return
        
        # Otherwise show login link
        html = """
        <html>
        <head><title>Home</title></head>
        <body>
            <h1>Welcome! Please <a href="/login">Login</a></h1>
        </body>
        </html>
        """
        self.send_html_response(html)

    def handle_user_register_form(self):
        """Show a simple HTML form for user registration."""
        
        if self.get_current_user_id():
            self.redirect('/dashboard')
            
        html = """
        <html>
        <head><title>Register User</title></head>
        <body>
            <h1>Register</h1>
            <form method="POST" action="/register_user">
                <p>First Name: <input type="text" name="first_name"></p>
                <p>Last Name: <input type="text" name="last_name"></p>
                <p>Email: <input type="email" name="email"></p>
                <p>Password: <input type="password" name="password"></p>
                <p>Phone: <input type="phone" name="phone"></p>
                <p>DOB: <input type="dob" name="dob"></p>
                <p>Gender: 
                    <select name="gender">
                        <option value="" disabled selected>Select a gender</option> 
                        <option value="m">m</option>
                        <option value="f">f</option>
                        <option value="o">o</option>
                    </select>
                </p>
                <p>Address: <input type="address" name="address"></p>
                <p>Role: 
                    <select name="role">
                        <option value="" disabled selected>Select a role</option> 
                        <option value="artist">artist</option>
                        <option value="artist_manager">artist_manager</option>
                        <option value="super_admin">super_admin</option>
                    </select>
                </p>
                <input type="submit" value="Register">
            </form>
            <p><a href="/login">Back to Login</a></p>
            <p><a href="/">Back to Home</a></p>
        </body>
        </html>
        """
        self.send_html_response(html)

    def handle_user_update_form(self):
            """Show a simple HTML form for user update."""
            
            html = """
            <html>
            <head><title>Update User</title></head>
            <body>
                <h1>Update User</h1>
                <form method="POST" action="/update_user">
                    <p>User ID: <input type="number" name="id"></p>
                    <p>First Name: <input type="text" name="first_name"></p>
                    <p>Last Name: <input type="text" name="last_name"></p>
                    <p>Email: <input type="email" name="email"></p>
                    <p>Password: <input type="password" name="password"></p>
                    <p>Phone: <input type="phone" name="phone"></p>
                    <p>DOB: <input type="dob" name="dob"></p>
                    <p>Gender: 
                    <select name="gender">
                        <option value="" disabled selected>Select a gender</option> 
                        <option value="m">m</option>
                        <option value="f">f</option>
                        <option value="o">o</option>
                    </select>
                    </p>
                    <p>Address: <input type="address" name="address"></p>
                    <p>Role: 
                        <select name="role">
                            <option value="" disabled selected>Select a role</option> 
                            <option value="artist">artist</option>
                            <option value="artist_manager">artist_manager</option>
                            <option value="super_admin">super_admin</option>
                        </select>
                    </p>
                    <input type="submit" value="Update">
                </form>
                <p><a href="/">Back to Home</a></p>
            </body>
            </html>
            """
            self.send_html_response(html)

    def handle_user_delete_form(self):
            """Show a simple HTML form for deleting user."""
            
            html = """
            <html>
            <head><title>Delete User</title></head>
            <body>
                <h1>Delete</h1>
                <form method="POST" action="/delete_user">
                    <p>User ID: <input type="number" name="user_id"></p>
                    <input type="submit" value="Delete">
                </form>
                <p><a href="/">Back to Home</a></p>
            </body>
            </html>
            """
            self.send_html_response(html)

    def handle_artist_register_form(self):
        """Show a simple HTML form for artist registration."""

        html = """
        <html>
        <head><title>Register Artist</title></head>
        <body>
            <h1>Register</h1>
            <form method="POST" action="/register_artist">
                <p>User ID: <input type="integer" name="user_id"></p>
                <p>Name: <input type="text" name="name"></p>
                <p>DOB: <input type="text" name="dob"></p>
                <p>Gender: 
                    <select name="gender">
                        <option value="" disabled selected>Select a gender</option> 
                        <option value="m">m</option>
                        <option value="f">f</option>
                        <option value="o">o</option>
                    </select>
                </p>
                <p>Address: <input type="text" name="address"></p>
                <p>First_release_year: <input type="text" name="first_release_year"></p>
                <p>No_of_albums_released: <input type="text" name="no_of_albums_released"></p>
                <input type="submit" value="Register">
            </form>
            <p><a href="/">Back to Home</a></p>
        </body>
        </html>
        """
        self.send_html_response(html)

    def handle_artist_update_form(self):
            """Show a simple HTML form for artist update."""
            
            html = """
            <html>
            <head><title>Update Artist</title></head>
            <body>
                <h1>Update Artist</h1>
                <form method="POST" action="/update_artist">
                    <p>Artist ID: <input type="number" name="id"></p>
                    <p>Name: <input type="text" name="name"></p>
                    <p>DOB: <input type="text" name="dob"></p>
                    <p>Gender: 
                    <select name="gender">
                        <option value="" disabled selected>Select a gender</option> 
                        <option value="m">m</option>
                        <option value="f">f</option>
                        <option value="o">o</option>
                    </select>
                    </p>
                    <p>Address: <input type="text" name="address"></p>
                    <p>First_release_year: <input type="text" name="first_release_year"></p>
                    <p>No_of_albums_released: <input type="number" name="no_of_albums_released"></p>
                    <input type="submit" value="Update">
                </form>
                <p><a href="/">Back to Home</a></p>
            </body>
            </html>
            """
            self.send_html_response(html)

    def handle_artist_delete_form(self):
            """Show a simple HTML form for artist delete."""
            
            html = """
            <html>
            <head><title>Delete Artist</title></head>
            <body>
                <h1>Delete</h1>
                <form method="POST" action="/delete_artist">
                    <p>Artist ID: <input type="number" name="artist_id"></p>
                    <input type="submit" value="Delete">
                </form>
                <p><a href="/">Back to Home</a></p>
            </body>
            </html>
            """
            self.send_html_response(html)

    def handle_song_register_form(self):
        """Show a simple HTML form for song registration."""

        html = """
        <html>
        <head><title>Register Song</title></head>
        <body>
            <h1>Register</h1>
            <form method="POST" action="/register_song">
                <p>Artist ID: <input type="integer" name="artist_id"></p>
                <p>Title: <input type="text" name="title"></p>
                <p>Album Name: <input type="text" name="album_name"></p>
                <p>Genre: <input type="text" name="genre"></p>
                <input type="submit" value="Register">
            </form>
            <p><a href="/">Back to Home</a></p>
        </body>
        </html>
        """
        self.send_html_response(html)

    def handle_song_update_form(self):
            """Show a simple HTML form for song update."""
            html = """
            <html>
            <head><title>Update Song</title></head>
            <body>
                <h1>Update Song</h1>
                <form method="POST" action="/update_song">
                    <p>Song ID: <input type="number" name="id"></p>
                    <p>Title: <input type="text" name="title"></p>
                    <p>Album Name: <input type="text" name="album_name"></p>
                    <p>Genre: <input type="text" name="genre"></p>
                    <input type="submit" value="Update">
                </form>
                <p><a href="/">Back to Home</a></p>
            </body>
            </html>
            """
            self.send_html_response(html)

    def handle_song_delete_form(self):
            """Show a simple HTML form for deleting song."""
            
            html = """
            <html>
            <head><title>Delete Song</title></head>
            <body>
                <h1>Delete</h1>
                <form method="POST" action="/delete_song">
                    <p>Song ID: <input type="number" name="id"></p>
                    <input type="submit" value="Delete">
                </form>
                <p><a href="/">Back to Home</a></p>
            </body>
            </html>
            """
            self.send_html_response(html)
            
    def handle_login_form(self):
        # If already logged in, go to dashboard
        if self.get_current_user_id():
            self.redirect('/dashboard')
        html = """
        <html>
        <head><title>Login</title></head>
        <body>
            <h1>Login</h1>
            <form method="POST" action="/login">
                <p>Email: <input type="email" name="email"></p>
                <p>Password: <input type="password" name="password"></p>
                <input type="submit" value="Login" style="margin-bottom: 10px; display: block;">
            </form> 
            
            <p>New user? <a href="/register_user">Register here</a></p>
            <p><a href="/">Back to Home</a></p>
        </body>
        </html>
        """
        self.send_html_response(html)

    def handle_dashboard(self):
        """Show user info and list of songs for that user."""
        
        user_id = self.get_current_user_id()
        if not user_id:
            self.redirect('/')

        user_row = get_user_by_id(user_id)
        if not user_row:
            self.send_html_response("<h1>User not found</h1>", 404)

        # Show a simple "Admin panel" if super_admin or artist_manager
        # If user is an artist, maybe show a simpler view
        role = user_row[4]  # role
        if role == 'super_admin':
            html = f"""
            <html>
            <head><title>Dashboard</title></head>
            <body>
                <h1>Dashboard (Super Admin)</h1>
                <p><a href="/users">Manage Users</a></p>
                <p><a href="/artists">Manage Artists</a></p>
                <p><a href="/songs">Manage Songs</a></p>
                <p><a href="/artist_import_form">Import Artists (CSV)</a></p>
                <p><a href="/artist_export">Export Artists (CSV)</a></p>
                <p><a href="/logout">Logout</a></p>
            </body>
            </html>
            """
        elif role == 'artist_manager':
            html = f"""
            <html>
            <head><title>Dashboard</title></head>
            <body>
                <h1>Dashboard (Artist Manager)</h1>
                <p><a href="/artists">Manage Artists</a></p>
                <p><a href="/songs">Manage Songs</a></p>
                <p><a href="/artist_import_form">Import Artists (CSV)</a></p>
                <p><a href="/artist_export">Export Artists (CSV)</a></p>
                <p><a href="/logout">Logout</a></p>
            </body>
            </html>
            """
        else:
            # role == 'artist'
            # Just show songs for this user

            songs = list_songs_for_user(user_id)
            list_html = "<ul>"
            if songs:
                for sid, album, stype in songs:
                    list_html += f"<li>{album} ({stype})</li>"
                list_html += "</ul>"
            else:
                list_html = "<p>No songs found.</p>"
            html = f"""
            <html>
            <head><title>Dashboard</title></head>
            <body>
                <h1>Dashboard (Artist)</h1>
                <h2>Your Songs:</h2>
                {list_html}
                <p><a href="/songs">Manage Songs</a></p>
                <p><a href="/logout">Logout</a></p>
            </body>
            </html>
            """

        self.send_html_response(html)

    def handle_list_users(self, query):
        """List users with pagination (super_admin only)."""
        if not self.check_role(['super_admin']):
            self.send_html_response("<h1>Access Denied</h1>", 403)
            return

        page = int(query.get('page', [1])[0])
        limit = int(query.get('limit', [5])[0])
        users = list_users_paginated(page=page, limit=limit)

        html = "<h1>User List</h1><table border='1'>"
        html += "<tr><th>ID</th><th>Name</th><th>Email</th><th>Role</th></tr>"
        for (uid, fname, lname, email, role) in users:
            html += f"<tr><td>{uid}</td><td>{fname} {lname}</td><td>{email}</td><td>{role}</td></tr>"
        html += "</table>"
        html += f"<p>Page: {page}</p>"
        html += f"<p><a href='/update_user'>Update User</a></p>"
        html += f"<p><a href='/delete_user'>Delete User</a></p>"
        html += f"<p><a href='/dashboard'>Back to Dashboard</a></p>"
        self.send_html_response(html)

    def handle_list_artists(self, query):
        """List artists with pagination. super_admin or artist_manager only."""
        if not self.check_role(['super_admin','artist_manager']):
            self.send_html_response("<h1>Access Denied</h1>", 403)
            return

        page = int(query.get('page', [1])[0])
        limit = int(query.get('limit', [5])[0])
        artists = list_artists_paginated(page=page, limit=limit)

        html = "<h1>Artist List</h1><table border='1'>"
        html += "<tr><th>ID</th>Name<th></th><th>Gender</th><th>First Release Year</th><th>#Albums</th><th>Actions</th></tr>"
        for (aid, user_id, name, gender, first_release, no_albums) in artists:
            html += f"<tr><td>{aid}</td><td>{name}</td><td>{gender}</td><td>{first_release}</td><td>{no_albums}</td>"
            # Button to see songs for this artist:
            html += f"<td><a href='/artist_songs?artist_id={aid}'>View Songs</a></td></tr>"
        html += "</table>"
        html += f"<p>Page: {page}</p>"
        html += f"<p><a href='/register_artist'>Create Artist</a></p>"
        html += f"<p><a href='/update_artist'>Update Artist</a></p>"
        html += f"<p><a href='/delete_artist'>Delete Artist</a></p>"
        html += f"<p><a href='/dashboard'>Back to Dashboard</a></p>"
        self.send_html_response(html)

    def handle_list_songs(self, query):
        """List songs with pagination. super_admin or artist_manager only."""
        if not self.check_role(['super_admin','artist_manager']):
            self.send_html_response("<h1>Access Denied</h1>", 403)
            
        page = int(query.get('page', [1])[0])
        limit = int(query.get('limit', [5])[0])
        songs = list_songs_paginated(page=page, limit=limit)

        html = "<h1>Song List</h1><table border='1'>"
        html += "<tr><th>ID</th><th>Artist ID</th><th>Album Name</th><th>Type</th></tr>"
        for (sid, artist_id, album_name, stype) in songs:
            html += f"<tr><td>{sid}</td><td>{artist_id}</td><td>{album_name}</td><td>{stype}</td></tr>"
        html += "</table>"
        html += f"<p>Page: {page}</p>"
        html += f"<p><a href='/register_song'>Create Song</a></p>"
        html += f"<p><a href='/update_song'>Update Song</a></p>"
        html += f"<p><a href='/delete_song'>Delete Song</a></p>"
        html += f"<p><a href='/dashboard'>Back to Dashboard</a></p>"
        self.send_html_response(html)

    def handle_artist_songs(self, query):
        """Show a list of songs for a particular artist."""
        if not self.check_role(['super_admin','artist_manager']):
            self.send_html_response("<h1>Access Denied</h1>", 403)
            return

        artist_id = query.get('artist_id', [None])[0]
        if not artist_id:
            self.send_html_response("<h1>Missing artist_id</h1>", 400)
            return

        songs = list_songs_for_artist(artist_id)
        html = f"<h1>Artist {artist_id} Songs</h1><ul>"
        if songs:
            for (mid, album_name, stype) in songs:
                html += f"<li>{album_name} ({stype})</li>"
        else:
            html += "<li>No songs found.</li>"
        html += "</ul>"
        html += "<p><a href='/artists'>Back to Artists</a></p>"
        self.send_html_response(html)

    def handle_artist_export(self):
        """Export all artists to CSV (super_admin or artist_manager)."""
        if not self.check_role(['super_admin','artist_manager']):
            self.send_html_response("<h1>Access Denied</h1>", 403)
            return
        
        csv_data = export_artists_csv()
        # Send as a CSV file download
        self.send_response(200)
        self.send_header('Content-Type', 'text/csv; charset=utf-8')
        self.send_header('Content-Disposition', 'attachment; filename="artists.csv"')
        self.end_headers()
        self.wfile.write(csv_data.encode('utf-8'))

    def handle_artist_import_form(self):
        """Show a form to upload CSV for import."""
        if not self.check_role(['super_admin','artist_manager']):
            self.send_html_response("<h1>Access Denied</h1>", 403)
            return
        html = """
        <html>
        <head><title>Import Artists (CSV)</title></head>
        <body>
            <h1>Import Artists (CSV)</h1>
            <form method="POST" action="/artist_import_form" enctype="application/x-www-form-urlencoded">
                <p>Paste CSV content here:</p>
                <textarea name="csv_content" rows="10" cols="50"></textarea><br>
                <input type="submit" value="Import">
            </form>
            <p><a href="/dashboard">Back to Dashboard</a></p>
        </body>
        </html>
        """
        self.send_html_response(html)

    def handle_logout(self):
        """Clear the session cookie (if any)."""
        session_id = None
        cookie_header = self.headers.get('Cookie')
        if cookie_header:
            for kv in cookie_header.split(';'):
                kv = kv.strip()
                if '=' in kv:
                    key, value = kv.split('=', 1)
                    if key == 'session_id':
                        session_id = value
                        break
        if session_id and session_id in SESSIONS:
            del SESSIONS[session_id]

        # Redirect to home
        self.send_response(302)
        self.send_header('Location', '/')
        # Overwrite the cookie
        self.send_header('Set-Cookie', 'session_id=; Max-Age=0')
        self.end_headers()

    # ------------------------
    # Route Handlers (POST)
    # ------------------------

    def handle_register_submit(self, form_data):
        first_name = form_data.get('first_name', [''])[0]
        last_name = form_data.get('last_name', [''])[0]
        email = form_data.get('email', [''])[0]
        password = form_data.get('password', [''])[0]
        phone = form_data.get('email', [''])[0]
        dob = form_data.get('dob', [''])[0]
        gender = form_data.get('gender', [''])[0]
        address = form_data.get('address', [''])[0]
        role = form_data.get('role', [''])[0]

        # Create user
        try:
            user_id = create_user(first_name, last_name, email, password, phone, dob, gender, address, role)
            # After registration, let's redirect them to home or login
            self.redirect('/login')

        except Exception as e:
            # Possibly an IntegrityError if email is already taken
            html = f"<h1>Error creating user: {e}</h1><p><a href='/register'>Try again</a></p>"
            self.send_html_response(html, 400)

    def handle_artist_import(self, form_data):
        """Handle CSV import for artists."""
        # if not self.check_role(['super_admin','artist_manager']):
        #     self.send_html_response("<h1>Access Denied</h1>", 403)
        #     return
        csv_content = form_data.get('csv_content', [''])[0]
        try:
            import_artists_csv(csv_content)
            self.send_html_response("<h1>Import Successful</h1><p><a href='/dashboard'>Back</a></p>")
        except Exception as e:
            html = f"<h1>Error importing CSV: {e}</h1><p><a href='/artist_import_form'>Try again</a></p>"
            self.send_html_response(html, 400)

    def handle_update_user_submit(self, form_data):
        # Parse the form values (each value is a list; we take the first element)
        user_id = form_data.get('id', [''])[0]
        first_name = form_data.get('first_name', [''])[0]
        last_name  = form_data.get('last_name', [''])[0]
        email      = form_data.get('email', [''])[0]
        password   = form_data.get('password', [''])[0]
        phone = form_data.get('phone', [''])[0]
        dob = form_data.get('dob', [''])[0]
        gender     = form_data.get('gender', [''])[0]
        address = form_data.get('address', [''])[0]
        role       = form_data.get('role', [''])[0]

        # Build a dictionary of the fields to update.
        # Only include fields that are not empty (if you want to update selectively)
        fields_to_update = {}
        if user_id is not None:
            if first_name:
                fields_to_update['first_name'] = first_name
            if last_name:
                fields_to_update['last_name'] = last_name
            if email:
                fields_to_update['email'] = email
            if password:
                # Hash the new password before storing it
                fields_to_update['password'] = hash_password(password)
            if phone:
                fields_to_update['phone'] = phone
            if dob:
                fields_to_update['dob'] = dob
            if gender:
                fields_to_update['gender'] = gender
            if address:
                fields_to_update['address'] = address
            if role:
                fields_to_update['role'] = role
        else:
            self.send_html_response("<h1>Error: User ID field is required and is of int type.</h1>", 401)
            return
        
        # Get the current user's id (assumes you have a function like get_current_user_id)
        user_id = get_user_by_id(user_id)  # Adjust according to your session handling
        if user_id is None:
            self.send_html_response("<h1>Error: User does not exist </h1>", 401)
            return
        # Now call update_user with all the fields
        update_user(user_id[0], **fields_to_update)

        # Optionally, redirect to the dashboard or another page after updating
        self.send_response(302)
        self.send_header('Location', '/dashboard')
        self.end_headers()

    def handle_delete_user_submit(self, form_data):
        # Parse the form values (we take the first value)
        user_id = form_data.get("user_id",[''])[0]
        if user_id:
            user_obj = get_user_by_id(user_id)
            if user_obj:
                delete_user(user_id)
                self.send_response(302)
                self.send_header('Location', '/dashboard')
                self.end_headers()
            else:
                self.send_html_response(f"<h1>Error: User with user_id {user_id} doesnot exist.", 401)

        if user_id is None:
            self.send_html_response("<h1>Error: User ID is required and is positive integer type.", 401)

    def handle_artist_register_submit(self, form_data):
        user_id = form_data.get('user_id', [''])[0]
        name = form_data.get('name', [''])[0]
        dob = form_data.get('dob', [''])[0]
        gender = form_data.get('gender', [''])[0]
        address = form_data.get('address', [''])[0]
        first_release_year = form_data.get('first_release_year', [''])[0]
        no_of_albums_released = form_data.get('no_of_albums_released', [''])[0]

        # Create user
        try:
            create_artist(user_id, name, dob, gender, address, first_release_year, no_of_albums_released)
            # After registration, let's redirect them to home or login
            self.send_response(302)
            self.send_header('Location', '/dashboard')
            self.end_headers()
        except Exception as e:
            # Possibly an IntegrityError if email is already taken
            html = f"<h1>Error creating artist user: {e}</h1><p><a href='/register_user'>Try again</a></p>"
            self.send_html_response(html, 400)

    def handle_artist_update_submit(self, form_data):
        # Parse the form values (each value is a list; we take the first element)
        artist_id = form_data.get('id', [''])[0]
        name = form_data.get('name', [''])[0]
        dob      = form_data.get('dob', [''])[0]
        gender   = form_data.get('gender', [''])[0]
        address  = form_data.get('address', [''])[0]
        first_release_year       = form_data.get('first_release_year', [''])[0]
        no_of_albums_released       = form_data.get('no_of_albums_released', [''])[0]

        # Build a dictionary of the fields to update.
        # Only include fields that are not empty (if you want to update selectively)
        fields_to_update = {}
        if  artist_id is not None:
            if name:
                fields_to_update['name'] = name
            if dob:
                fields_to_update['dob'] = dob
            if address:
                fields_to_update['address'] = address
            if gender:
                fields_to_update['gender'] = gender
            if first_release_year:
                fields_to_update['first_release_year'] = first_release_year
            if no_of_albums_released:
                fields_to_update['no_of_albums_released'] = no_of_albums_released
        else:
            self.send_html_response("<h1>Error: Artist ID field is required and is of int type.</h1>", 401)
            return
        

        # Get the current user's id (assumes you have a function like get_current_user_id)
        artist_obj = get_artist_by_id(artist_id)  # Adjust according to your session handling
        if artist_id is None:
            self.send_html_response(f"<h1>Error: Artist with artist id {artist_id} does not exist!</h1>", 401)

        # Now call update_user with all the fields
        update_artist(artist_id, **fields_to_update)

        # Optionally, redirect to the dashboard or another page after updating
        self.send_response(302)
        self.send_header('Location', '/dashboard')
        self.end_headers()

    def handle_delete_artist_submit(self, form_data):
        # Parse the form values (we take the first value)
        artist_id = form_data.get("artist_id",[''])[0]
        if artist_id:
            artist_obj = get_artist_by_id(artist_id)
            if artist_obj:
                delete_artist(artist_id)
                self.send_response(302)
                self.send_header('Location', '/dashboard')
                self.end_headers()
            else:
                self.send_html_response(f"<h1>Error: Artist with artist_id {artist_id} doesnot exist.", 401)

        if artist_id is None:
            self.send_html_response("<h1>Error: Artist ID is required and is positive integer type.", 401)

    def handle_song_register_submit(self, form_data):
        artist_id = form_data.get('artist_id', [''])[0]
        title = form_data.get('title', [''])[0]
        album_name = form_data.get('album_name', [''])[0]
        genre = form_data.get('genre', [''])[0]
       
        # Create user
        try:
            create_song(artist_id, title, album_name, genre)
            # After registration, let's redirect them to home or login
            self.send_response(302)
            self.send_header('Location', '/dashboard')
            self.end_headers()

        except Exception as e:
            # Possibly an IntegrityError if email is already taken
            html = f"<h1>Error creating song: {e}</h1><p><a href='/register_song'>Try again</a></p>"
            self.send_html_response(html, 400)

    def handle_song_update_submit(self, form_data):
        # Parse the form values (each value is a list; we take the first element)
        song_id = form_data.get('id', [''])[0]
        title = form_data.get('title', [''])[0]
        album_name      = form_data.get('album_name', [''])[0]
        genre  = form_data.get('genre', [''])[0]
       

        # Build a dictionary of the fields to update.
        # Only include fields that are not empty (if you want to update selectively)
        fields_to_update = {}
        if  song_id is not None:
            if title:
                fields_to_update['title'] = title
            if album_name:
                fields_to_update['album_name'] = album_name
            if genre:
                fields_to_update['genre'] = genre
            
        else:
            self.send_html_response("<h1>Error: Song ID field is required and is of int type.</h1>", 401)
            return
        

        # Get the current user's id (assumes you have a function like get_current_user_id)
        song_obj = get_song_by_id(song_id)  # Adjust according to your session handling
        if song_obj is None:
            self.send_html_response(f"<h1>Error: song with song id {song_id} does not exist!</h1>", 401)

        # Now call update_user with all the fields
        update_song(song_id, **fields_to_update)

        # Optionally, redirect to the dashboard or another page after updating
        self.send_response(302)
        self.send_header('Location', '/dashboard')
        self.end_headers()

    def handle_song_delete_submit(self, form_data):
        # Parse the form values (we take the first value)
        song_id = form_data.get("id",[''])[0]
        if song_id:
            song_obj = get_song_by_id(song_id)
            if song_obj:
                delete_song(song_id)
                self.send_response(302)
                self.send_header('Location', '/dashboard')
                self.end_headers()
            else:
                self.send_html_response(f"<h1>Error: Song with song_id {song_id} doesnot exist.", 401)

        if song_id is None:
            self.send_html_response("<h1>Error: Song ID is required and is positive integer type.", 401)
        

    def handle_login_submit(self, form_data):
        email = form_data.get('email', [''])[0]
        password = form_data.get('password', [''])[0]
        user_info = login(email, password)
        if user_info:
            # Create session
            session_id = generate_session_id()
            SESSIONS[session_id] = user_info["id"]
            self.send_response(302)
            self.send_header('Location', '/dashboard')
            # Set a cookie
            self.send_header('Set-Cookie', f'session_id={session_id}; HttpOnly')
            self.end_headers()
        else:
            html = "<h1>Invalid credentials</h1><p><a href='/login'>Try again</a></p>"
            self.send_html_response(html, 401)

# ---------------------------------------------
# Run the server
# ---------------------------------------------
import socketserver

class MyTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

def run_server(port=8001):
    create_tables()  # Ensure DB tables are created
    with MyTCPServer(("0.0.0.0", port), MyHandler) as httpd:
        print(f"serving on port {port}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
