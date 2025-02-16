
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr


EMAIL_ADDRESS  = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER')
SMTP_PORT   = int(os.getenv('EMAIL_SMTP_PORT'))

IMAP_SERVER = os.getenv('EMAIL_IMAP_SERVER')
IMAP_PORT   = int(os.getenv('EMAIL_IMAP_PORT'))


def send_email(to_address: str, subject: str, body: str, sender_name: str = 'backoffice', from_address: str = EMAIL_ADDRESS) -> None:
    # Create the email message
    message = MIMEMultipart()
    message['From']    = formataddr((sender_name, from_address))
    message['To']      = to_address
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    # Send the message
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(message)

