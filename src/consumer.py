"""Message queue consumer for email notification processing"""
import backoff
from os import getenv
from json import loads, JSONDecodeError
from time import sleep
from traceback import format_exc
from pika import BlockingConnection,  URLParameters
from src import logger
from src.utils import local_environment, handle_actions
from pika.adapters.blocking_connection import BlockingChannel
from pika.exceptions import AMQPConnectionError


RETRY_INTERVAL = int(getenv("RETRY_INTERVAL", 15))
QUEUE_NAME = getenv("QUEUE_NAME", "tasks")
PREFETCH_COUNT = int(getenv("PREFETCH_COUNT", 1))


def create_connection(broker_url: str) -> BlockingConnection:
    """Creates and returns a connection to the message broker."""
    try:
        return BlockingConnection(URLParameters(broker_url))
    except AMQPConnectionError as error:
        logger.error(f"Failed to connect to message broker: {error}")
        raise


def get_broker_url() -> str:
    """Constructs the broker URL from environment variables."""
    return (f'amqp://{getenv("BROKER_USERNAME")}:'
            f'{getenv("BROKER_PASSWORD")}@{getenv("BROKER_HOST")}')


def process_message(body: bytes) -> None:
    """Processes a message received from the queue."""
    try:
        data = loads(body)

        logger.info(f"Processing message: {data.get('id')}")
        if not isinstance(data, dict):
            logger.error(f"Invalid message format: {data}")
            return

        if not data.get('id'):
            logger.error("No message id provided.")
            return

        handle_actions(data)

    except JSONDecodeError as error:
        logger.error(
            f"Invalid message format (JSON decoding error): {error}, Body: {body}")
    except Exception as error:
        logger.error(
            f"Error processing message: {error}, Traceback: {format_exc()}")


@backoff.on_exception(backoff.expo,
                      AMQPConnectionError,
                      max_tries=5,  
                      on_backoff=lambda details: logger.warning(f"Backing off {details.get('wait'):.1f} seconds after {details.get('tries')} tries"))
def consume_messages(channel: BlockingChannel) -> None:
    """Consumes messages from the queue."""
    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=lambda ch, method, properties, body: process_message(
            body),
        auto_ack=True
    )
    logger.info('Ready to receive messages')
    channel.start_consuming()


def main() -> None:
    """Main entry point for the consumer."""
    logger.info('Initializing consumer...')
    local_environment()

    while True:
        try:
            connection = create_connection(get_broker_url())
            channel = connection.channel()

            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            channel.basic_qos(prefetch_count=PREFETCH_COUNT)

            consume_messages(channel)

        except AMQPConnectionError:
            logger.error(
                f'Connection lost. Retrying in {RETRY_INTERVAL} seconds...')
            sleep(RETRY_INTERVAL)
        except KeyboardInterrupt:
            logger.info('Shutting down consumer...')
            if connection and not connection.is_closed:
                connection.close()
            break
        except Exception as error:
            logger.error(
                f'Unexpected error: {error}, Traceback: {format_exc()}')
            sleep(RETRY_INTERVAL)


if __name__ == '__main__':
    main()
