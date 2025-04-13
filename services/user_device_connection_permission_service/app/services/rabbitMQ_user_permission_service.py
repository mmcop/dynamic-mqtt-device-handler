from shared.app.enums.user_type import UserType, UserUpdateModel, TopicRemoveUserModel
import requests
from requests.auth import HTTPBasicAuth
import threading
import time
import uuid
from shared.app.database.table import TaskState
from shared.app.enums.task_action_type import ActionType
import logging
from services.user_device_connection_permission_service.app.core.config import RABBITMQ_USER, RABBITMQ_PASSWORD, RABBITMQ_VHOST, RABBITMQ_HOST
from services.user_device_connection_permission_service.app.core.database_connection import pg_client
from services.user_device_connection_permission_service.app.core.config import subTaskTopic, subTaskPermission, subTaskTopicRemove, subTaskCreate, DEVICE_MQTT_SERVICE_URL, API_KEY

def create_user(username, password):
    url = f"{RABBITMQ_HOST}/api/users/{username}"
    data = {"password": password, "tags": "mqtt"}
    response = requests.put(url, json=data, auth=HTTPBasicAuth(RABBITMQ_USER, RABBITMQ_PASSWORD))
    if response.status_code == 201 or response.status_code == 204:
        logging.info(f"RabbitMQ User Created : '{username}'")
        return True
    else:
        logging.error(f"RabbitMQ User Creation Error: {username}")
        return False

def set_permissions(username):
    url = f"{RABBITMQ_HOST}/api/permissions/{RABBITMQ_VHOST}/{username}"
    data = {
        "configure": "^([amq.topic].*)$",
        "write": "^([amq.topic].*)$",
        "read": ""
    }
    response = requests.put(url, json=data, auth=HTTPBasicAuth(RABBITMQ_USER, RABBITMQ_PASSWORD))
    if response.status_code == 201 or response.status_code == 204:
        logging.info(f"RabbitMQ Permissions Set for User : '{username}'")
        return True
    else:
        logging.error(f"RabbitMQ Permission Setting Error: {response.text}")
        return False

def set_topic_permissions(user: UserType):
    url = f"{RABBITMQ_HOST}/api/topic-permissions/{RABBITMQ_VHOST}/{user.username}"
    if( "/" in user.topic):
        data = {
            "exchange": "amq.topic",
            "write": f"^{user.topic.split('/')[0]}.*",
            "read": ""
        }
        response = requests.put(url, json=data, auth=HTTPBasicAuth(RABBITMQ_USER, RABBITMQ_PASSWORD))
        if response.status_code == 201 or response.status_code == 204:
            logging.info(f"RabbitMQ Topic Permissions Set for User : '{user.username}'")
            return True
        else:
            logging.error(f"RabbitMQ Topic Permission Setting Error: {response.text}")
            return False
    else:
        logging.error("Topic is not in the correct format")
        return False

def delete_user(username):
    url = f"{RABBITMQ_HOST}/api/users/{username}?"
    response = requests.delete(url, auth=HTTPBasicAuth(RABBITMQ_USER, RABBITMQ_PASSWORD))
    if response.status_code == 204 or response.status_code == 200:
        logging.info(f"RabbitMQ User Removed : '{username}'")
        return True
    else:
        logging.error(f"RabbitMQ User Removed Error: {response.text}")
        return False

def check_user(username):
    response = requests.get(f'{RABBITMQ_HOST}/api/users', auth=HTTPBasicAuth(RABBITMQ_USER, RABBITMQ_PASSWORD))
    if response.status_code == 200:
        users = response.json()
        user_names = [u['name'] for u in users]
        return username in user_names
    else:
        logging.error(f"RabbitMQ User Check Error: {username} does not exist")
        return False
    
def query_task_table_and_create_user_queue(user, next_task_id, sub_task_id):
    while True:
        results = pg_client.select_from_table_with_model(model_class=TaskState,
            filters={TaskState.sub_task_id.key: sub_task_id},order_by='id',single=True)

        if results and (results.sub_task_action == ActionType.topic_remove_completed.value or
                        results.sub_task_action == ActionType.topic_remove_not_found.value or
                        results.sub_task_action == ActionType.topic_remove_error.value):
            create_user_queue(user.new_user_topic, next_task_id, subTaskPermission + str(uuid.uuid4()),
                              subTaskTopic + str(uuid.uuid4()))
            break

        time.sleep(1)
    
