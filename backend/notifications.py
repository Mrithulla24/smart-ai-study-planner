import os
import smtplib
from email.message import EmailMessage


def send_email(to_email, subject, body):
    host = os.getenv('SMTP_HOST', '')
    port = int(os.getenv('SMTP_PORT', '587'))
    username = os.getenv('SMTP_USERNAME', '')
    password = os.getenv('SMTP_PASSWORD', '')
    sender = os.getenv('SMTP_FROM', username)
    use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'

    if not all([host, username, password, sender]):
        raise RuntimeError('Email is not configured. Add SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD and SMTP_FROM to .env.')

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to_email
    msg.set_content(body)

    with smtplib.SMTP(host, port, timeout=20) as server:
        if use_tls:
            server.starttls()
        server.login(username, password)
        server.send_message(msg)


def send_sms(to_number, message):
    sid = os.getenv('TWILIO_ACCOUNT_SID', '')
    token = os.getenv('TWILIO_AUTH_TOKEN', '')
    from_number = os.getenv('TWILIO_FROM_NUMBER', '')

    if not all([sid, token, from_number]):
        raise RuntimeError('SMS is not configured. Add Twilio credentials to .env.')

    try:
        from twilio.rest import Client
    except ImportError:
        raise RuntimeError('SMS support requires the twilio package. Run: pip install twilio')

    client = Client(sid, token)
    client.messages.create(body=message, from_=from_number, to=to_number)
