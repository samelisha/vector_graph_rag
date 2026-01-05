import smtplib
from email.message import EmailMessage
from config import (
    GMAIL_ADDRESS,
    GMAIL_APP_PASSWORD,
    SMTP_SERVER,
    SMTP_PORT,
)

def send_email(to_address, subject, body):
    msg = EmailMessage()
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.send_message(msg)

