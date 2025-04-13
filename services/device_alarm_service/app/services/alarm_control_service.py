from shared.app.enums import MessageType
from shared.app.database.client import PostgreSQLORMClientSingle
import json
import logging
from services.device_alarm_service.app.core.operators import OPERATORS, LOGIC_OPERATORS
from services.device_alarm_service.app.services.redis_conneciton import RedisConnection

pg_client = PostgreSQLORMClientSingle()
redis_connection = RedisConnection()

def send_alarm(title, description):
    logging.error(f"[ALARM] Title: {title}, Description: {description}")


def evaluate_logic_tree(logic_groups, rules, value):
    def process_group(group):
        # Evaluate individual rules
        rule_results = [
            OPERATORS[rule.operator](value, rule.threshold)
            for rule in rules if rule.logic_group_id == group.id
        ]

        # Recursively process child groups
        child_group_results = [
            process_group(child)
            for child in logic_groups if child.parent_group_id == group.id
        ]

        # Combine results based on logic operator
        results = rule_results + child_group_results
        return LOGIC_OPERATORS.get(group.logic_operator, lambda x: x[0])(results)

    # Find root group and evaluate
    root_group = next(group for group in logic_groups if group.parent_group_id is None)
    return process_group(root_group)


def alarm_control(control_alarm_data):
    if not control_alarm_data:
        return

    topic = control_alarm_data.get(MessageType.topic.value)
    data = json.loads(control_alarm_data.get(MessageType.data.value))

    # Redis Cache'ten Alarmları Çek
    cache_key = f"alarm:{topic}"
    cached_alarm = redis_connection.redis_client.get(cache_key)
    """
    # Fetch active alarms for the topic
    alarms = pg_client.SessionLocal().query(AlarmDefinitions).filter(
        (AlarmDefinitions.active == True) &
        (AlarmDefinitions.topic == topic)
    ).all()
    """
    if not cached_alarm:
        print(f"Alarm verisi cache'de bulunamadı: {cache_key}")
        return

    alarms = [json.loads(cached_alarm)]

    for alarm in alarms:
        print(alarm)
        parameter = alarm['device_data_label']
        print(parameter)
        print(data[parameter])
        if parameter not in data or not isinstance(data[parameter], (int, float)):
            continue

        logic_groups = json.loads(redis_connection.redis_client.get(f"logic_group:{alarm['id']}") or "[]")
        rules = json.loads(redis_connection.redis_client.get(f"rule:{alarm['id']}") or "[]")

        print(logic_groups)
        print(rules)
        """
        # Fetch associated logic groups and rules
        logic_groups = pg_client.SessionLocal().query(LogicGroups).filter_by(
            alarm_definition_id=alarm.id
        ).all()

        rules = pg_client.SessionLocal().query(AlarmRules).filter(
            AlarmRules.logic_group_id.in_([group.id for group in logic_groups])
        ).all()
        """

        # Evaluate alarm logic
        if evaluate_logic_tree(logic_groups, rules, data[parameter]):
            send_alarm(alarm.notification_title, alarm.notification_description)