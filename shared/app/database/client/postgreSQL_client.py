# -*- coding: utf-8 -*-
from psycopg2 import pool,sql
import json
import psycopg2

class PostgreSQLClient:
    def __init__(self, host, port, dbname, user, password, minconn=1, maxconn=10):
        self.connection_params = {
            'host': host,
            'port': port,
            'dbname': dbname,
            'user': user,
            'password': password
        }
        self.minconn = minconn
        self.maxconn = maxconn
        self.pool = None

    def connect(self):
        """Veritabanı bağlantı havuzunu oluştur."""
        try:
            self.pool = psycopg2.pool.SimpleConnectionPool(
                self.minconn,
                self.maxconn,
                **self.connection_params
            )
            if self.pool:
                print("PostgreSQL bağlantı havuzu oluşturuldu.")
        except Exception as e:
            print(f"PostgreSQL bağlantı havuzu oluşturma hatası: {e}")
            raise e

    def close_connection(self):
        """Bağlantı havuzunu kapat."""
        if self.pool:
            self.pool.closeall()
            print("PostgreSQL bağlantı havuzu kapatıldı.")

    def create_table(self, table_name):
        """Tabloyu oluştur."""
        create_table_query = sql.SQL("""
            CREATE TABLE IF NOT EXISTS {table} (
                id SERIAL PRIMARY KEY,
                data JSONB
            );
        """).format(table=sql.Identifier(table_name))
        
        conn = None
        try:
            conn = self.pool.getconn()  # Havuzdan bağlantı al
            cursor = conn.cursor()
            cursor.execute(create_table_query)
            conn.commit()
            print(f"{table_name} tablosu oluşturuldu veya zaten mevcut.")
        except Exception as e:
            print(f"Tablo oluşturma hatası: {e}")
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.pool.putconn(conn)  # Bağlantıyı havuza geri koy

    def insert_message(self, table_name, message):
        """Mesajı veritabanına kaydet."""
        conn = None
        try:
            conn = self.pool.getconn()  # Havuzdan bağlantı al
            cursor = conn.cursor()
            query = sql.SQL("INSERT INTO {table} (data) VALUES (%s)").format(
                table=sql.Identifier(table_name)
            )
            cursor.execute(query, [json.dumps(message)])
            conn.commit()
            print("Mesaj veritabanına kaydedildi.")
        except Exception as e:
            print(f"Veritabanı kaydetme hatası: {e}")
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.pool.putconn(conn)  # Bağlantıyı havuza geri koy
