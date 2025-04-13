from services.device_message_handler_service.app.core.config import ELASTICSEARCH_HOST, ELASTICSEARCH_PORT, ELASTICSEARCH_CONNECTION, threadPoolExecuteWorker
from shared.app.utils.logging_config import setup_logging
from shared.app.utils.managed_thread_pool import ManagedThreadPool
from services.device_message_handler_service.app.services import listen_queues

if __name__ == "__main__":
    logger = setup_logging('device_message_handler_service',[{'host': ELASTICSEARCH_HOST, 'port': ELASTICSEARCH_PORT, 'scheme': 'http'}], es_start=ELASTICSEARCH_CONNECTION, index_name='mm-device-message-handler-service')
    logger.info("Message Handler Service Starting...")

    threadPoolDeadLetterConsumer = ManagedThreadPool(max_workers=threadPoolExecuteWorker, thread_name="dead_letter_thread")
    listen_queues(threadPoolDeadLetterConsumer)