import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import re
from settings import logger, SMTP


def send_email(from_, to_, subject, body_text, body_html):
    if not from_:
        from_ = SMTP["default_sender"]
    if not re.match(r"[^@]+@[^@]+\.[^@]+", from_) or not re.match(r"[^@]+@[^@]+\.[^@]+", to_):
        logger.error("Invalid email address from {} -- to {}".format(from_, to_))
        return False

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_
    msg['To'] = to_

    # Record the MIME types of both parts - text/plain and text/html.
    parts = []
    if body_text:
        parts.append(MIMEText(body_text, 'plain'))
    if body_html:
        parts.append(MIMEText(body_html, 'html'))

    for part in parts:
        msg.attach(part)

    logger.warning("EMAIL: " + msg.as_string())
    return True
    
    server = smtplib.SMTP_SSL(SMTP["host"], SMTP["port"])
    server.ehlo()
    server.login(SMTP["user"], SMTP["password"])
    server.sendmail(from_, to_, msg.as_string())
    server.close()
