import os
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app


main = Blueprint("main", __name__)

@main.route("/")
def index():
    return render_template("index.html")
@main.route("/owner_login", methods=["GET", "POST"])
def owner_login():
    return render_template("owner_login.html")

@main.route("/worker_login", methods=["GET", "POST"])
def worker_login():
    return render_template("worker_login.html")
@main.route("/owner_dashboard")
def owner_dashboard():
    return render_template("owner_dashboard.html")

@main.route("/worker_dashboard")
def worker_dashboard():
    return render_template("worker_dashboard.html")
@main.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


# ---------------- OWNER LOGIN ----------------
@main.route("/owner_login", methods=["GET", "POST"])
def owner_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if (username == os.getenv("OWNER_USERNAME") and
                password == os.getenv("OWNER_PASSWORD")):

            session["owner"] = username
            return redirect(url_for("main.owner_dashboard"))

    return render_template("owner_login.html")
# ---------------- WORKER CREATION ----------------
@main.route("/add_worker", methods=["POST"])
def add_worker():
    if "owner" not in session:
        return redirect(url_for("main.owner_login"))

    username = request.form["username"]
    password = request.form["password"]

    current_app.db.worker.insert_one({
        "username": username,
        "password": password
    })

    return redirect(url_for("main.owner_dashboard"))
# ---------------- WORKER LOGIN ----------------
@main.route("/worker_login", methods=["GET", "POST"])
def worker_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        worker = current_app.db.worker.find_one({
            "username": username,
            "password": password
        })

        if worker:
            session["worker"] = username
            return redirect(url_for("main.worker_dashboard"))

    return render_template("worker_login.html")