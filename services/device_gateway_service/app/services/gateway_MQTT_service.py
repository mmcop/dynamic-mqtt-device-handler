# -*- coding: utf-8 -*-
from shared.app.enums import GeneralType, UserType, UserInfoType, UserTestType, TopicRemoveUserModel, UserCloseListenModel
from services.device_gateway_service.app.mqtt import MQTTClient, MQTTTestConnectionClient
from shared.app.database.table import TaskState
from shared.app.utils.managed_thread_pool import ManagedThreadPool
import uuid
import time
from shared.app.enums.task_action_type import ActionType
from services.device_gateway_service.app.core.config import BASIC_THREAD_WORKER,PREMIUM_THREAD_WORKER,FREE_THREAD_WORKER,freeChunkSize,basicChunkSize,MQTT_TIMEOUT, freeThreadName, basicThreadName
from services.device_gateway_service.app.core.config import RABBITMQ_PASSWORD, RABBITMQ_HOST, RABBITMQ_USER, MQTT_PORT, AMQP_PORT, EXCHANGE_NAME, EXCHANGE_FANOUT, QUEUE_FRONTEND, QUEUE_KPI
from services.device_gateway_service.app.core.database_connection import pg_client

freeClient = {}
basicClient = {}
premiumClient = {}
testConnectionClient = {}

def new_client_set_connection(client_map, chunk_size, user: UserType, thread_worker, sub_task_listen_id, save_database, thread_name):
    if client_map:
        company_dict = {}
        for company in client_map:
            topic_lenght = len(list(client_map[company][GeneralType.topic_definition.name].keys()))
            if topic_lenght < chunk_size:
                company_dict[company] = topic_lenght
                
        if company_dict:
            max_topic_company = max(company_dict, key=company_dict.get)
            client_map[max_topic_company][GeneralType.topic_definition.name][user.topic] = {UserInfoType.max_messages_per_minute.name: user.max_messages_per_minute,
                                                                                           UserInfoType.max_message_size.name: user.max_message_size,
                                                                                           UserInfoType.save_database.name: save_database}

            client_map[max_topic_company][GeneralType.mqtt_client_object.name].topicInfo = client_map[max_topic_company][GeneralType.topic_definition.name].copy()
            client_map[max_topic_company][GeneralType.mqtt_client_object.name].client.subscribe((user.topic, 1))
        
        else:
            generateCompanyName = str(uuid.uuid4())
            topic_map = {user.topic: {UserInfoType.max_messages_per_minute.name: user.max_messages_per_minute,
                                    UserInfoType.max_message_size.name: user.max_message_size,
                                      UserInfoType.save_database.name: save_database}}
            create_mqtt_and_thread_objects(client_type_object=client_map, company=generateCompanyName, thread_worker=thread_worker, topic_map=topic_map, client_id=generateCompanyName, thread_name=thread_name)
            topic_listen_task_done(user=user, sub_task_listen_id=sub_task_listen_id)

    else:
        generateCompanyName = str(uuid.uuid4())
        topic_map = {user.topic: {UserInfoType.max_messages_per_minute.name: user.max_messages_per_minute,
                                  UserInfoType.max_message_size.name: user.max_message_size,
                                  UserInfoType.save_database.name: save_database}}
        create_mqtt_and_thread_objects(client_type_object=client_map, company=generateCompanyName, thread_worker=thread_worker, topic_map=topic_map, client_id=generateCompanyName, thread_name=thread_name)
        topic_listen_task_done(user=user, sub_task_listen_id=sub_task_listen_id)
        
