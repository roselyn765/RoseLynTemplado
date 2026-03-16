from flask import Flask, jsonify, request, render_template_string, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secretkey123"


# DATABASE
def init_db():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        grade TEXT,
        section TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()


# LOGIN PAGE
@app.route("/")
def login_page():
    if "user" in session:
        return redirect("/dashboard")

    return render_template_string("""

<h2>Login</h2>

<input id="user" placeholder="Username"><br><br>
<input id="pass" type="password" placeholder="Password"><br><br>

<button onclick="login()">Login</button>
<button onclick="register()">Register</button>

<script>

function login(){

fetch('/login',{
method:'POST',
headers:{'Content-Type':'application/json'},
body:JSON.stringify({
username:document.getElementById("user").value,
password:document.getElementById("pass").value
})
})
.then(res=>res.json())
.then(data=>{
alert(data.message)
if(data.success){
location.href='/dashboard'
}
})

}

function register(){

fetch('/register',{
method:'POST',
headers:{'Content-Type':'application/json'},
body:JSON.stringify({
username:document.getElementById("user").value,
password:document.getElementById("pass").value
})
})
.then(res=>res.json())
.then(data=>{
alert(data.message)
})

}

</script>

""")


# REGISTER
@app.route("/register", methods=["POST"])
def register():
    data = request.json

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("INSERT INTO users(username,password) VALUES(?,?)",
                (data["username"], data["password"]))

    conn.commit()
    conn.close()

    return jsonify({"message":"Registered successfully"})


# LOGIN
@app.route("/login", methods=["POST"])
def login():

    data = request.json

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE username=? AND password=?",
                (data["username"], data["password"]))

    user = cur.fetchone()

    conn.close()

    if user:
        session["user"] = user[1]
        return jsonify({"success":True,"message":"Login successful"})
    else:
        return jsonify({"success":False,"message":"Invalid login"})


# DASHBOARD
@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/")

    return render_template_string("""

<h1>Student Management Dashboard</h1>

<button onclick="logout()">Logout</button>

<h3>Add Student</h3>

<input id="name" placeholder="Name">
<input id="grade" placeholder="Grade">
<input id="section" placeholder="Section">

<button onclick="addStudent()">Add</button>

<br><br>

<input id="search" placeholder="Search student">
<button onclick="searchStudent()">Search</button>
<button onclick="loadStudents()">Refresh</button>

<table border="1" width="60%">
<thead>
<tr>
<th>ID</th>
<th>Name</th>
<th>Grade</th>
<th>Section</th>
<th>Action</th>
</tr>
</thead>

<tbody id="table"></tbody>

</table>


<script>

function loadStudents(){

fetch('/students')
.then(res=>res.json())
.then(data=>{

let table=document.getElementById("table")
table.innerHTML=""

data.forEach(s=>{

table.innerHTML+=`
<tr>
<td>${s.id}</td>
<td>${s.name}</td>
<td>${s.grade}</td>
<td>${s.section}</td>
<td>
<button onclick="deleteStudent(${s.id})">Delete</button>
</td>
</tr>
`

})

})

}


function addStudent(){

fetch('/add_student',{
method:'POST',
headers:{'Content-Type':'application/json'},
body:JSON.stringify({
name:document.getElementById("name").value,
grade:document.getElementById("grade").value,
section:document.getElementById("section").value
})
})
.then(res=>res.json())
.then(data=>{
alert(data.message)
loadStudents()
})

}


function deleteStudent(id){

fetch('/delete/'+id,{
method:'DELETE'
})
.then(res=>res.json())
.then(data=>{
alert(data.message)
loadStudents()
})

}


function searchStudent(){

let name=document.getElementById("search").value

fetch('/search?name='+name)
.then(res=>res.json())
.then(data=>{

let table=document.getElementById("table")
table.innerHTML=""

data.forEach(s=>{

table.innerHTML+=`
<tr>
<td>${s.id}</td>
<td>${s.name}</td>
<td>${s.grade}</td>
<td>${s.section}</td>
<td>-</td>
</tr>
`

})

})

}


function logout(){
location.href="/logout"
}

loadStudents()

</script>

""")


# GET STUDENTS
@app.route("/students")
def students():

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM students")
    rows = cur.fetchall()

    conn.close()

    return jsonify([dict(row) for row in rows])


# ADD STUDENT
@app.route("/add_student", methods=["POST"])
def add_student():

    data = request.json

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("INSERT INTO students(name,grade,section) VALUES(?,?,?)",
                (data["name"],data["grade"],data["section"]))

    conn.commit()
    conn.close()

    return jsonify({"message":"Student added"})


# DELETE
@app.route("/delete/<int:id>", methods=["DELETE"])
def delete_student(id):

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("DELETE FROM students WHERE id=?",(id,))

    conn.commit()
    conn.close()

    return jsonify({"message":"Student deleted"})


# SEARCH
@app.route("/search")
def search():

    name = request.args.get("name")

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM students WHERE name LIKE ?",('%'+name+'%',))
    rows = cur.fetchall()

    conn.close()

    return jsonify([dict(row) for row in rows])


# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
