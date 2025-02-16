# api/lib/mail.py
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER')
SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', '465'))

def send_email(to_address: str, subject: str, body: str, sender_name: str = 'Course Platform') -> None:
    print(f"Attempting to send email to: {to_address}")
    print(f"Using SMTP server: {SMTP_SERVER}:{SMTP_PORT}")
    
    if not all([EMAIL_ADDRESS, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT]):
        raise ValueError(
            "Email configuration missing. Need EMAIL_ADDRESS, EMAIL_PASSWORD, "
            "EMAIL_SMTP_SERVER, and EMAIL_SMTP_PORT in environment variables."
        )

    # Create the email message
    message = MIMEMultipart()
    message['From'] = formataddr((sender_name, EMAIL_ADDRESS))
    message['To'] = to_address
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    try:
        # Send the message
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            print("Connected to SMTP server")
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            print("Logged in successfully")
            server.send_message(message)
            print(f"Email sent successfully to {to_address}")
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        raise