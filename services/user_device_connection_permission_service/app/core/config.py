import os

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_USER = os.getenv("RABBITMQ_USER")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST","%2F")
DEVICE_MQTT_SERVICE_URL = os.getenv('DEVICE_MQTT_SERVICE_URL')
ELASTICSEARCH_HOST = os.getenv('ELASTICSEARCH_HOST')
ELASTICSEARCH_CONNECTION = True if os.getenv('ELASTICSEARCH_CONNECTION') == "True" else False
ELASTICSEARCH_PORT = int(os.getenv('ELASTICSEARCH_PORT'))
DATABASE_HOST = os.getenv('DATABASE_HOST')
DATABASE_PORT = int(os.getenv('DATABASE_PORT',"5432"))
DATABASE_NAME = os.getenv('DATABASE_NAME')
DATABASE_USERNAME = os.getenv('DATABASE_USERNAME')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')
API_KEY = os.getenv('API_KEY')
subTaskCreate = "create_user_"
subTaskPermission = "set_permission_"
subTaskTopic = "set_topic_permission_"
subTaskUserRecognition = "user_recognition_"
subTaskOldUserDelete = "old_user_delete_"
subTaskDeleteUser = "delete_user_"
subTaskTopicRemove = "topic_remove_"