import os
import time
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import cv2
from ultralytics import YOLO
MODEL_PATH = "yolov8n.pt"
from dotenv import load_dotenv
model = YOLO(MODEL_PATH)

from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, Response, jsonify
from werkzeug.utils import secure_filename

from ai_module.core.detector import run_frame_processing

# ---------------- LOAD ENV ----------------
load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
RECEIVER_EMAILS = os.getenv("EMAIL_RECEIVERS", os.getenv("EMAIL_RECEIVER", "receiver_email@gmail.com"))
ENV_STANDARD_COUNT = int(os.getenv("STANDARD_COUNT", 50))

def get_standard_count(db):
    try:
        setting = db.settings.find_one({"key": "standard_count"})
        if setting:
            return int(setting.get("value", ENV_STANDARD_COUNT))
    except:
        pass
    return ENV_STANDARD_COUNT

# ---------------- INIT ----------------
main = Blueprint("main", __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "../static/uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

workers = []

# ---------------- GLOBAL STORAGE ----------------
uploaded_video_counts = {}
latest_alerts = []
last_alert_sent = {}   # prevent multiple emails


# ---------------- EMAIL FUNCTION ----------------
def send_email_alert(message):
    try:
        from dotenv import load_dotenv
        load_dotenv(override=True)
        
        user = os.getenv("EMAIL_USER")
        pw = os.getenv("EMAIL_PASS")
        receivers = os.getenv("EMAIL_RECEIVERS", os.getenv("EMAIL_RECEIVER", "receiver_email@gmail.com"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(user, pw)
        
        # Support multiple emails formatted as comma-separated string
        emails = [e.strip() for e in receivers.split(",") if e.strip()]
        
        for email in emails:
            print(f"📧 Attempting to alert: {email}")
            msg = MIMEText(message)
            msg["Subject"] = "🚨 Livestock Alert: Missing Animals!"
            msg["From"] = user
            msg["To"] = email
            server.sendmail(user, email, msg.as_string())
            print(f"✅ Email sent successfully to {email}")

        server.quit()
    except Exception as e:
        print("❌ Email error:", e)


# ---------------- HOME ----------------
@main.route("/")
def index():
    return render_template("index.html")


# ---------------- UPLOAD VIDEO ----------------
@main.route("/upload_video_ajax", methods=["POST"])
def upload_video_ajax():
    if "owner" not in session:
        return jsonify({"success": False, "error": "Not logged in"})

    if "video" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"})

    file = request.files["video"]
    filename = secure_filename(file.filename)

    if filename == "":
        return jsonify({"success": False, "error": "Empty filename"})

    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)

    duration = request.form.get("duration", "0")
    video_url = url_for('main.live_upload_stream', filename=filename, duration=duration)

    return jsonify({
        "success": True,
        "filename": filename,
        "video_url": video_url,
        "entry_count": 0,
        "total_count": 0
    })


# ---------------- LIVE VIDEO STREAM ----------------
@main.route("/live_upload_stream/<filename>")
def live_upload_stream(filename):
    if "owner" not in session:
        return "Unauthorized", 403
    video_path = os.path.abspath(os.path.join(UPLOAD_FOLDER, filename))

    duration = request.args.get("duration", "0")
    try:
        duration_mins = float(duration)
    except:
        duration_mins = 0

    if not os.path.exists(video_path):
        return "Video not found", 404

    db = current_app.db

    def generate():
        import time
        from datetime import datetime
        start_time = time.time()
        timeout_seconds = duration_mins * 60
        session_saved = False
        
        final_entry = 0
        final_total = 0

        try:
            for frame_bytes, entry_count, total_count in run_frame_processing(video_path):
                final_entry = entry_count
                final_total = total_count

                if duration_mins > 0 and (time.time() - start_time) > timeout_seconds:
                    break

                # ✅ Update counts
                uploaded_video_counts[filename] = {
                    "entry_count": entry_count,
                    "total_count": total_count
                }

                # ✅ Streaming frame
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        except Exception as e:
            if not isinstance(e, GeneratorExit):
                print("❌ Stream error:", e)
        finally:
            elapsed_mins = round((time.time() - start_time) / 60.0, 2)
            db.sessions.insert_one({
                "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": "Uploaded Video",
                "duration_mins": elapsed_mins,
                "entry_count": final_entry,
                "total_count": final_total
            })

            # Check Alert Condition at the end of the session!
            std_count = get_standard_count(db)
            missing = std_count - final_entry
            if missing > 0:
                alert_msg = f"⚠️ Session Ended: {missing} livestock missing! Expected {std_count}, Counted {final_entry}."
                if alert_msg not in latest_alerts:
                    latest_alerts.append(alert_msg)
                send_email_alert(alert_msg)

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


# ---------------- LIVE COUNTS API ----------------
@main.route("/live_counts")
def get_live_counts():
    filename = request.args.get("filename")

    if filename in uploaded_video_counts:
        return jsonify({
            "success": True,
            "entry_count": uploaded_video_counts[filename]["entry_count"],
            "total_count": uploaded_video_counts[filename]["total_count"]
        })

    return jsonify({"success": False})


# ---------------- ALERTS API ----------------
@main.route("/get_alerts")
def get_alerts():
    return jsonify({
        "success": True,
        "alerts": latest_alerts[-5:]
    })


# ---------------- SESSIONS API ----------------
@main.route("/get_sessions")
def get_sessions():
    if "owner" not in session:
        return jsonify({"success": False, "error": "Unauthorized"})
    
    sessions_list = list(current_app.db.sessions.find({}, {"_id": 0}).sort("_id", -1).limit(20))
    return jsonify({"success": True, "sessions": sessions_list})


# ---------------- STANDARD COUNT API ----------------
@main.route("/get_standard_count")
def get_std_count():
    if "owner" not in session:
        return jsonify({"success": False, "error": "Unauthorized"})
    
    count = get_standard_count(current_app.db)
    return jsonify({"success": True, "standard_count": count})


@main.route("/update_standard_count", methods=["POST"])
def update_std_count():
    if "owner" not in session:
        return jsonify({"success": False, "error": "Unauthorized"})
    
    try:
        new_count = int(request.form.get("standard_count", ENV_STANDARD_COUNT))
        current_app.db.settings.update_one(
            {"key": "standard_count"},
            {"$set": {"value": new_count}},
            upsert=True
        )
        return jsonify({"success": True, "new_count": new_count})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@main.route("/test_email_manual")
def test_email_manual():
    if "owner" not in session:
        return jsonify({"success": False, "error": "Unauthorized"})

    test_msg = "🔥 Manual SMTP Test: Your Livestock Monitoring System is successfully connected to the email server."
    try:
        send_email_alert(test_msg)
        return jsonify({"success": True, "message": "Test triggered. Check your console and inbox!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ---------------- DASHBOARDS ----------------
@main.route("/owner_dashboard")
def owner_dashboard():
    if "owner" not in session:
        return redirect(url_for("main.owner_login"))
    # Fetch count from DB settings if exists
    setting = current_app.db.settings.find_one({"key": "standard_count"})
    db_count = setting["value"] if setting else ENV_STANDARD_COUNT
    return render_template("owner_dashboard.html", workers=workers, standard_count=db_count)


@main.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.owner_login"))


@main.route("/worker_dashboard")
def worker_dashboard():
    if "worker" not in session:
        return redirect(url_for("main.worker_login"))
    return render_template("worker_dashboard.html")


# ---------------- AUTH ----------------
@main.route("/owner_register", methods=["GET", "POST"])
def owner_register():
    if request.method == "POST":
        data = request.form

        if current_app.db.owners.find_one({"email": data["email"]}):
            return "Owner already registered"

        current_app.db.owners.insert_one(dict(data))

        return redirect(url_for("main.owner_login"))

    return render_template("owner_register.html")


@main.route("/owner_login", methods=["GET", "POST"])
def owner_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # 🚀 Auto-seed default admin from .env if the database is empty or doesn't have an admin
        default_admin_email = os.getenv("OWNER_USERNAME")
        default_admin_pass = os.getenv("OWNER_PASSWORD")

        if email == default_admin_email:
            existing = current_app.db.owners.find_one({"email": email})
            if not existing:
                current_app.db.owners.insert_one({
                    "name": "Admin",
                    "email": default_admin_email,
                    "password": default_admin_pass,
                    "farm_name": "My Farm"
                })

        owner = current_app.db.owners.find_one({
            "email": email,
            "password": password
        })

        if owner:
            session["owner"] = owner["name"]
            return redirect(url_for("main.owner_dashboard"))

        return render_template("owner_login.html", error="Invalid Email or Password. Please try again.")

    return render_template("owner_login.html")


@main.route("/worker_login", methods=["GET", "POST"])
def worker_login():
    if request.method == "POST":
        for worker in workers:
            if worker["username"] == request.form["username"] and worker["password"] == request.form["password"]:
                session["worker"] = worker["username"]
                return redirect(url_for("main.worker_dashboard"))

    return render_template("worker_login.html")


@main.route("/add_worker", methods=["POST"])
def add_worker():
    if "owner" not in session:
        return redirect(url_for("main.owner_login"))

    username = request.form["username"]

    for w in workers:
        if w["username"] == username:
            return "Worker already exists"

    workers.append({
        "username": username,
        "password": request.form["password"]
    })

    return redirect(url_for("main.owner_dashboard"))
@main.route("/live_stream")
def live_stream():
    if "owner" not in session:
        return "Unauthorized", 403

    ip = request.args.get("ip")
    if not ip:
        return "IP not provided", 400

    duration = request.args.get("duration", "0")
    try:
        duration_mins = float(duration)
    except:
        duration_mins = 0

    db = current_app.db

    def generate():
        import time
        from datetime import datetime
        start_time = time.time()
        timeout_seconds = duration_mins * 60
        print("📡 Connecting to:", ip)

        cap = cv2.VideoCapture(ip)

        if not cap.isOpened():
            print("❌ Cannot open stream")
            return

        # SAME VARIABLES FROM YOUR WORKING CODE
        entry_count = 0
        counted_entry_ids = set()
        total_ids = set()
        track_states = {}

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    continue

                frame = cv2.resize(frame, (640, 480))

                results = model.track(
                    frame,
                    tracker="bytetrack.yaml",
                    persist=True,
                    conf=0.45,
                    classes=[0], # Cow
                    imgsz=640,
                    verbose=False
                )

                # ENTRY ZONE
                ENTRY_X1, ENTRY_Y1 = 300, 300
                ENTRY_X2, ENTRY_Y2 = 600, 450

                cv2.rectangle(frame, (ENTRY_X1, ENTRY_Y1),
                              (ENTRY_X2, ENTRY_Y2), (0, 0, 255), 2)

                if results[0].boxes.id is not None:
                    boxes = results[0].boxes.xyxy.cpu()
                    ids = results[0].boxes.id.cpu()

                    for box, track_id in zip(boxes, ids):
                        x1, y1, x2, y2 = map(int, box)
                        track_id = int(track_id)

                        total_ids.add(track_id)

                        cx = (x1 + x2) // 2
                        cy = (y1 + y2) // 2

                        inside = ENTRY_X1 < cx < ENTRY_X2 and ENTRY_Y1 < cy < ENTRY_Y2

                        if inside and track_id not in counted_entry_ids:
                            entry_count += 1
                            counted_entry_ids.add(track_id)

                        track_states[track_id] = inside

                        # DRAW
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, f"ID {track_id}",
                                    (x1, y1 - 8),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                if duration_mins > 0 and (time.time() - start_time) > timeout_seconds:
                    break

                # UPDATE COUNTS FOR DASHBOARD
                uploaded_video_counts[ip] = {
                    "entry_count": entry_count,
                    "total_count": len(total_ids)
                }

                # DISPLAY TEXT
                cv2.putText(frame, f"Entry: {entry_count}", (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                cv2.putText(frame, f"Total: {len(total_ids)}", (20, 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

                # ENCODE FRAME
                ret, jpeg = cv2.imencode('.jpg', frame)
                if not ret:
                    continue

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
                   
        except Exception as e:
            if not isinstance(e, GeneratorExit):
                print("❌ Stream error:", e)
        finally:
            elapsed_mins = round((time.time() - start_time) / 60.0, 2)
            db.sessions.insert_one({
                "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": "Live IP Camera",
                "duration_mins": elapsed_mins,
                "entry_count": entry_count,
                "total_count": len(total_ids)
            })

            # Check Alert Condition at the end of the session!
            std_count = get_standard_count(db)
            missing = std_count - entry_count
            if missing > 0:
                alert_msg = f"⚠️ Live Session Ended: {missing} livestock missing! Expected {std_count}, Counted {entry_count}."
                if alert_msg not in latest_alerts:
                    latest_alerts.append(alert_msg)
                send_email_alert(alert_msg)
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


# ---------------- SECURITY MODULE ----------------
@main.route("/security_stream")
def security_stream():
    if "owner" not in session:
        return "Unauthorized", 403

    ip = request.args.get("ip")
    if not ip:
        return "IP not provided", 400

    def generate():
        import time
        from datetime import datetime
        print("🛡️ Security Monitoring Active on:", ip)

        cap = cv2.VideoCapture(ip)
        if not cap.isOpened():
            print("❌ Cannot open security stream")
            return

        notified_intrusions = set()
        
        # DEFINE SECURITY ZONES (Rectangles - Scaled for 640x480)
        SEC_ZONE_1 = (0, 80, 180, 460)   # Left Restricted Area
        SEC_ZONE_2 = (460, 80, 640, 460) # Right Restricted Area

        def stream_logic():
            try:
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        continue

                    frame = cv2.resize(frame, (640, 480))

                    # Track Humans(0) and Cows(19)
                    results = model.track(
                        frame,
                        tracker="bytetrack.yaml",
                        persist=True,
                        conf=0.4,
                        classes=[0, 19], 
                        imgsz=640,
                        verbose=False
                    )

                    # Draw Security Zones (RED)
                    cv2.rectangle(frame, (SEC_ZONE_1[0], SEC_ZONE_1[1]), (SEC_ZONE_1[2], SEC_ZONE_1[3]), (0, 0, 255), 3)
                    cv2.putText(frame, "RESTRICTED: L", (SEC_ZONE_1[0]+5, SEC_ZONE_1[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)
                    
                    cv2.rectangle(frame, (SEC_ZONE_2[0], SEC_ZONE_2[1]), (SEC_ZONE_2[2], SEC_ZONE_2[3]), (0, 0, 255), 3)
                    cv2.putText(frame, "RESTRICTED: R", (SEC_ZONE_2[0]+5, SEC_ZONE_2[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)

                    if results[0].boxes.id is not None:
                        boxes = results[0].boxes.xyxy.cpu()
                        ids = results[0].boxes.id.cpu()
                        cls_ids = results[0].boxes.cls.cpu()

                        for box, track_id, cls_id in zip(boxes, ids, cls_ids):
                            x1, y1, x2, y2 = map(int, box)
                            track_id = int(track_id)
                            label = "Cow" if int(cls_id) == 19 else "Intruder"

                            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                            # Check intrusion in either zone
                            in_zone_1 = SEC_ZONE_1[0] < cx < SEC_ZONE_1[2] and SEC_ZONE_1[1] < cy < SEC_ZONE_1[3]
                            in_zone_2 = SEC_ZONE_2[0] < cx < SEC_ZONE_2[2] and SEC_ZONE_2[1] < cy < SEC_ZONE_2[3]

                            if (in_zone_1 or in_zone_2) and track_id not in notified_intrusions:
                                timestamp = datetime.now().strftime("%I:%M:%S %p")
                                alert_msg = f"🚨 SECURITY BREACH! {label} (ID {track_id}) entered restricted zone at {timestamp}."
                                
                                # Add to global alerts for dash view
                                if alert_msg not in latest_alerts:
                                    latest_alerts.append(alert_msg)
                                
                                # IMMEDIATE NOTIFICATION
                                send_email_alert(alert_msg)
                                notified_intrusions.add(track_id)

                            # DRAW ON FRAME
                            color = (0, 0, 255) if (in_zone_1 or in_zone_2) else (0, 255, 0)
                            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                            cv2.putText(frame, f"{label} ID {track_id}", (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                    ret, jpeg = cv2.imencode('.jpg', frame)
                    if not ret: continue
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

            except Exception as e:
                if not isinstance(e, GeneratorExit):
                    print("❌ Security stream error:", e)
            finally:
                cap.release()
        
        return stream_logic()

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')



@main.route("/live_counts_ip")
def live_counts_ip():
    ip = request.args.get("ip")
    if not ip:
        return jsonify({"success": False, "error": "IP not provided"})
    
    counts = uploaded_video_counts.get(ip, {"entry_count": 0, "total_count": 0})
    return jsonify({"success": True, **counts})