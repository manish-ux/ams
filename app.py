import http.server
import socketserver
import urllib.parse
import random
import string
from database import create_tables      
from user_crud import create_user, login, get_user_by_id
from music_crud import list_songs_for_user

# In-memory session store: { session_id: user_id }
SESSIONS = {}

def generate_session_id(length=32):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

class MyHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        # Parse the path
        path = self.path
        if path == '/':
            self.handle_home_page()
        elif path == '/register':
            self.handle_register_form()
        elif path == '/login':
            self.handle_login_form()
        elif path == '/dashboard':
            self.handle_dashboard()
        elif path == '/logout':
            self.handle_logout()
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        # We'll parse form data from the body
        path = self.path
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        form_data = urllib.parse.parse_qs(body.decode())

        if path == '/register':
            self.handle_register_submit(form_data)
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

    def send_html_response(self, html, status=200):
        """Utility to send HTML with UTF-8 encoding."""
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    # ------------------------
    # Route Handlers (GET)
    # ------------------------

    def handle_home_page(self):
        user_id = self.get_current_user_id()
        if user_id:
            # If user is logged in, show a link to Dashboard, plus Logout
            html = f"""
            <html>
            <head><title>Home</title></head>
            <body>
                <h1>Welcome!</h1>
                <p>You are logged in as user_id = {user_id}</p>
                <p><a href="/dashboard">Go to Dashboard</a></p>
                <p><a href="/logout">Logout</a></p>
            </body>
            </html>
            """
        else:
            # If not logged in, show links to Login or Register
            html = """
            <html>
            <head><title>Home</title></head>
            <body>
                <h1>Welcome!</h1>
                <p><a href="/login">Login</a></p>
                <p><a href="/register">Register</a></p>
            </body>
            </html>
            """
        self.send_html_response(html)

    def handle_register_form(self):
        """Show a simple HTML form for registration."""
        html = """
        <html>
        <head><title>Register</title></head>
        <body>
            <h1>Register</h1>
            <form method="POST" action="/register">
                <p>First Name: <input type="text" name="first_name"></p>
                <p>Last Name: <input type="text" name="last_name"></p>
                <p>Email: <input type="email" name="email"></p>
                <p>Password: <input type="password" name="password"></p>
                <p>Gender: <input type="text" name="gender"></p>
                <p>Role: 
                    <select name="role">
                        <option value="artist">artist</option>
                        <option value="artist_manager">artist_manager</option>
                        <option value="super_admin">super_admin</option>
                    </select>
                </p>
                <input type="submit" value="Register">
            </form>
            <p><a href="/">Back to Home</a></p>
        </body>
        </html>
        """
        self.send_html_response(html)

    def handle_login_form(self):
        """Show a simple HTML form for login."""
        html = """
        <html>
        <head><title>Login</title></head>
        <body>
            <h1>Login</h1>
            <form method="POST" action="/login">
                <p>Email: <input type="email" name="email"></p>
                <p>Password: <input type="password" name="password"></p>
                <input type="submit" value="Login">
            </form>
            <p><a href="/">Back to Home</a></p>
        </body>
        </html>
        """
        self.send_html_response(html)

    def handle_dashboard(self):
        """Show user info and list of songs for that user."""
        user_id = self.get_current_user_id()
        if not user_id:
            # Not logged in, redirect to home
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()
            return self.handle_home_page()

        # Get user info
        user_row = get_user_by_id(user_id)
        if not user_row:
            # Something’s wrong: user not found
            self.send_html_response("<h1>User not found</h1>", 404)
            return

        _, first_name, last_name, email, role = user_row

        # List songs for this user
        songs = list_songs_for_user(user_id)  # e.g. [(id, album_name, type, stage_name), ...]

        song_list_html = "<ul>"
        for album_name, genre, artist_name in songs:
            song_list_html += f"<li>{album_name} {genre} {artist_name}</li>"
        song_list_html += "</ul>" if songs else "<li>No songs found.</li></ul>"

        html = f"""
        <html>
        <head><title>Dashboard</title></head>
        <body>
            <h1>Dashboard</h1>
            <p>User: {first_name} {last_name} | Email: {email} | Role: {role}</p>
            <h2>Your Songs:</h2>
            {song_list_html}
            <p><a href="/">Home</a> | <a href="/logout">Logout</a></p>
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
        gender = form_data.get('gender', [''])[0]
        role = form_data.get('role', [''])[0]

        # Create user
        try:
            user_id = create_user(first_name, last_name, email, password, gender, role)
            # After registration, let's redirect them to home or login
            self.send_response(302)
            self.send_header('Location', '/login')
            self.end_headers()
        except Exception as e:
            # Possibly an IntegrityError if email is already taken
            html = f"<h1>Error creating user: {e}</h1><p><a href='/register'>Try again</a></p>"
            self.send_html_response(html, 400)

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
def run_server(port=8001):
    create_tables()  # Ensure DB tables are created
    with socketserver.TCPServer(("0.0.0.0", port), MyHandler) as httpd:
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
