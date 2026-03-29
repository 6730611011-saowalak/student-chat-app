from flask import Flask, render_template, render_template_string, request, redirect, session, send_from_directory
from flask_socketio import SocketIO, send
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"
socketio = SocketIO(app)

UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

DB = "chat.db"


# =============================
# DATABASE SETUP
# =============================

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        message TEXT,
        time TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()


# =============================
# LOGIN PAGE
# =============================

login_html = """

<!DOCTYPE html>
<html>

<head>

<title>Student Chat Login</title>

<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

<style>

body{
background: linear-gradient(135deg,#667eea,#764ba2);
height:100vh;
display:flex;
justify-content:center;
align-items:center;
}

.card{
width:360px;
padding:30px;
border-radius:20px;
}

</style>

</head>

<body>

<div class="card shadow-lg">

<h3 class="text-center mb-4">🎓 Student Chat System</h3>

<form method="POST">

<input name="username" class="form-control mb-3" placeholder="Username" required>

<input name="password" type="password" class="form-control mb-3" placeholder="Password" required>

<button class="btn btn-primary w-100">Login</button>

</form>

<div class="text-center mt-3">

<a href="/register">Create account</a>

</div>

</div>

</body>

</html>

"""


# =============================
# REGISTER PAGE
# =============================

register_html = """

<!DOCTYPE html>
<html>

<head>

<title>Create Account</title>

<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

<style>

body{
background: linear-gradient(135deg,#ff758c,#ff7eb3);
height:100vh;
display:flex;
justify-content:center;
align-items:center;
}

.card{
width:360px;
padding:30px;
border-radius:20px;
}

</style>

</head>

<body>

<div class="card shadow-lg">

<h3 class="text-center mb-4">Create Account</h3>

<form method="POST">

<input name="username" class="form-control mb-3" placeholder="Username" required>

<input name="password" type="password" class="form-control mb-3" placeholder="Password" required>

<button class="btn btn-success w-100">Register</button>

</form>

<div class="text-center mt-3">

<a href="/">Back to login</a>

</div>

</div>

</body>

</html>

"""


# =============================
# ROUTES
# =============================

@app.route("/", methods=["GET","POST"])
def login():

    if request.method=="POST":

        username=request.form["username"]
        password=request.form["password"]

        conn=sqlite3.connect(DB)
        c=conn.cursor()

        c.execute("SELECT * FROM users WHERE username=? AND password=?",(username,password))

        user=c.fetchone()

        conn.close()

        if user:

            session["user"]=username

            return redirect("/chat")

    return render_template_string(login_html)


@app.route("/register", methods=["GET","POST"])
def register():

    if request.method=="POST":

        username=request.form["username"]
        password=request.form["password"]

        conn=sqlite3.connect(DB)
        c=conn.cursor()

        try:
            c.execute("INSERT INTO users(username,password) VALUES (?,?)",(username,password))
            conn.commit()
        except:
            pass

        conn.close()

        return redirect("/")

    return render_template_string(register_html)


@app.route("/chat")
def chat():

    if "user" not in session:
        return redirect("/")

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT username, message, time FROM messages ORDER BY id ASC")

    messages = c.fetchall()

    conn.close()

    return render_template(
        "index.html",
        username=session["user"],
        messages=messages
    )


@app.route("/logout")
def logout():

    session.pop("user",None)

    return redirect("/")


@app.route("/upload", methods=["POST"])
def upload():

    if "file" not in request.files:
        return redirect("/chat")

    file=request.files["file"]

    if file.filename=="":
        return redirect("/chat")

    filepath=os.path.join(UPLOAD_FOLDER,file.filename)

    file.save(filepath)

    return redirect("/chat")


@app.route("/uploads/<filename>")
def uploaded_file(filename):

    return send_from_directory(UPLOAD_FOLDER,filename)


# =============================
# SOCKET EVENT
# =============================

@socketio.on("message")
def handle_message(msg):

    username=session.get("user","Unknown")

    time=datetime.now().strftime("%H:%M")

    full_msg=f"{username}: {msg} ({time})"

    conn=sqlite3.connect(DB)
    c=conn.cursor()

    c.execute("INSERT INTO messages(username,message,time) VALUES (?,?,?)",(username,msg,time))

    conn.commit()
    conn.close()

    send(full_msg,broadcast=True)


# =============================
# MAIN
# =============================

if __name__=="__main__":

    socketio.run(app,debug=True)
