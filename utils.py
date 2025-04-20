# utils.py
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL, PASSWORD

# Generate a 4-digit OTP
def generate_otp():
    return str(random.randint(1000, 9999))

# Send OTP to email
def send_otp(receiver_email, otp):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL
        msg['To'] = receiver_email
        msg['Subject'] = "Your Quiznix OTP Code"

        body = f"Hello,\n\nYour OTP code is: {otp}\n\nDon't share this code.\n\n- Quiznix Team"
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL, PASSWORD)
        server.sendmail(EMAIL, receiver_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Error sending OTP:", e)
        return False

# Verify OTP entered by user
def verify_entered_otp(user_otp, actual_otp):
    return user_otp == actual_otp