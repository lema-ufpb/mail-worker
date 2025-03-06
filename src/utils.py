from os import environ, getenv, listdir, path
from json import loads, JSONDecodeError
from yaml import safe_load
from typing import Tuple, Union, List
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from src import logger
from dotenv import dotenv_values


def local_environment() -> None:
    """ Handle vars for development environment only """
    config = {
        **dotenv_values(".env"),
        **dotenv_values(".env.secrets"),
    }
    if config.get('SERVER') != 'production':
        for k, value in config.items():
            environ[k] = value


def get_template_filenames(template_dir="src/templates"):
    """Returns a list of template filenames in the given directory."""
    try:
        filenames = [f.replace(".html", "") for f in listdir(
            template_dir) if path.isfile(path.join(template_dir, f))]
        return filenames
    except FileNotFoundError:
        logger.error(f"Template directory not found: {template_dir}")
        return []


def handle_actions(data: dict) -> None:
    """Handles actions based on provided data.
    Args
    data: Dictionary containing data to process.
    """
    actions = get_template_filenames()
    if len(actions) == 0:
        logger.error("No templates found.")
        return

    action_id = data.get('id')

    if action_id not in actions:
        logger.error(f"Unknown action: {action_id}")
        return

    send_email(data)


def read_email_template(form: dict) -> Union[str, bool]:
    """Reads and returns the email template.

    Args:
        action: The action associated with the template.
        form: Dictionary containing data to populate the template.

    Returns:
        The email template string, or False if the template file is not found.
    """
    action_id = form.get('id')
    template_path = f"src/templates/{action_id}.html"
    config_path = f"src/config/{action_id}.yml"
    try:
        if not path.exists(template_path):
            logger.error(f"Template file not found: {template_path}")
            return False
        if not path.exists(config_path):
            logger.error(f"Config file not found: {config_path}")
            return False

        with open(config_path, 'r', encoding='utf-8') as file:
            config = safe_load(file)
        with open(template_path, 'r', encoding='utf-8') as file:
            template = file.read()

        if config and isinstance(config.get('params'), list):
            for param in config['params']:
                value = str(form.get(param, ''))
                template = template.replace(f'|{param}|', value)

        if config and isinstance(config.get('body'), dict):
            for key, value in config['body'].items():
                template = template.replace(f'|{key}|', value)
        return template, config
    except FileNotFoundError:
        logger.error(f"Template file not found: {template_path}")
        return False


def create_email_message(data: dict) -> Tuple[str, str, Union[str, bool]]:
    """Creates email message based on provided data.

    Args:
        data: Dictionary containing email data.

    Returns:
        Tuple containing sender, subject, and email body. Returns False for body if data is invalid.
    """
    local_environment()
    sender = ''
    subject = ''

    body, config = read_email_template(form=data)

    if body is False:
        return sender, subject, False

    sender = f"{getenv('SMTP_SENDER_NAME')} <{getenv('SMTP_SENDER')}>"
    if config and isinstance(config.get('body'), dict):
        subject = config['body'].get('title', '')
    else:
        return sender, subject, False

    return sender, subject, body


def send_email(data: dict) -> None:
    """Sends an email.

    Args:
        data: Dictionary containing email data.
    """
    try:
        local_environment()
        sender, subject, body = create_email_message(data)

        if not body:
            logger.info("No valid email data or template.")
            return

        recipients: List[str] = [data.get('email')] if data.get(
            'email') else []

        if len(recipients) == 0:
            recipients_str = getenv('MAIL_RECEPTORS')
            if recipients_str:
                try:
                    recipients += loads(recipients_str)
                except JSONDecodeError:
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

        with smtplib.SMTP(host=getenv('SMTP_HOST'), port=int(getenv('SMTP_PORT', 587))) as server:
            server.starttls()
            server.login(getenv('SMTP_USERNAME'),
                         getenv('SMTP_PASSWORD'))

            logger.info(f"Sending email to {', '.join(recipients)}")
            server.sendmail(sender, recipients, msg.as_string())
            logger.info(f"Email related to {data.get('id')} sent successfully")

    except smtplib.SMTPConnectError as e:
        logger.error(f"SMTP connection error: {e}", exc_info=True)
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error sending email: {e}", exc_info=True)


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

    missing_vars = [var for var in required_vars if not getenv(var)]

    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}")
