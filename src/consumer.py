"""Message queue consumer for email notification processing"""
import os
import json
import time
import traceback
import pika
import backoff
from src import logger
from src.utils import set_environment, handle_actions
from pika.adapters.blocking_connection import BlockingChannel

# Configuration should ideally be separated from the main code
RETRY_INTERVAL = int(os.getenv("RETRY_INTERVAL", 15))
QUEUE_NAME = os.getenv("QUEUE_NAME", "tasks")
PREFETCH_COUNT = int(os.getenv("PREFETCH_COUNT", 1))


def create_connection(broker_url: str) -> pika.BlockingConnection:
    """Creates and returns a connection to the message broker."""
    try:
        return pika.BlockingConnection(pika.URLParameters(broker_url))
    except pika.exceptions.AMQPConnectionError as error:
        logger.error(f"Failed to connect to message broker: {error}")
        raise


def get_broker_url() -> str:
    """Constructs the broker URL from environment variables."""
    return (f'amqp://{os.getenv("BROKER_USERNAME")}:'
            f'{os.getenv("BROKER_PASSWORD")}@{os.getenv("BROKER_HOST")}')


def process_message(body: bytes) -> None:
    """Processes a message received from the queue."""
    try:
        data = json.loads(body)
        message_id = data.get('id', 'unknown')
        # Include data for debugging
        logger.info(f"Processing message {message_id}: {data}")

        handle_actions(data)

    except json.JSONDecodeError as error:
        logger.error(
            f"Invalid message format (JSON decoding error): {error}, Body: {body}")
    except Exception as error:
        logger.error(
            f"Error processing message: {error}, Traceback: {traceback.format_exc()}")


@backoff.on_exception(backoff.expo,
                      pika.exceptions.AMQPConnectionError,
                      max_tries=5,  # Limit retry attempts
                      on_backoff=lambda details: logger.warning(f"Backing off {details.get('wait'):.1f} seconds after {details.get('tries')} tries"))
def consume_messages(channel: BlockingChannel) -> None:
    """Consumes messages from the queue."""
    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=lambda ch, method, properties, body: process_message(
            body),
        auto_ack=True  # Consider manual ack for better reliability
    )
    logger.info('Ready to receive messages')
    channel.start_consuming()


def main() -> None:
    """Main entry point for the consumer."""
    logger.info('Initializing consumer...')
    set_environment()

    while True:
        try:
            connection = create_connection(get_broker_url())
            channel = connection.channel()

            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            channel.basic_qos(prefetch_count=PREFETCH_COUNT)

            consume_messages(channel)

        except pika.exceptions.AMQPConnectionError:
            logger.error(
                f'Connection lost. Retrying in {RETRY_INTERVAL} seconds...')
            time.sleep(RETRY_INTERVAL)
        except KeyboardInterrupt:
            logger.info('Shutting down consumer...')
            if connection and not connection.is_closed:
                connection.close()
            break
        except Exception as error:
            logger.error(
                f'Unexpected error: {error}, Traceback: {traceback.format_exc()}')
            time.sleep(RETRY_INTERVAL)


if __name__ == '__main__':
    main()
