from enum import Enum

class MessageType(Enum):
    topic = 'topic'
    data = 'data'
    error = 'error'
    errorLog = 'error_log'