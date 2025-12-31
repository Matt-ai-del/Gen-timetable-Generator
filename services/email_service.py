import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import streamlit as st

logger = logging.getLogger(__name__)


def send_feedback_email(user_email: str | None, message: str) -> bool:
    """Send user feedback to the configured admin inbox via SMTP."""
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    sender_email = 'matthewkasango@gmail.com'
    sender_password = 'wfxg alzt djek mjgp'
    receiver_email = 'matthewkasango@gmail.com'

    if not message or not message.strip():
        st.error("Feedback message cannot be empty")
        return False

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = 'MSU Timetable System Feedback'
    body = f"Feedback from: {user_email or 'Anonymous'}\n\n{message}"
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        logger.info("Feedback email sent successfully")
        return True
    except smtplib.SMTPException as exc:
        error_message = f"Failed to send feedback: {exc}"
        logger.error(error_message)
        st.error(error_message)
        return False
    except Exception as exc:
        error_message = f"An unexpected error occurred: {exc}"
        logger.error(error_message)
        st.error(error_message)
        return False
