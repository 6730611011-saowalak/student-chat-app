from flask import Flask, render_template_string, request, redirect, session, send_from_directory
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
# CHAT PAGE (NEW PROFESSIONAL UI)
# =============================

chat_html = """

<!DOCTYPE html>
<html>

<head>

<title>Student Chat System</title>

<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

<style>

body{
background:#eef2f7;
}

.chat-container{
max-width:900px;
margin:auto;
margin-top:20px;
}

.chat-box{
height:420px;
overflow-y:scroll;
background:white;
padding:20px;
border-radius:15px;
box-shadow:0px 3px 10px rgba(0,0,0,0.1);
}

.msg{
padding:10px 15px;
margin:8px;
border-radius:20px;
max-width:60%;
display:inline-block;
}

.me{
background:#0d6efd;
color:white;
margin-left:auto;
display:block;
}

.other{
background:#e9ecef;
}

.topbar{
display:flex;
justify-content:space-between;
align-items:center;
margin-bottom:15px;
}

.file-upload{
margin-top:10px;
}

</style>

</head>

<body>

<div class="chat-container">

<div class="topbar">

<h4>🎓 Student Chat System</h4>

<div>

<span class="badge bg-success">Online: {{username}}</span>

<a href="/logout" class="btn btn-danger btn-sm">Logout</a>

</div>

</div>


<div id="chat" class="chat-box"></div>


<form id="msgForm" class="d-flex gap-2 mt-3">

<input id="msg" class="form-control" placeholder="Type message..." required>

<button class="btn btn-primary">Send</button>

</form>


<form action="/upload" method="POST" enctype="multipart/form-data" class="file-upload d-flex gap-2">

<input type="file" name="file" class="form-control">

<button class="btn btn-success">Upload</button>

</form>

</div>


<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>


<script>

var socket = io();

var username = "{{username}}";


socket.on("message", function(msg){

var chat=document.getElementById("chat");

if(msg.startsWith(username + ":")){

chat.innerHTML += "<div class='msg me'>" + msg + "</div>";

}else{

chat.innerHTML += "<div class='msg other'>" + msg + "</div>";

}

chat.scrollTop=chat.scrollHeight;

});


document.getElementById("msgForm").onsubmit=function(e){

e.preventDefault();

var msg=document.getElementById("msg").value;

socket.send(msg);

document.getElementById("msg").value="";

}

</script>

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

    return render_template("index.html",
                           username=session["user"],
                           messages=messages)


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
