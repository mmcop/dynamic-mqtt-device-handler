import threading
from sqlalchemy import create_engine, Table, select, desc, text, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import logging

class PostgreSQLORMClientSingle:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """Singleton örneğini oluştur veya mevcut olanı döndür."""
        with cls._lock:
            if not cls._instance:
                cls._instance = super(PostgreSQLORMClientSingle, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self, host=None, port=None, dbname=None, user=None, password=None, pool_size=3, max_overflow=0, pool_timeout=30, pool_recycle=1800):
        if self._initialized:
            return
        self._initialized = True

        self.database_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"

        # SQLAlchemy motorunu oluşturma
        self.engine = create_engine(
            self.database_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            pool_pre_ping=True,
            echo_pool=True
        )

        # Oturum (session) yönetimi
        self.SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=self.engine))
        self.Base = declarative_base()
        self._stop_event = threading.Event()

    def connect(self):
        """Veritabanı bağlantısını başlatır ve bağlantı havuzunu oluşturur."""
        self.engine.connect()
        logging.info("PostgreSQL client and pool created.")

    def close_connection(self):
        """Bağlantı havuzunu kapatır."""
        self.SessionLocal.remove()
        self.engine.dispose()
        logging.info("PostgreSQL client pooling has been turned off.")

    def create_table(self, table_class):
        """Veritabanında tablo oluşturur."""
        schema_name = table_class.__table_args__.get('schema') if '__table_args__' in table_class.__dict__ else None

        if schema_name:
            with self.engine.connect() as connection:
                with connection.begin() as trans:
                    try:
                        schema_check_query = text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
                        connection.execute(schema_check_query)
                        logging.info(f"{schema_name} schema has been created or already exists.")
                        trans.commit()
                    except Exception as e:
                        logging.error(f"Schema creation failed: {e}")
                        trans.rollback()
                        raise e

        table_class.__table__.create(bind=self.engine, checkfirst=True)
        logging.info(f"{table_class.__tablename__} The table has been created or already exists.")

    def insert_message(self, table_class, message):
        """Mesajı veritabanına kaydeder."""
        db = self.SessionLocal()
        try:
            db_message = table_class(**message)
            db.add(db_message)
            db.commit()
            db.refresh(db_message)
        except Exception as e:
            db.rollback()
            logging.critical(f"Database Save Error: {e}")
            raise e
        finally:
            db.close()