from shared.app.rabbitMQ.rabbitMQ_consumer import RabbitMQConsumer
from services.device_message_handler_service.app.core import pg_client, start_connection, close_connection
from services.device_message_handler_service.app.core.config import RABBITMQ_HOST, AMQP_PORT, RABBITMQ_USER, RABBITMQ_PASSWORD, EXCHANGE_NAME, DEAD_LETTER_EXCHANGE_NAME, DEAD_LETTER_QUEUE_NAME, QUEUE_NAME
import logging

def listen_queues(threadPoolDeadLetterConsumer):
    try:
        start_connection()
        consumer_two = RabbitMQConsumer(RABBITMQ_HOST, AMQP_PORT, RABBITMQ_USER, RABBITMQ_PASSWORD,EXCHANGE_NAME,pg_client)
        threadPoolDeadLetterConsumer.submit_task(consumer_two.consume, DEAD_LETTER_QUEUE_NAME, DEAD_LETTER_EXCHANGE_NAME)
        consumer = RabbitMQConsumer(RABBITMQ_HOST, AMQP_PORT, RABBITMQ_USER, RABBITMQ_PASSWORD,EXCHANGE_NAME,pg_client)
        consumer.consume(QUEUE_NAME, EXCHANGE_NAME, DEAD_LETTER_EXCHANGE_NAME) 

    finally:
        logging.info("Message Handler Service is Closing...")
        consumer.close_connection()
        consumer_two.close_connection()
        threadPoolDeadLetterConsumer.shutdown()
        close_connection()