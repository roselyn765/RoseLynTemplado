from flask import Flask, jsonify, request, render_template_string, session, redirect
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret123"
DB = "students.db"


def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        grade INTEGER,
        section TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()


login_page = """
<html>
<head>
<title>Login</title>

<style>
body{
font-family:Arial;
background:linear-gradient(135deg,#FFC0CB,#FFB6C1);
display:flex;
justify-content:center;
align-items:center;
height:100vh;
color:white;
}

.box{
background:rgba(255,255,255,0.25);
padding:40px;
border-radius:15px;
backdrop-filter:blur(10px);
box-shadow:0 0 20px rgba(0,0,0,0.2);
}

input{
padding:10px;
margin:10px;
border:none;
border-radius:5px;
width:200px;
}

button{
padding:10px 20px;
border:none;
background:#FF69B4;
color:white;
border-radius:5px;
cursor:pointer;
font-weight:bold;
}

button:hover{
background:#FF1493;
}
</style>
</head>

<body>

<div class="box">

<h2>Admin Login</h2>

<form method="POST">

<input name="username" placeholder="Username"><br>
<input name="password" type="password" placeholder="Password"><br>

<button>Login</button>

</form>

</div>

</body>
</html>
"""


dashboard = """
<!DOCTYPE html>
<html>
<head>

<title>Student Manager</title>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<style>

body{
font-family:Arial;
background:linear-gradient(135deg,#FFC0CB,#FFB6C1);
color:white;
text-align:center;
padding:30px;
}

.container{
background:rgba(255,255,255,0.25);
padding:25px;
border-radius:15px;
width:750px;
margin:auto;
backdrop-filter:blur(10px);
box-shadow:0 0 20px rgba(0,0,0,0.2);
}

input{
padding:10px;
margin:5px;
border:none;
border-radius:5px;
}

button{
padding:8px 12px;
margin:4px;
border:none;
border-radius:5px;
cursor:pointer;
font-weight:bold;
}

.add{background:#FF69B4;color:white;}
.edit{background:#FFB6C1;color:black;}
.delete{background:#FF1493;color:white;}

table{
width:100%;
margin-top:20px;
border-collapse:collapse;
background:rgba(255,255,255,0.15);
}

th,td{
padding:10px;
border-bottom:1px solid rgba(255,255,255,0.3);
}

th{
background:rgba(255,255,255,0.25);
}

</style>

</head>

<body>

<h1>Student Manager</h1>

<div class="container">

<input id="search" placeholder="Search student..." onkeyup="searchStudent()">

<h3>Add / Edit Student</h3>

<input id="id" placeholder="ID (for update)">
<input id="name" placeholder="Name">
<input id="grade" placeholder="Grade">
<input id="section" placeholder="Section">

<br>

<button class="add" onclick="addStudent()">Add</button>
<button class="edit" onclick="updateStudent()">Update</button>

<h3>Students</h3>

<table id="table"></table>

<h3>Grade Chart</h3>

<canvas id="chart"></canvas>

</div>

<script>

let students=[]
let chart

function loadStudents(){

fetch('/students')
.then(res=>res.json())
.then(data=>{

students=data
drawTable(data)

let names=data.map(s=>s.name)
let grades=data.map(s=>s.grade)

drawChart(names,grades)

})

}

function drawTable(data){

let table=document.getElementById("table")

table.innerHTML=`
<tr>
<th>ID</th>
<th>Name</th>
<th>Grade</th>
<th>Section</th>
<th>Action</th>
</tr>
`

data.forEach(s=>{

table.innerHTML+=`
<tr>
<td>${s.id}</td>
<td>${s.name}</td>
<td>${s.grade}</td>
<td>${s.section}</td>
<td>
<button class="edit" onclick="fillForm(${s.id},'${s.name}','${s.grade}','${s.section}')">Edit</button>
<button class="delete" onclick="deleteStudent(${s.id})">Delete</button>
</td>
</tr>
`

})

}

function fillForm(id,name,grade,section){

document.getElementById("id").value=id
document.getElementById("name").value=name
document.getElementById("grade").value=grade
document.getElementById("section").value=section

}

function searchStudent(){

let q=document.getElementById("search").value.toLowerCase()

let filtered=students.filter(s=>s.name.toLowerCase().includes(q))

drawTable(filtered)

}

function drawChart(names,grades){

if(chart) chart.destroy()

chart=new Chart(document.getElementById("chart"),{
type:"bar",
data:{
labels:names,
datasets:[{
label:"Grade Level",
data:grades,
backgroundColor:"#FF69B4"
}]
}
})

}

function addStudent(){

fetch("/students",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({
name:document.getElementById("name").value,
grade:document.getElementById("grade").value,
section:document.getElementById("section").value
})
}).then(()=>loadStudents())

}

function updateStudent(){

let id=document.getElementById("id").value

fetch("/students/"+id,{
method:"PUT",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({
name:document.getElementById("name").value,
grade:document.getElementById("grade").value,
section:document.getElementById("section").value
})
}).then(()=>loadStudents())

}

function deleteStudent(id){

fetch("/students/"+id,{
method:"DELETE"
}).then(()=>loadStudents())

}

loadStudents()

</script>

</body>
</html>
"""


@app.route("/", methods=["GET","POST"])
def login():

    if request.method=="POST":

        if request.form["username"]=="admin" and request.form["password"]=="1234":
            session["user"]="admin"
            return redirect("/dashboard")

    return login_page


@app.route("/dashboard")
def home():

    if "user" not in session:
        return redirect("/")

    return render_template_string(dashboard)


@app.route("/students", methods=["GET"])
def get_students():

    conn=sqlite3.connect(DB)
    cur=conn.cursor()

    cur.execute("SELECT * FROM students")

    rows=cur.fetchall()

    conn.close()

    students=[{"id":r[0],"name":r[1],"grade":r[2],"section":r[3]} for r in rows]

    return jsonify(students)


@app.route("/students", methods=["POST"])
def add_student():

    data=request.get_json()

    conn=sqlite3.connect(DB)
    cur=conn.cursor()

    cur.execute(
        "INSERT INTO students(name,grade,section) VALUES(?,?,?)",
        (data["name"],data["grade"],data["section"])
    )

    conn.commit()
    conn.close()

    return jsonify({"message":"added"})


@app.route("/students/<int:id>", methods=["PUT"])
def update_student(id):

    data=request.get_json()

    conn=sqlite3.connect(DB)
    cur=conn.cursor()

    cur.execute(
        "UPDATE students SET name=?, grade=?, section=? WHERE id=?",
        (data["name"],data["grade"],data["section"],id)
    )

    conn.commit()
    conn.close()

    return jsonify({"message":"updated"})


@app.route("/students/<int:id>", methods=["DELETE"])
def delete_student(id):

    conn=sqlite3.connect(DB)
    cur=conn.cursor()

    cur.execute("DELETE FROM students WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return jsonify({"message":"deleted"})


if __name__ == "__main__":

    port=int(os.environ.get("PORT",5000))

    app.run(host="0.0.0.0",port=port)
