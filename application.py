import os

from flask import Flask, session,render_template,request, redirect, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests



app = Flask(__name__)

# Check for environment variable

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine("postgres://kielmddlqwfpun:2b8e475804e406eeb85a9e82df12706df6b790385d98e706d6caa32c46ad62c6@ec2-54-165-36-134.compute-1.amazonaws.com:5432/d86s0803c05qhc")
db = scoped_session(sessionmaker(bind=engine))


@app.route("/", methods=["POST","GET"])
def index():
    return render_template("notlog.html")


@app.route("/about", methods=["GET"])
def about():
    return render_template("about.html")

@app.route("/jobs", methods=["GET"])
def jobs():
    data = db.execute("select * from jobs").fetchall()
    count = len(data)
    return render_template("jobs.html", count = count, data = data)

@app.route("/apply", methods=["GET", "POST"])
def apply():
    if "login" not in session:
        return redirect("/login")
    if session["login"] == 0:
        return redirect("/login")
    if session["name"] == "admin":
        return redirect("/admin")
    else:
        data = db.execute("select * from jobs").fetchall()
        count = len(data)
        return render_template("apply.html", count=count, data= data)#todo

@app.route("/logout")
def logout():
    session["login"] = 0
    session["name"] = ""
    return redirect("/")

@app.route("/register", methods=["POST","GET"] )
def register():
    if request.method == "GET":
        return render_template("register.html", message = "If already a member try logging in", login = 0)
    else:
        name = request.form.get("username")
        password = request.form.get("password")
        if db.execute("select * from users where name=:name",{"name": name}).rowcount != 0:
            return render_template("register.html", message = "username is used", login = 0)
        elif password == None:
            return render_template("register.html", message = "at least put some effort in password", login = 0)
        else:
            db.execute("insert into users (name, password) values (:name,:password)",{"name":name,"password":password})
            db.commit()
            session["login"] = 1
            session["name"] = name

            return redirect("/apply")

@app.route("/login", methods=["POST","GET"])
def login():
    if request.method == "GET":
        return render_template("register.html", message = "enter your username", login = 1)
    else:
        name = request.form.get("username")
        password = request.form.get("password")
        db.commit()
        data = db.execute("select * from users where name=:name and password = :password",{"name": name,"password":password}).rowcount == 0
        if data:
            db.commit()
            return render_template("register.html", message = "username/password is incorrect", login = 1)
        else:
            session["login"] = 1
            session["name"] = name
            return redirect("/apply")

@app.route("/process", methods = ["POST","GET"])
def process():
    if request.method == "GET":
        return redirect("/apply")
    else:
        email = request.form.get("email")
        name = session["name"]
        title = request.form.get("title")
        description = request.form.get("description")
        if not title or not email or not description:
            return redirect("/apply")
        count = db.execute("select * from applicant where name = :name and title = :title",{"name":name,"title":title}).rowcount
        if count != 0:
            db.execute("update applicant set email = :email, description= :description where name = :name and title = :title",{"name":name,"title":title,"email":email,"description":description})
            db.commit()
            return redirect("/status")
        db.execute("insert into applicant (name,title,description,email,status) values (:name,:title,:description,:email,0)",{"name":name, "title":title, "description":description, "email":email})
        db.commit()
        return redirect("/status")


@app.route("/admin_process", methods = ["POST","GET"])
def admin_process():
    if request.method == "GET":
        return redirect("/admin")
    else:
        appnum = request.form.get("appnum")
        status = request.form.get("status")
        title = request.form.get("title")
        if not title or not appnum or not status:
            return redirect("/admin")
        count = db.execute("select * from applicant where id = :appnum and title = :title",{"appnum":appnum,"title":title}).rowcount
        if count == 0:
            return redirect("/admin")
        db.execute("update applicant set status = :status where id = :appnum and title = :title",{"appnum":appnum, "title":title, "status":status})
        db.commit()
        return redirect("/admin")

@app.route("/perk", methods=["POST","GET"])
def perk():
    return render_template("perk.html")

@app.route("/status", methods=["POST","GET"])
def status():
    data = db.execute("select * from applicant where name = :name",{"name":session["name"]}).fetchall()
    return render_template("status.html", data = data, count = len(data))

@app.route("/admin", methods=["POST","GET"])
def admin():
    data = db.execute("select * from applicant where status = '0'").fetchall()
    return render_template("admin.html", data = data, count = len(data))

@app.route("/admin_jobs", methods = ["POST","GET"])
def admin_jobs():
    if request.method == "GET":
        data = db.execute("select * from jobs").fetchall()
        count = len(data)
        return render_template("admin_jobs.html", count = count, data = data)
    else:
        title = request.form.get("title")
        addtitle = request.form.get("addtitle")
        description = request.form.get("description")
        deadline = request.form.get("deadline")
        if (not description or not deadline) and description.lower() != "remove":
            return redirect("/admin_jobs")
        if addtitle:
            db.execute("insert into jobs (title,deadline,description) values (:title,:deadline,:description)",{"title":addtitle,"description":description,"deadline":deadline})
            db.commit()
            return redirect("/admin_jobs")
        elif title:
            if description.lower()=="remove":
                db.execute("delete from jobs where title = :title",{"title":title})
                db.commit()
            else:
                db.execute("update jobs set description = :description, deadline = :deadline where title = :title",{"title":title,"description":description,"deadline":deadline} )
                db.commit()
            return redirect("/admin_jobs")
        return redirect("/admin_jobs")