def create_user_queue(user: UserType, subTaskOne: str, subTaskTwo: str, subTaskThree: str):
    pg_client.insert_message(TaskState,
                          {TaskState.username.key: user.username, TaskState.main_task_action.key: ActionType.started.value,
                           TaskState.main_task_id.key: user.main_task_id})
    if create_user(user.username, user.password):
        pg_client.insert_message(TaskState, {TaskState.username.key: user.username,
                                          TaskState.main_task_action.key: ActionType.continuous.value,
                                          TaskState.main_task_id.key: user.main_task_id, TaskState.sub_task_id.key: subTaskOne,
                                          TaskState.sub_task_action.key: ActionType.create_user_completed.value,
                                          TaskState.next_task_id.key: subTaskTwo})
        if set_permissions(user.username):
            pg_client.insert_message(TaskState, {TaskState.username.key: user.username,
                                              TaskState.main_task_action.key: ActionType.continuous.value,
                                              TaskState.main_task_id.key: user.main_task_id,
                                              TaskState.sub_task_id.key: subTaskTwo,
                                              TaskState.sub_task_action.key: ActionType.set_permission_completed.value,
                                              TaskState.next_task_id.key: subTaskThree})
            if set_topic_permissions(user):
                pg_client.insert_message(TaskState, {TaskState.username.key: user.username,
                                                  TaskState.main_task_action.key: ActionType.completed.value,
                                                  TaskState.main_task_id.key: user.main_task_id,
                                                  TaskState.sub_task_id.key: subTaskThree,
                                                  TaskState.sub_task_action.key: ActionType.set_topic_permission_completed.value})
            else:
                pg_client.insert_message(TaskState, {TaskState.username.key: user.username,
                                                  TaskState.main_task_action.key: ActionType.error.value,
                                                  TaskState.main_task_id.key: user.main_task_id,
                                                  TaskState.sub_task_id.key: subTaskThree,
                                                  TaskState.sub_task_action.key: ActionType.set_topic_permission_error.value})
                _ = delete_user(user.username)
        else:
            pg_client.insert_message(TaskState, {TaskState.username.key: user.username,
                                              TaskState.main_task_action.key: ActionType.error.value,
                                              TaskState.main_task_id.key: user.main_task_id,
                                              TaskState.sub_task_id.key: subTaskTwo,
                                              TaskState.sub_task_action.key: ActionType.set_permission_error.value})
            _ = delete_user(user.username)
    else:
        pg_client.insert_message(TaskState,
                              {TaskState.username.key: user.username, TaskState.main_task_action.key: ActionType.error.value,
                               TaskState.main_task_id.key: user.main_task_id, TaskState.sub_task_id.key: subTaskOne,
                               TaskState.sub_task_action.key: ActionType.create_user_error.value})

def update_user_queue(user: UserUpdateModel, sub_task_one: str, sub_task_two: str):
    pg_client.insert_message(TaskState,
                          {TaskState.username.key: user.new_user_topic.username,
                           TaskState.main_task_action.key: ActionType.started.value,
                           TaskState.main_task_id.key: user.new_user_topic.main_task_id})
    topic_remove_user = TopicRemoveUserModel(
        sub_task_id = subTaskTopicRemove + str(uuid.uuid4()),
        user=user.old_user_topic
    )
    create_user_next_task_id = subTaskCreate + str(uuid.uuid4())
    
    if check_user(user.old_user_topic.username):
        pg_client.insert_message(TaskState,
                              {TaskState.username.key: user.new_user_topic.username,
                               TaskState.main_task_action.key: ActionType.continuous.value,
                               TaskState.main_task_id.key: user.new_user_topic.main_task_id,
                               TaskState.sub_task_id.key: sub_task_one,
                               TaskState.sub_task_action.key: ActionType.user_recognition_completed.value,
                               TaskState.next_task_id.key: sub_task_two})
        if delete_user(user.old_user_topic.username):
            pg_client.insert_message(TaskState,
                                  {TaskState.username.key: user.new_user_topic.username,
                                   TaskState.main_task_action.key: ActionType.continuous.value,
                                   TaskState.main_task_id.key: user.new_user_topic.main_task_id,
                                   TaskState.sub_task_id.key: sub_task_two,
                                   TaskState.sub_task_action.key: ActionType.old_user_delete_completed.value,
                                   TaskState.next_task_id.key: topic_remove_user.sub_task_id})
        else:
            pg_client.insert_message(TaskState,
                                  {TaskState.username.key: user.new_user_topic.username,
                                   TaskState.main_task_action.key: ActionType.continuous.value,
                                   TaskState.main_task_id.key: user.new_user_topic.main_task_id,
                                   TaskState.sub_task_id.key: sub_task_two,
                                   TaskState.sub_task_action.key: ActionType.old_user_delete_error.value,
                                   TaskState.next_task_id.key: topic_remove_user.sub_task_id})
    else:
        pg_client.insert_message(TaskState,
                              {TaskState.username.key: user.new_user_topic.username,
                               TaskState.main_task_action.key: ActionType.continuous.value,
                               TaskState.main_task_id.key: user.new_user_topic.main_task_id,
                               TaskState.sub_task_id.key: sub_task_one,
                               TaskState.sub_task_action.key: ActionType.user_recognition_error.value,
                               TaskState.next_task_id.key: sub_task_two})

    pg_client.insert_message(TaskState,
                          {TaskState.username.key: user.new_user_topic.username,
                           TaskState.main_task_action.key: ActionType.continuous.value,
                           TaskState.main_task_id.key: user.new_user_topic.main_task_id,
                           TaskState.sub_task_id.key: topic_remove_user.sub_task_id,
                           TaskState.sub_task_action.key: ActionType.topic_remove_started.value,
                           TaskState.next_task_id.key: create_user_next_task_id})

    response = requests.put(f"{DEVICE_MQTT_SERVICE_URL}/gateway/topic-remove", json=topic_remove_user.dict(), headers={"api_key": f"{API_KEY}"})
    if response.status_code == 200:
        logging.info(f"Topic Remove Message sent successfully: {response.json()}")
    else:
        pg_client.insert_message(TaskState,
                              {TaskState.username.key: user.new_user_topic.username,
                               TaskState.main_task_action.key: ActionType.continuous.value,
                               TaskState.main_task_id.key: user.new_user_topic.main_task_id,
                               TaskState.sub_task_id.key: topic_remove_user.sub_task_id,
                               TaskState.sub_task_action.key: ActionType.topic_remove_error.value,
                               TaskState.next_task_id.key: create_user_next_task_id})
        logging.error(f"Topic Remove Failed to send message: {response.status_code}")
        
    query_thread = threading.Thread(target=query_task_table_and_create_user_queue,
                                    args=(user, create_user_next_task_id, topic_remove_user.sub_task_id))
    query_thread.start()

