import os
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

_conn = None

def wait_for_db(max_retries=5, delay=3):
    """Ожидание готовности БД с экспоненциальной задержкой"""
    retries = 0
    while retries < max_retries:
        try:
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                port=int(os.getenv("DB_PORT", "5678")),
                dbname=os.getenv("POSTGRES_DB"),
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD"),
                connect_timeout=3
            )
            conn.close()
            print("✅ База данных готова")
            return True
        except psycopg2.OperationalError as e:
            retries += 1
            wait_time = delay * (2 ** retries) 
            print(f"⚠️ Ожидание БД (попытка {retries}/{max_retries}), жду {wait_time} сек...")
            time.sleep(wait_time)
    raise Exception("Не удалось подключиться к БД после нескольких попыток")

def get_connection():
    global _conn
    if _conn is None:
        wait_for_db() 
        
        try:
            _conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                port=int(os.getenv("DB_PORT", "5678")),
                dbname=os.getenv("POSTGRES_DB"),
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD"),
                connect_timeout=5
            )
            _conn.autocommit = True
            print("✅ Установлено подключение к БД")
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            raise
    return _conn