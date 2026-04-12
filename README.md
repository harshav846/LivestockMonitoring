# 🐄 Smart Livestock Monitoring AI System

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-FF2D20?style=flat&logo=yolo&logoColor=white)](https://github.com/ultralytics/ultralytics)
[![MongoDB](https://img.shields.io/badge/MongoDB-Cloud-47A248?style=flat&logo=mongodb&logoColor=white)](https://www.mongodb.com/)

An advanced AI-powered livestock monitoring and security system designed for modern farm management. This platform leverages Computer Vision (YOLOv8) to track livestock, count cattle, and detect unauthorized intrusions in real-time.

---

## 🌟 Key Features

-   **🎥 Real-Time Monitoring**: Support for high-definition video uploads and Live IP Camera streams (compatible with IP Webcam mobile apps).
-   **📈 Intelligent Counting**: Automated livestock counting using **YOLOv8** and **ByteTrack**, tracking animals as they enter specific grazing or feeding zones.
-   **🛡️ Security Module**: Advanced intrusion detection system that identifies humans in restricted areas and triggers immediate security protocols.
-   **📧 Automated Alerts**: Instant SMTP email notifications for:
    *   Missing livestock (when counts fall below standard).
    *   Security breaches (intruder detection).
-   **📊 Dual Dashboards**:
    *   **Owner Dashboard**: Full administrative control, session history, worker management, and alert logs.
    *   **Worker Dashboard**: Simplified interface for monitoring daily livestock movement.
-   **💾 Cloud Integration**: Robust data persistence using **MongoDB** for session logs, livestock counts, and user authentication.

---

## 🏗️ Tech Stack

-   **Backend**: Flask (Python)
-   **AI Integration**: YOLOv8 (Ultralytics), OpenCV
-   **Database**: MongoDB Atlas
-   **Frontend**: HTML5, Vanilla CSS, JavaScript (AJAX)
-   **Deployment**: Render / Gunicorn / Waitress

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.9 or higher
- MongoDB Atlas account (for cloud database)
- Gmail account (for SMTP alerts)

### 2. Installation
Clone the repository and install the dependencies:
```bash
git clone https://github.com/yourusername/LivestockMonitoring.git
cd LivestockMonitoring
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory and add the following:
```env
SECRET_KEY=your_secret_key_here
MONGO_URI=your_mongodb_connection_string
EMAIL_USER=your_gmail@gmail.com
EMAIL_PASS=your_app_password
EMAIL_RECEIVERS=receiver1@gmail.com,receiver2@gmail.com
STANDARD_COUNT=50
OWNER_USERNAME=admin@farm.com
OWNER_PASSWORD=securepassword
```
> [!NOTE]
> For Gmail SMTP, you must use an **App Password** instead of your regular password.

### 4. Running Locally
```bash
python run.py
```
Access the application at `http://127.0.0.1:5000`.

---

## 🌐 Deployment (Render)

The project is pre-configured for deployment on **Render**.

1. Create a new **Web Service** on Render.
2. Select your repository.
3. Use the following settings:
    - **Build Command**: `./render-build.sh`
    - **Start Command**: `gunicorn run:app`
4. Add all environment variables from your `.env` to the Render Dashboard.

---

## 📁 Project Structure

```text
├── ai_module/          # AI Logic (YOLOv8, Tracking, Core processing)
├── app/                # Flask Application (Routes, Models, Services)
│   ├── templates/      # Jinja2 HTML Templates
│   └── routes.py       # Main application routes & API endpoints
├── static/             # Static assets (CSS, JS, Uploads)
├── yolov8n.pt          # YOLOv8 Weights
├── Procfile            # Deployment configuration
├── render-build.sh     # Build script for production
└── run.py              # Application entry point
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*Developed with ❤️ for the Agricultural Technology community.*