def delete_user_queue(user: UserType, sub_task_one: str, sub_task_two: str):
    pg_client.insert_message(TaskState,
                          {TaskState.username.key: user.username,
                           TaskState.main_task_action.key: ActionType.started.value,
                           TaskState.main_task_id.key: user.main_task_id})
    
    topic_remove_user = TopicRemoveUserModel(
        sub_task_id=subTaskTopicRemove + str(uuid.uuid4()),
        user=user
    )
    
    if check_user(user.username):
        pg_client.insert_message(TaskState,
                              {TaskState.username.key: user.username,
                               TaskState.main_task_action.key: ActionType.continuous.value,
                               TaskState.main_task_id.key: user.main_task_id,
                               TaskState.sub_task_id.key: sub_task_one,
                               TaskState.sub_task_action.key: ActionType.user_recognition_completed.value,
                               TaskState.next_task_id.key: sub_task_two})
        if delete_user(user.username):
            pg_client.insert_message(TaskState,
                                  {TaskState.username.key: user.username,
                                   TaskState.main_task_action.key: ActionType.continuous.value,
                                   TaskState.main_task_id.key: user.main_task_id,
                                   TaskState.sub_task_id.key: sub_task_two,
                                   TaskState.sub_task_action.key: ActionType.user_delete_completed.value,
                                   TaskState.next_task_id.key: topic_remove_user.sub_task_id})
        else:
            pg_client.insert_message(TaskState,
                                  {TaskState.username.key: user.username,
                                   TaskState.main_task_action.key: ActionType.continuous.value,
                                   TaskState.main_task_id.key: user.main_task_id,
                                   TaskState.sub_task_id.key: sub_task_two,
                                   TaskState.sub_task_action.key: ActionType.old_user_delete_error.value,
                                   TaskState.next_task_id.key: topic_remove_user.sub_task_id})
    else:
        pg_client.insert_message(TaskState,
                              {TaskState.username.key: user.username,
                               TaskState.main_task_action.key: ActionType.continuous.value,
                               TaskState.main_task_id.key: user.main_task_id,
                               TaskState.sub_task_id.key: sub_task_one,
                               TaskState.sub_task_action.key: ActionType.user_recognition_error.value,
                               TaskState.next_task_id.key: sub_task_two})

    pg_client.insert_message(TaskState,
                          {TaskState.username.key: user.username,
                           TaskState.main_task_action.key: ActionType.continuous.value,
                           TaskState.main_task_id.key: user.main_task_id,
                           TaskState.sub_task_id.key: topic_remove_user.sub_task_id,
                           TaskState.sub_task_action.key: ActionType.topic_remove_started.value})
    response = requests.put(f"{DEVICE_MQTT_SERVICE_URL}/gateway/topic-remove", json=topic_remove_user.dict(), headers={"api_key": f"{API_KEY}"})
    if response.status_code == 200:
        logging.info(f"Topic Remove Message sent successfully: {response.json()}")
    else:
        pg_client.insert_message(TaskState,
                              {TaskState.username.key: user.username,
                               TaskState.main_task_action.key: ActionType.continuous.value,
                               TaskState.main_task_id.key: user.main_task_id,
                               TaskState.sub_task_id.key: topic_remove_user.sub_task_id,
                               TaskState.sub_task_action.key: ActionType.topic_remove_error.value})
        logging.error(f"Topic Remove Failed to send message: {response.status_code}")