def add_new_client_queue(user: UserType, sub_task_listen_id: str, sub_task_control_id: str):
    pg_client.insert_message(TaskState,
                          {TaskState.username.key: user.username, TaskState.main_task_action.key: ActionType.started.value,
                           TaskState.main_task_id.key: user.main_task_id})
    control_topic(sub_task_control_id,sub_task_listen_id,user) # Control Topic if is available

    if user.subscribe_type == GeneralType.free.value:
        new_client_set_connection(client_map= freeClient, chunk_size= freeChunkSize, user= user, thread_worker= FREE_THREAD_WORKER, 
                                  sub_task_listen_id= sub_task_listen_id, save_database=False, thread_name=freeThreadName)

    elif user.subscribe_type == GeneralType.basic.value:
        new_client_set_connection(client_map= basicClient, chunk_size= basicChunkSize, user= user, thread_worker= BASIC_THREAD_WORKER, 
                                  sub_task_listen_id= sub_task_listen_id, save_database=True, thread_name=basicThreadName)

    elif user.subscribe_type == GeneralType.premium.value:
        if premiumClient:
            if user.company in premiumClient:
                premiumClient[user.company][GeneralType.topic_definition.name][user.topic] = {UserInfoType.max_messages_per_minute.name: user.max_messages_per_minute,
                                                                                             UserInfoType.max_message_size.name: user.max_message_size,
                                                                                             UserInfoType.save_database.name: True}

                premiumClient[user.company][GeneralType.mqtt_client_object.name].topicInfo = premiumClient[user.company][GeneralType.topic_definition.name].copy()
                premiumClient[user.company][GeneralType.mqtt_client_object.name].client.subscribe((user.topic, 1))
            else:
                topic_map = {user.topic: {UserInfoType.max_messages_per_minute.name: user.max_messages_per_minute,
                                                                                UserInfoType.max_message_size.name: user.max_message_size}}
                create_mqtt_and_thread_objects(client_type_object=premiumClient, company=user.company, thread_worker=PREMIUM_THREAD_WORKER, topic_map=topic_map, client_id=user.company, thread_name=user.company+"-thread")
                topic_listen_task_done(user=user, sub_task_listen_id=sub_task_listen_id)
        else:
            topic_map = {user.topic: {UserInfoType.max_messages_per_minute.name: user.max_messages_per_minute,
                                      UserInfoType.max_message_size.name: user.max_message_size,
                                      UserInfoType.save_database.name: True}}
            create_mqtt_and_thread_objects(client_type_object=premiumClient, company=user.company, thread_worker=PREMIUM_THREAD_WORKER, topic_map=topic_map, client_id=user.company, thread_name=user.company+"-thread")
            topic_listen_task_done(user=user, sub_task_listen_id=sub_task_listen_id)
                
def topic_remove_queue(remove_user: TopicRemoveUserModel):
    user = remove_user.user
    sub_task_id = remove_user.sub_task_id
    if user.subscribe_type == GeneralType.free.value and freeClient:
        for company in freeClient:
            if user.topic in freeClient[company][GeneralType.topic_definition.name]:
                del freeClient[company][GeneralType.topic_definition.name][user.topic]
                unscribe_mqtt_topic(client_type_object=freeClient, company=company, old_topic_list=[user.topic])
                break
        remove_topic_task_done(user=user,sub_task_remove_id=sub_task_id)

    elif user.subscribe_type == GeneralType.basic.value and basicClient:
        for company in basicClient:
            if user.topic in basicClient[company][GeneralType.topic_definition.name]:
                del basicClient[company][GeneralType.topic_definition.name][user.topic]
                unscribe_mqtt_topic(client_type_object=basicClient, company=company, old_topic_list=[user.topic])
                break
        remove_topic_task_done(user=user,sub_task_remove_id=sub_task_id)
        
    elif user.subscribe_type == GeneralType.premium.value and premiumClient:
        if user.topic in premiumClient[user.company][GeneralType.topic_definition.name]:
            del premiumClient[user.company][GeneralType.topic_definition.name][user.topic]
            unscribe_mqtt_topic(client_type_object=premiumClient, company=user.company, old_topic_list=[user.topic])
        remove_topic_task_done(user=user,sub_task_remove_id=sub_task_id)

    else:
        remove_topic_task_error(user=user,sub_task_remove_id=sub_task_id)
            
def add_test_client_queue(user: UserTestType, sub_task_test_id: str):
    pg_client.insert_message(TaskState,
                             {TaskState.username.key: user.username,
                              TaskState.main_task_action.key: ActionType.started.value,
                              TaskState.main_task_id.key: user.main_task_id})
    test_topic = {user.topic: time.time()}
    if testConnectionClient:
        testConnectionClient[GeneralType.mqtt_client_object.name].client.subscribe((user.topic, 1))
        testConnectionClient[GeneralType.mqtt_client_object.name].topicInfo[user.topic] = time.time()
    else:
        testConnectionClient[GeneralType.mqtt_client_object.name] = MQTTTestConnectionClient(test_topic, RABBITMQ_USER, RABBITMQ_PASSWORD, pg_client)
        testConnectionClient[GeneralType.thread_object.name] =  ManagedThreadPool(max_workers=1, thread_name='test-listen-thread')
        testConnectionClient[GeneralType.thread_object.name].submit_task(testConnectionClient[GeneralType.mqtt_client_object.name].connect(RABBITMQ_HOST, MQTT_PORT,
                                                                                      MQTT_TIMEOUT))
    pg_client.insert_message(TaskState,
                             {TaskState.username.key: user.username,
                              TaskState.main_task_action.key: ActionType.completed.value,
                              TaskState.main_task_id.key: user.main_task_id,
                              TaskState.sub_task_id.key: sub_task_test_id,
                              TaskState.sub_task_action.key: ActionType.test_topic_listen_completed.value
                              })

