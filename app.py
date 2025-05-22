from flask import Flask, request, render_template_string
from sqlalchemy import create_engine, text
import os

app = Flask(__name__)

# Get DB credentials from environment variables
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")

# SQLAlchemy connection string
DB_URI = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
engine = create_engine(DB_URI, pool_recycle=280)

login_form = '''
    <h2>User Login</h2>
    <form method="post">
        Username: <input name="username"><br>
        Password: <input name="password" type="password"><br>
        <input type="submit" value="Login">
    </form>
'''

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM users WHERE username=:u AND password=:p"),
                                  {"u": uname, "p": pwd})
            user = result.fetchone()
            if user:
                return f"<h3>Welcome, {uname}!</h3>"
            else:
                return "<h3>Login failed. Invalid credentials.</h3>" + login_form
    return login_form

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
