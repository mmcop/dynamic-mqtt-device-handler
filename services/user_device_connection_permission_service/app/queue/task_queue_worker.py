import queue
import uuid
import logging
from services.user_device_connection_permission_service.app.core.config import subTaskCreate, subTaskUserRecognition, subTaskPermission, subTaskTopic, subTaskOldUserDelete
from services.user_device_connection_permission_service.app.services import create_user_queue, delete_user_queue, update_user_queue

task_queue = queue.Queue()

def worker():
    while True:
        task = task_queue.get()
        source = task['source']
        user = task['data']

        if source == 'user/create':
            create_user_queue(user, subTaskCreate+str(uuid.uuid4()), subTaskPermission+str(uuid.uuid4()), subTaskTopic+str(uuid.uuid4()))
        elif source == 'user/update':
            update_user_queue(user, subTaskUserRecognition+str(uuid.uuid4()), subTaskOldUserDelete+str(uuid.uuid4()))
        elif source == 'user/delete':
            delete_user_queue(user, subTaskUserRecognition+str(uuid.uuid4()), subTaskOldUserDelete+str(uuid.uuid4()))
        else:
            logging.error("Unknown job queue")

        task_queue.task_done()