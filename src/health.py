# -*- coding: UTF-8 -*-
"""Health check module for mail-worker service"""
import sys
import os
import time
from pika import BlockingConnection, URLParameters, exceptions
from urllib.parse import urlparse
from src import logger

RETRY_DELAY = 5  # seconds
MAX_RETRIES = 3


def get_broker_url():
    """Constructs the broker URL from environment variables."""
    try:
        url = os.environ.get("BROKER_URL")

        if url:
            # Use BROKER_URL if provided
            parsed_url = urlparse(url)
            if not all([parsed_url.hostname, parsed_url.username, parsed_url.password]):
                raise ValueError(
                    "Invalid BROKER_URL. Must include hostname, username, and password. Provided: " + url)
            return url
        else:
            # Fallback to individual components
            username = os.environ.get("BROKER_USERNAME")
            password = os.environ.get("BROKER_PASSWORD")
            host = os.environ.get("BROKER_HOST")
            port = os.environ.get("BROKER_PORT", 5672) # Default to 5672 if not provided
            if not all([username, password, host]):
                raise ValueError(
                    "Missing required environment variables: BROKER_USERNAME, BROKER_PASSWORD, and BROKER_HOST or BROKER_URL.")
            return f'amqp://{username}:{password}@{host}:{port}'

    except ValueError as e:
        raise e


def check_broker_connection():
    """Checks connection to message broker with retries."""

    retries = 0
    while retries < MAX_RETRIES:
        try:
            url = get_broker_url()

            # Attempt connection with a timeout
            connection = BlockingConnection(URLParameters(url), heartbeat=60)

            if connection.is_open:
                logger.info("Successfully connected to message broker")
                connection.close()
                return True
            else:
                logger.error("Failed to open connection to message broker.")
                return False  # Explicitly return False if connection is not open

        except exceptions.AMQPConnectionError as e:
            logger.error(f"Failed to connect to message broker: {e}")
            retries += 1
            if retries < MAX_RETRIES:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
        except ValueError as e:
            logger.error(f"Invalid Broker URL: {e}")
            return False # Exit on invalid URL
        except Exception as e:
            logger.exception(f"Unexpected error occurred: {e}")
            return False

    return False # Return False after all retries fail


def main():
    """Main health check function"""
    if check_broker_connection():
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

