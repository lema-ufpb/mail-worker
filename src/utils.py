import os
import json
from typing import Tuple, Union, List
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from src import logger



def create_email_message(data: dict) -> Tuple[str, str, Union[str, bool]]:
    """Creates email message based on provided data.

    Args:
        data: Dictionary containing email data.

    Returns:
        Tuple containing sender, subject, and email body. Returns False for body if data is invalid.
    """
    sender = ''
    subject = ''
    action = data.get('action')

    if not data or not action:  
        return sender, subject, False

    body = read_email_template(action=action, form=data)

    if body is False:  
        return sender, subject, False

    sender = f"{os.getenv('SMTP_SENDER_NAME')} <{os.getenv('SMTP_SENDER')}>"

    if action == 'pin-code':
        subject = f"{data.get('pin')} é o seu código de acesso"
    elif action == 'user-contact':
        subject = f"Contato de Usuário - {data.get('id')}"
    else:
        subject = ""  

    return sender, subject, body


def send_email(data: dict) -> None:
    """Sends an email.

    Args:
        data: Dictionary containing email data.
    """
    try:
        sender, subject, body = create_email_message(data)

        if not body:
            logger.info("No valid email data or template.")
            return

        recipients: List[str] = [data.get('email')] if data.get(
            'action') == 'pin-code' and data.get('email') else []
        if data.get('action') == 'user-contact':
            recipients_str = os.getenv('MAIL_RECEPTORS')
            if recipients_str:
                try:
                    recipients = json.loads(recipients_str)
                except json.JSONDecodeError:
                    logger.error(
                        "Invalid JSON in MAIL_RECEPTORS environment variable.")
                    return

        if not recipients:  
            logger.warning("No recipients specified for email.")
            return

        msg = MIMEMultipart('alternative')
        msg['From'] = sender
        msg['Subject'] = subject
        msg['To'] = ', '.join(recipients)
        msg.attach(MIMEText(body, 'html'))

        with smtplib.SMTP(host=os.getenv('SMTP_HOST'), port=int(os.getenv('SMTP_PORT', 587))) as server:
            server.starttls()
            server.login(os.getenv('SMTP_USERNAME'),
                         os.getenv('SMTP_PASSWORD'))

            logger.info(f"Sending email to {', '.join(recipients)}")
            server.sendmail(sender, recipients, msg.as_string())
            logger.info(f"Email related to {data.get('id')} sent successfully")

    except smtplib.SMTPConnectError as e:
        logger.error(f"SMTP connection error: {e}", exc_info=True)
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error sending email: {e}", exc_info=True)


def read_email_template(action: str, form: dict) -> Union[str, bool]:
    """Reads and returns the email template.

    Args:
        action: The action associated with the template.
        form: Dictionary containing data to populate the template.

    Returns:
        The email template string, or False if the template file is not found.
    """
    template_path = f"src/templates/{action}.html"
    try:
        with open(template_path, 'r', encoding='utf-8') as file:
            template = file.read()

        if action == 'pin-code':
            template = template.replace('{{pin}}', str(
                form.get('pin', ''))) 
        elif action == 'user-contact':
            template = template.replace('{{name}}', str(form.get('name', '')))
            template = template.replace(
                '{{email}}', str(form.get('email', '')))
            template = template.replace(
                '{{message}}', str(form.get('message', '')))

        return template
    except FileNotFoundError:
        logger.error(f"Template file not found: {template_path}")
        return False


def validate_email_config() -> None:
    """Validates required email configuration."""
    required_vars = [
        'SMTP_HOST',
        'SMTP_PORT',
        'SMTP_USERNAME',
        'SMTP_PASSWORD',
        'SMTP_SENDER',
        'MAIL_RECEPTORS'  # Added MAIL_RECEPTORS
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}")
