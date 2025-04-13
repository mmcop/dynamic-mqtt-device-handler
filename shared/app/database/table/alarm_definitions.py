from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean, func, ForeignKey, Numeric
from sqlalchemy.orm import relationship

Base = declarative_base()

class AlarmDefinitions(Base):
    __tablename__ = "alarm_definitions"
    __table_args__ = {'schema': 'mm_device'}
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    topic = Column(String(100))
    alarm_name = Column(String(255))
    active = Column(Boolean)
    severity = Column(Integer)
    priority = Column(Integer)
    device_data_label = Column(String(50))
    notification_title = Column(String(50))
    notification_description = Column(String(255))
    notification_type = Column(String(20))
    created_time = Column(TIMESTAMP(timezone=True), default=func.now())
    updated_time = Column(TIMESTAMP(timezone=True), onupdate=func.now())
    tenant_id = Column(String(100))
    created_user = Column(String(100))
    updated_user = Column(String(100))

    logic_groups = relationship("LogicGroups", back_populates="alarm_definition")

    def to_dict(self):
        return {
            "id": self.id,
            "topic": self.topic,
            "alarm_name": self.alarm_name,
            "active": self.active,
            "severity": self.severity,
            "priority": self.priority,
            "device_data_label": self.device_data_label,
            "notification_title": self.notification_title,
            "notification_description": self.notification_description,
            "notification_type": self.notification_type,
            "created_time": self.created_time.isoformat() if self.created_time else None,
            "updated_time": self.updated_time.isoformat() if self.updated_time else None,
            "tenant_id": self.tenant_id,
            "created_user": self.created_user,
            "updated_user": self.updated_user,
        }


class LogicGroups(Base):
    __tablename__ = "logic_groups"
    __table_args__ = {'schema': 'mm_device'}
    id = Column(Integer, primary_key=True, autoincrement=True)
    alarm_definition_id = Column(Integer, ForeignKey("mm_device.alarm_definitions.id"))
    parent_group_id = Column(Integer, ForeignKey("mm_device.logic_groups.id"), nullable=True)
    logic_operator = Column(String(10))

    alarm_definition = relationship("AlarmDefinitions", back_populates="logic_groups")
    parent_group = relationship("LogicGroups", back_populates="child_groups", remote_side=[id])
    child_groups = relationship("LogicGroups", back_populates="parent_group")
    rules = relationship("AlarmRules", back_populates="logic_group")

    def to_dict(self):
        return {
                    "id": self.id,
                    "alarm_definition_id": self.alarm_definition_id,
                    "parent_group_id": self.parent_group_id,
                    "logic_operator": self.logic_operator
            }


class AlarmRules(Base):
    __tablename__ = "alarm_rules"
    __table_args__ = {'schema': 'mm_device'}
    id = Column(Integer, primary_key=True, autoincrement=True)
    logic_group_id = Column(Integer, ForeignKey("mm_device.logic_groups.id"))
    operator = Column(String(5))
    threshold = Column(Numeric(18, 3))

    logic_group = relationship("LogicGroups", back_populates="rules")

    def to_dict(self):
        return {
                    "id": self.id,
                    "logic_group_id": self.logic_group_id,
                    "operator": self.operator,
                    "threshold": str(self.threshold)
            }