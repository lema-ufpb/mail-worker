import pika
from json import dumps
from os import getenv
from src.consumer import get_broker_url

def simulate_producer(message_data: dict) -> None:
    """Simulates a producer sending a message to RabbitMQ."""

    broker_url = get_broker_url()
    try:
        connection = pika.BlockingConnection(pika.URLParameters(broker_url))
        channel = connection.channel()

        queue_name = getenv("QUEUE_NAME", "tasks") # Use the same queue name as the consumer
        channel.queue_declare(queue=queue_name, durable=True) # Ensure the queue exists and is durable

        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=dumps(message_data),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE  # Make messages persistent
            ))
        print(f" [x] Sent message: {message_data['email']}")

    except pika.exceptions.AMQPConnectionError as e:
        print(f"Error connecting to RabbitMQ: {e}")
    finally:
        if connection:
            connection.close()



# Example usage:
if __name__ == "__main__":

    message1 = {
        "id": "pin-code",
        "pin": "123456",
        "email": "hiltonmbr@gmail.com",
    }
    simulate_producer(message1)

    
    message2 = {
        "id": "user-subscription",
        "name": "Test User",
        "email": "hiltonmbr@gmail.com",
        "message": "Welcome to our platform!",
    }
    simulate_producer(message2)
   

