from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, JSON, TIMESTAMP, func

Base = declarative_base()

class DeviceTestConnectionData(Base):
    __tablename__ = "device_test_connection_data"
    __table_args__ = {'schema': 'mm_device'}
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    data = Column(JSON)
    time = Column(TIMESTAMP(timezone=True), default=func.now())
    topic = Column(String(100))