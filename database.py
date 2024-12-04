from flask import Flask, g, request, jsonify, render_template, redirect, url_for, session
import sqlite3
import requests
import os

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session signing

# Path to the SQLite database file
DATABASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "Plant_Parenthood2.db"))


# Helper function to get a database connection
def get_db():
    """
    Get a database connection for the current request context.
    """
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE, check_same_thread=False)
        g.db.row_factory = sqlite3.Row  # Optional: Makes rows behave like dictionaries
    return g.db

# Cleanup function to close the database connection after each request
@app.teardown_appcontext
def close_db(exception):
    """
    Close the database connection at the end of the request.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Mock user data for authentication
users = {'admin': 'password', 'comfyd03': 'Comfyd03!', 'dylan': 'dylan', 'coraorog':'Cora51804'}

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login route to authenticate a user and store their session.
    """
    theme = 'dark'  # Default theme for the login page

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in users and users[username] == password:
            session['username'] = username  # Store username in session
            return redirect(url_for('home'))  # Redirect to home after successful login
        else:
            return "Invalid credentials! Try again."

    # Render the login form with the default theme
    return render_template('login.html', theme=theme)


@app.route('/logout')
def logout():
    """
    Logout route to clear the user session.
    """
    session.pop('username', None)  # Remove username from session
    return redirect(url_for('login'))  # Redirect to login after logout

@app.route('/')
def home():
    """
    Home page showing available tables and a personalized welcome message
    if the user is logged in. Redirects to /login if not logged in.
    """
    # Check if the user is logged in
    if 'username' not in session:
        # Redirect to the login page if the user is not logged in
        return redirect(url_for('login'))
    username = session['username']
    # User is logged in; display tables and username
    db = get_db()
    cursor = db.cursor()
    # Fetch the user's current theme preference
    cursor.execute("SELECT theme FROM user_preferences WHERE username = ?", (username,))
    preference = cursor.fetchone()
    theme = preference['theme'] if preference else 'dark'


    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    all_tables = [table[0] for table in cursor.fetchall()]
    # Filter for desired tables
    allowed_tables = ['ORDERS', 'PLANTS', 'CUSTOMERS']
    tables = [table for table in all_tables if table in allowed_tables]
    return render_template('index.html', username=session['username'], tables=tables, theme=theme)

@app.route('/api/plants')
def get_plants():
    """
    Proxy route to fetch plant data from the Trefle API.
    Requires user to be logged in.
    """
    if 'username' not in session:
        return redirect(url_for('login'))
    API_TOKEN = '1t8skG5tcDfrLsVt3IGQpZYMhW9_2ZMTyRX7tt6mbG4'
    trefle_url = f'https://trefle.io/api/v1/plants?token={API_TOKEN}'

    response = requests.get(trefle_url)
    if response.status_code == 200:
        return jsonify(response.json())  # Return the API response as JSON
    else:
        return jsonify({"error": "Failed to fetch plant data"}), response.status_code

@app.route('/view/<table_name>')
def view_table(table_name):
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    db = get_db()
    cursor = db.cursor()

    # Fetch theme preference
    cursor.execute("SELECT theme FROM user_preferences WHERE username = ?", (username,))
    preference = cursor.fetchone()
    theme = preference['theme'] if preference else 'dark'

    # Fetch records and columns
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]

    return render_template('view.html', table_name=table_name, records=rows, columns=columns, theme=theme)

@app.route('/preferences', methods=['GET', 'POST'])
def preferences():
    """
    User preferences page for changing theme settings.
    """
    if 'username' not in session:
        return redirect(url_for('login'))

    db = get_db()
    cursor = db.cursor()
    username = session['username']

    if request.method == 'POST':
        # Update theme preference
        theme = request.form.get('theme', 'dark')  # Default to 'dark' if no theme selected
        cursor.execute(
            "INSERT INTO user_preferences (username, theme) VALUES (?, ?) "
            "ON CONFLICT(username) DO UPDATE SET theme = ?",
            (username, theme, theme)
        )
        db.commit()
        return redirect(url_for('preferences'))

    # Fetch the current theme preference for the user
    cursor.execute("SELECT theme FROM user_preferences WHERE username = ?", (username,))
    preference = cursor.fetchone()
    current_theme = preference['theme'] if preference else 'dark'

    return render_template('preferences.html', current_theme=current_theme, theme=current_theme)



@app.route('/add/<table_name>', methods=['GET', 'POST'])
def add_record(table_name):
    """
    Add a new record to the specified table via a web form.
    Requires user to be logged in.
    """
    if 'username' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()

    # Fetch theme preference for the logged-in user
    username = session['username']
    cursor.execute("SELECT theme FROM user_preferences WHERE username = ?", (username,))
    preference = cursor.fetchone()
    theme = preference['theme'] if preference else 'dark'

    if request.method == 'POST':
        # Get form data from the user
        data = {key: value for key, value in request.form.items()}

        # Prepare and execute the INSERT query
        placeholders = ", ".join(["?"] * len(data))
        columns = ", ".join(data.keys())
        values = list(data.values())
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        cursor.execute(query, values)
        db.commit()
        return redirect(url_for('view_table', table_name=table_name))

    # Fetch column names to generate the form dynamically
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    
    return render_template('add.html', table_name=table_name, columns=columns, theme=theme)


@app.route('/delete/<table_name>/<column>/<value>', methods=['POST'])
def delete_record(table_name, column, value):
    """
    Delete a record from the specified table.
    Requires user to be logged in.
    """
    if 'username' not in session:
        return redirect(url_for('login'))
    db = get_db()
    cursor = db.cursor()

    # Execute DELETE query
    query = f"DELETE FROM {table_name} WHERE {column} = ?"
    cursor.execute(query, (value,))
    db.commit()
    return redirect(url_for('view_table', table_name=table_name))

if __name__ == '__main__':
    app.run(debug=True)
