import smtplib
import csv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

# CONFIGURATION
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT =465
SENDER_EMAIL = ''  # Your email
SENDER_PASSWORD = ""  # Use an App Password, not your main password
SUBJECT = "Email Trial"  # subject comes here


DELAY_SECONDS = 5  # Delay between each email

# Read CSV and send emails
with open("trial.csv", newline="", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        recipient_email = row["Email"]
        username = row["Username"]

        # Create the email
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = recipient_email
        msg["Subject"] = SUBJECT

        body = f"""
        Hello {username},

        This is a test email sent via Python.
        
        Followers count: {row['Followers']}

        Regards,
        Your Name
        """
        msg.attach(MIMEText(body, "plain"))

        try:
            # SSL connection (no starttls here)
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg)
                print(f"✅ Email sent to {recipient_email}")
        except Exception as e:
            print(f"❌ Failed to send email to {recipient_email}: {e}")

        # Delay between sends
        time.sleep(DELAY_SECONDS)