def topic_listen_close_queue(user: UserCloseListenModel, sub_task_listen_close: str):
    if user.subscribe_type == GeneralType.free.name and freeClient:
        for company in freeClient:
            if user.topic in freeClient[company][GeneralType.topic_definition.name]:
                del freeClient[company][GeneralType.topic_definition.name][user.topic]
                unscribe_mqtt_topic(client_type_object=freeClient, company=company, old_topic_list=[user.topic])
                break
        close_topic_listen_task_done(user=user,sub_task_remove_id=sub_task_listen_close)    
    
    elif user.subscribe_type == GeneralType.basic.value and basicClient:
        for company in basicClient:
            if user.topic in basicClient[company][GeneralType.topic_definition.name]:
                del basicClient[company][GeneralType.topic_definition.name][user.topic]
                unscribe_mqtt_topic(client_type_object=basicClient, company=company, old_topic_list=[user.topic])
                break
        close_topic_listen_task_done(user=user,sub_task_remove_id=sub_task_listen_close)
        
    elif user.subscribe_type == GeneralType.premium.value and premiumClient:
        if user.topic in premiumClient[user.company][GeneralType.topic_definition.name]:
            del premiumClient[user.company][GeneralType.topic_definition.name][user.topic]
            unscribe_mqtt_topic(client_type_object=premiumClient, company=user.company, old_topic_list=[user.topic])
        close_topic_listen_task_done(user=user,sub_task_remove_id=sub_task_listen_close)
    else:
        close_topic_listen_task_error(user=user,sub_task_remove_id=sub_task_listen_close)

def control_topic(sub_task_id: str, sub_task_listen_id: str, user: UserType):
    if user.subscribe_type == GeneralType.free.value and freeClient:
        for company in freeClient:
            if user.topic in freeClient[company][GeneralType.topic_definition.name]:
                pg_client.insert_message(TaskState,
                                      {TaskState.username.key: user.username,
                                       TaskState.main_task_action.key: ActionType.continuous.value,
                                       TaskState.main_task_id.key: user.main_task_id,
                                       TaskState.sub_task_id.key: sub_task_id,
                                       TaskState.sub_task_action.key: ActionType.same_topic_listen_error.value,
                                       TaskState.next_task_id.key: sub_task_listen_id})
                break
    elif user.subscribe_type == GeneralType.basic.value and basicClient:
        for company in basicClient:
            if user.topic in basicClient[company][GeneralType.topic_definition.name]:
                pg_client.insert_message(TaskState,
                                         {TaskState.username.key: user.username,
                                          TaskState.main_task_action.key: ActionType.continuous.value,
                                          TaskState.main_task_id.key: user.main_task_id,
                                          TaskState.sub_task_id.key: sub_task_id,
                                          TaskState.sub_task_action.key: ActionType.same_topic_listen_error.value,
                                          TaskState.next_task_id.key: sub_task_listen_id})
                break
    elif user.subscribe_type == GeneralType.premium.value and premiumClient:
        for company in premiumClient:
            if user.topic in premiumClient[company][GeneralType.topic_definition.name]:
                pg_client.insert_message(TaskState,
                                         {TaskState.username.key: user.username,
                                          TaskState.main_task_action.key: ActionType.continuous.value,
                                          TaskState.main_task_id.key: user.main_task_id,
                                          TaskState.sub_task_id.key: sub_task_id,
                                          TaskState.sub_task_action.key: ActionType.same_topic_listen_error.value,
                                          TaskState.next_task_id.key: sub_task_listen_id})
                break

def topic_listen_task_done(user: UserType, sub_task_listen_id: str):
    pg_client.insert_message(TaskState, {TaskState.username.key: user.username,
                                         TaskState.main_task_action.key: ActionType.completed.value,
                                         TaskState.main_task_id.key: user.main_task_id,
                                         TaskState.sub_task_id.key: sub_task_listen_id,
                                         TaskState.sub_task_action.key: ActionType.listen_topic_completed.value})

