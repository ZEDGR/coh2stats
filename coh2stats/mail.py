from coh2stats.config import Config
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl

config = Config()

port = config.EMAIL_PORT
smtp_server = config.SMTP_SERVER
sender_email = config.SENDER_EMAIL
sender_password = config.SENDER_PASSWORD
receiver_email = config.RECEIVER_EMAIL


def send_error_mail(subject, message):
    msg = MIMEMultipart()
    msg['Subject'] = subject

    msg.attach(MIMEText(message, 'plain'))
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
