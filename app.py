from flask import Flask, request, jsonify, session, render_template, redirect, url_for, flash
from flask_bcrypt import Bcrypt
import pymysql
import os
from google.cloud.sql.connector import Connector # type: ignore

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key')
bcrypt = Bcrypt(app)

# Initialize Cloud SQL Connector
connector = Connector()

def get_db_connection():
    conn = connector.connect(
        os.environ['INSTANCE_CONNECTION_NAME'],
        "pymysql",
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASS'],
        db=os.environ['DB_NAME']
    )
    return conn

# Create users table if not exists
def init_db():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(30) UNIQUE,
                password VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    conn.commit()
    conn.close()

# Create MySQL user
def create_mysql_user(username, password):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE USER '{username}'@'%' IDENTIFIED BY '{password}'")
            cursor.execute(f"GRANT SELECT, INSERT, UPDATE ON {os.environ['DB_NAME']}.* TO '{username}'@'%'")
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error creating MySQL user: {e}")
        return False

# Render registration page
@app.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html')

# Handle registration form submission
@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash('Username and password required', 'error')
        return redirect(url_for('register_page'))

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                flash('Username already exists', 'error')
                return redirect(url_for('register_page'))

            cursor.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                (username, hashed_password)
            )
            conn.commit()

            if create_mysql_user(username, password):
                flash('Registration successful! You can now log in.', 'success')
                return redirect(url_for('login_page'))
            else:
                flash('Failed to create MySQL user', 'error')
                return redirect(url_for('register_page'))
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('register_page'))
    finally:
        conn.close()

# Render login page
@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

# Handle login form submission
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash('Username and password required', 'error')
        return redirect(url_for('login_page'))

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            if user and bcrypt.check_password_hash(user[0], password):
                session['username'] = username
                flash('Login successful!', 'success')
                return redirect(url_for('home'))
            else:
                flash('Invalid credentials', 'error')
                return redirect(url_for('login_page'))
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('login_page'))
    finally:
        conn.close()

# Home page after login
@app.route('/')
def home():
    if 'username' in session:
        return render_template('home.html', username=session['username'])
    return redirect(url_for('login_page'))

# Initialize database on startup
init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))