def close_topic_listen_task_done(user: UserCloseListenModel, sub_task_remove_id: str):
    pg_client.insert_message(TaskState, {TaskState.username.key: user.username,
                                         TaskState.main_task_action.key: ActionType.completed.value,
                                         TaskState.main_task_id.key: user.main_task_id,
                                         TaskState.sub_task_id.key: sub_task_remove_id,
                                         TaskState.sub_task_action.key: ActionType.close_listen_topic_completed.value})

def close_topic_listen_task_error(user: UserCloseListenModel, sub_task_remove_id: str):
    pg_client.insert_message(TaskState, {TaskState.username.key: user.username,
                                         TaskState.main_task_action.key: ActionType.completed.value,
                                         TaskState.main_task_id.key: user.main_task_id,
                                         TaskState.sub_task_id.key: sub_task_remove_id,
                                         TaskState.sub_task_action.key: ActionType.close_listen_topic_not_found.value})
    
def remove_topic_task_done(user: UserType, sub_task_remove_id: str):
    pg_client.insert_message(TaskState, {TaskState.username.key: user.username,
                                         TaskState.main_task_action.key: ActionType.continuous.value,
                                         TaskState.main_task_id.key: user.main_task_id,
                                         TaskState.sub_task_id.key: sub_task_remove_id,
                                         TaskState.sub_task_action.key: ActionType.topic_remove_completed.value})

def remove_topic_task_error(user: UserType, sub_task_remove_id: str):
    pg_client.insert_message(TaskState, {TaskState.username.key: user.username,
                                         TaskState.main_task_action.key: ActionType.continuous.value,
                                         TaskState.main_task_id.key: user.main_task_id,
                                         TaskState.sub_task_id.key: sub_task_remove_id,
                                         TaskState.sub_task_action.key: ActionType.topic_remove_not_found.value})

def create_mqtt_and_thread_objects(client_type_object, company, topic_map, thread_worker, client_id, thread_name):
    client_type_object[company] = {GeneralType.topic_definition.name: topic_map,
                                         GeneralType.mqtt_client_object.name: MQTTClient(topicInfo=topic_map,
                                                                                            RABBITMQ_USER=RABBITMQ_USER,
                                                                                            RABBITMQ_PASSWORD=RABBITMQ_PASSWORD,
                                                                                            RABBITMQ_HOST=RABBITMQ_HOST,
                                                                                            AMQP_PORT=AMQP_PORT, EXCHANGE=EXCHANGE_NAME, pg_client=pg_client,
                                                                                            EXCHANGE_FANOUT=EXCHANGE_FANOUT, QUEUE_KPI=QUEUE_KPI,
                                                                                            QUEUUE_FRONTEND=QUEUE_FRONTEND, client_id=client_id),
                                         GeneralType.thread_object.name: ManagedThreadPool(max_workers=thread_worker,thread_name=thread_name)}

    client_type_object[company][GeneralType.thread_object.name].submit_task(
        client_type_object[company][GeneralType.mqtt_client_object.name].connect(RABBITMQ_HOST, MQTT_PORT,
                                                                                      MQTT_TIMEOUT))

def unscribe_mqtt_topic(client_type_object, company, old_topic_list):
    client_type_object[company][GeneralType.mqtt_client_object.name].stop_listening_to_topics(old_topic_list)
    if len(list(client_type_object[company][GeneralType.topic_definition.name].keys())) > 0:
        client_type_object[company][GeneralType.mqtt_client_object.name].topicInfo = client_type_object[company][GeneralType.topic_definition.name].copy()
    else:
        client_type_object[company][GeneralType.mqtt_client_object.name].disconnect()
        client_type_object[company][GeneralType.thread_object.name].shutdown()
        del client_type_object[company]

def delete_mqtt_and_thread_object(client_type_object,company=None):
    if company:
        if company in client_type_object:
            client_type_object[company][GeneralType.mqtt_client_object.name].disconnect()
            client_type_object[company][GeneralType.thread_object.name].shutdown()
            del client_type_object[company]
            return True
        else:
            return False
    else:
        temp_company_name = list(client_type_object.keys())
        for company in temp_company_name:
            client_type_object[company][GeneralType.mqtt_client_object.name].disconnect()
            client_type_object[company][GeneralType.thread_object.name].shutdown()
            del client_type_object[company]