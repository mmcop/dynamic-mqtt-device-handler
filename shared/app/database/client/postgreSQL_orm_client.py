# -*- coding: utf-8 -*-
import threading
import time
from sqlalchemy import create_engine, Table, select,desc,text, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import logging

class PostgreSQLORMClient:
    def __init__(self, host, port, dbname, user, password, check_health, pool_size=3, max_overflow=0, pool_timeout=30, pool_recycle=1800, health_check_interval=60):
        self.database_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
        self.check_health= check_health
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

        # Periyodik sağlık kontrolü için iş parçacığı başlat
        if check_health:
            self.health_check_thread = threading.Thread(target=self._periodic_health_check, args=(health_check_interval,))
            self.health_check_thread.daemon = True
            self.health_check_thread.start()

    def connect(self):
        """Veritabanı bağlantısını başlatır ve bağlantı havuzunu oluşturur."""
        self.engine.connect()
        logging.info("PostgreSQL client and pool created.")

    def close_connection(self):
        """Bağlantı havuzunu kapatır."""
        self._stop_event.set()  # Sağlık kontrolü iş parçacığını durdur
        if self.check_health:
            self.health_check_thread.join()  # İş parçacığının tamamen durmasını bekler
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
            #logging.info("The message is saved in the database")
        except Exception as e:
            db.rollback()
            logging.critical(f"Database Save Error: {e}")
            raise e
        finally:
            db.close()

    def check_database_health(self):
        """Veritabanı sağlığını kontrol eder."""
        with self.engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            if result.scalar() == 1:
                logging.info("The Database is Healthy")
            else:
                logging.critical("Database health Problem")

    def get_pool_status(self):
        """Bağlantı havuzu durumunu döndürür."""
        logging.info(f"Connection Pool Statistic: {self.engine.pool.status()}")

    def _periodic_health_check(self, interval):
        """Veritabanı sağlığını ve havuz durumunu periyodik olarak kontrol eder."""
        while not self._stop_event.is_set():
            try:
                self.check_database_health()
                self.get_pool_status()
            except Exception as e:
                logging.error(f"Database Health Check Error: {e}")
            time.sleep(interval)  # Belirtilen aralıklarla bekle

    def select_from_table_with_model(self, model_class, filters=None, order_by=None, limit=None, offset=None, single=False):
        """Belirtilen model sınıfından veri seçer, dinamik sütun filtreleme, sıralama, limit ve offset uygular.
           Eğer single=True ise, ilk kaydı döner."""
        db = self.SessionLocal()
        try:
            query = select(model_class)

            if filters:
                for column_name, value in filters.items():
                    query = query.where(getattr(model_class, column_name) == value)

            if order_by:
                query = query.order_by(desc(getattr(model_class, order_by)))

            if limit:
                query = query.limit(limit)

            if offset:
                query = query.offset(offset)

            if single:
                result = db.execute(query).scalars().first()
            else:
                result = db.execute(query).scalars().all()

            return result
        except Exception as e:
            logging.critical(f"Database Query Error: {e}")
            raise e
        finally:
            db.close()

    def select_from_table(self, table_name, schema=None, filters=None, order_by=None, limit=None, offset=None):
        """Tablo ve şema ismiyle sorgu yapar, dinamik sütun filtreleme, sıralama, limit ve offset uygular."""
        db = self.SessionLocal()
        try:
            metadata = MetaData()
            table = Table(table_name, metadata, autoload_with=self.engine, schema=schema)

            query = select(table)

            # Dinamik filtreleri uygula
            if filters:
                for column_name, value in filters.items():
                    query = query.where(getattr(table.c, column_name) == value)

            # Dinamik sıralama uygula
            if order_by:
                query = query.order_by(desc(getattr(table.c, order_by)))

            # Dinamik limit uygula
            if limit:
                query = query.limit(limit)

            # Dinamik offset uygula
            if offset:
                query = query.offset(offset)

            result = db.execute(query).fetchall()

            return result, table  # Tablo nesnesini döndürüyoruz
        except Exception as e:
            logging.critical(f"Database Query Error: {e}")
            raise e
        finally:
            db.close()

    def parse_results_to_model(self, results, table):
        """Sorgu sonuçlarını dinamik bir Python sınıfına parse eder."""

        # Dinamik bir model sınıfı oluştur
        class DynamicModel:
            def __init__(self, **entries):
                self.__dict__.update(entries)

            def __repr__(self):
                return f"<DynamicModel {self.__dict__}>"

        parsed_results = []

        # Her bir sonucu dinamik olarak oluşturulan sınıfa parse et
        for row in results:
            row_dict = {column.name: value for column, value in
                        zip(table.columns, row)}  # Tablo nesnesinin sütunlarını kullanıyoruz
            parsed_results.append(DynamicModel(**row_dict))

        return parsed_results
