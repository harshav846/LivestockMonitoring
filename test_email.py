import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
RECEIVER_EMAILS = os.getenv("EMAIL_RECEIVERS", "receiver_email@gmail.com")

def test_email():
    print(f"📡 Testing SMTP with User: {EMAIL_USER}")
    print(f"📩 Target Recipient(s): {RECEIVER_EMAILS}")

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        
        emails = [e.strip() for e in RECEIVER_EMAILS.split(",") if e.strip()]
        
        for email in emails:
            msg = MIMEText("This is a test alert from the Livestock Monitoring System!")
            msg["Subject"] = "🧪 TEST ALERT"
            msg["From"] = EMAIL_USER
            msg["To"] = email
            server.sendmail(EMAIL_USER, email, msg.as_string())
            print(f"✅ Success! Test email sent to {email}")

        server.quit()
    except Exception as e:
        print(f"❌ SMTP Error: {e}")

if __name__ == "__main__":
    test_email()
