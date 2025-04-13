# -*- coding: utf-8 -*-
from enum import Enum,auto

class GeneralType(Enum):
    current_time = auto()
    start_time = auto()
    message_count = auto()
    premium  = 'PREMIUM'
    free = 'FREE'
    basic = 'BASIC'
    topic_definition = auto()
    subscribe_type  = auto()
    mqtt_client_object = auto()
    thread_object = auto()