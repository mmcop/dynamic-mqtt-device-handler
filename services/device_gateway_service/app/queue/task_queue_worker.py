import queue
from services.device_gateway_service.app.services import add_new_client_queue, topic_remove_queue, add_test_client_queue, topic_listen_close_queue
from services.device_gateway_service.app.core.config import subTaskListenTopic, subTaskControlTopic, subTaskTestTopic, subTaskCloseListenTopic
import uuid
import logging

task_queue = queue.Queue()

def worker(old_user):
    for user_info in old_user:
        task_queue.put({"source": "gateway/topic-listen", "data": user_info})

    while True:
        task = task_queue.get()
        source = task['source']
        user = task['data']

        if source == 'gateway/topic-listen':
            add_new_client_queue(user, subTaskListenTopic+str(uuid.uuid4()), subTaskControlTopic+str(uuid.uuid4()))
        elif source == 'gateway/topic-remove':
            topic_remove_queue(user)
        elif source == 'gateway/test-topic-listen':
            add_test_client_queue(user, subTaskTestTopic+str(uuid.uuid4()))
        elif source == 'gateway/topic-listen-close':
            topic_listen_close_queue(user, subTaskCloseListenTopic+str(uuid.uuid4()))
        else:
            logging.error("Unknown job queue")

        task_queue.task_done()