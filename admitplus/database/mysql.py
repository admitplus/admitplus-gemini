import logging
import os

import mysql.connector
import mysql.connector.pooling
from dotenv import load_dotenv

load_dotenv()


class MySQLConnector:
    _instance = None
    _pool = None

    def __init__(self):
        if MySQLConnector._instance is not None:
            logging.warning(
                "[MySQL Service] [Init] Direct instantiation detected. Use get_instance() instead."
            )
            raise Exception(
                "[MySQLConnector] Use get_instance() instead of direct instantiation."
            )
        self._create_connection_pool()

    @classmethod
    def get_instance(cls) -> "MySQLConnector":
        if cls._instance is None:
            logging.info("[MySQL Service] [Init] Creating singleton instance.")
            cls._instance = MySQLConnector()
        else:
            logging.info(
                "[MySQL Service] [Init] Returning existing singleton instance."
            )
        return cls._instance

    def _create_connection_pool(self):
        if self._pool is not None:
            return

        try:
            self.mysql_host = os.getenv("MYSQL_HOST")
            self.mysql_user = os.getenv("MYSQL_USER")
            self.mysql_password = os.getenv("MYSQL_PASSWORD")
            self.mysql_database = os.getenv("MYSQL_DATABASE")

            if not all(
                [
                    self.mysql_host,
                    self.mysql_user,
                    self.mysql_password,
                    self.mysql_database,
                ]
            ):
                logging.error(
                    "[MySQL Service] [Init] Missing one or more MySQL environment variables"
                )
                raise ValueError("Missing one or more MySQL environment variables.")

            self._pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name="mypool",
                pool_size=5,
                host=self.mysql_host,
                user=self.mysql_user,
                password=self.mysql_password,
                database=self.mysql_database,
            )
            logging.info(
                "[MySQL Service] [Init] MySQL connection pool created successfully."
            )
        except Exception as e:
            logging.error(f"[MySQL Service] [Init] Error creating connection pool: {e}")
            raise e

    def get_connection(self):
        if self._pool is None:
            self._create_connection_pool()

        try:
            conn = self._pool.get_connection()
            if conn.is_connected():
                logging.info(
                    "[MySQL Service] [Connection] Successfully retrieved a connection from the pool."
                )
                return conn
            else:
                logging.error(
                    "[MySQL Service] [Connection] Failed to retrieve a connection from the pool."
                )
                return None
        except Exception as e:
            logging.error(f"[MySQL Service] [Connection] Error getting connection: {e}")
            return None

    def close_connection(self, conn):
        if conn and conn.is_connected():
            conn.close()
            logging.info("[MySQL Service] [Connection] MySQL connection closed.")
        else:
            logging.warning(
                "[MySQL Service] [Connection] No active connection to close."
            )

    def execute_query(self, query, params=None):
        conn = self.get_connection()
        if not conn:
            return None
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            result = cursor.fetchall()
            conn.commit()
            logging.info(
                f"[MySQL Service] [Query] Successfully executed query: {query}"
            )
            return result
        except Exception as e:
            conn.rollback()
            logging.error(f"[MySQL Service] [Query] Failed to execute query: {e}")
            return None
        finally:
            cursor.close()
            self.close_connection(conn)

    def execute_non_query(self, query, params=None):
        conn = self.get_connection()
        if not conn:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            conn.commit()
            logging.info(
                f"[MySQL Service] [Query] Successfully executed query: {query}"
            )
            return True
        except mysql.connector.Error as e:
            conn.rollback()
            logging.error(f"[MySQL Service] [Query] MySQL Error: {e}")
            logging.error(f"[MySQL Service] [Query] Error Code: {e.errno}")
            logging.error(f"[MySQL Service] [Query] SQL State: {e.sqlstate}")
            logging.error(f"[MySQL Service] [Query] Query: {query}")
            logging.error(f"[MySQL Service] [Query] Parameters: {params}")
            return False
        except Exception as e:
            conn.rollback()
            logging.error(f"[MySQL Service] [Query] Failed to execute non-query: {e}")
            logging.error(f"[MySQL Service] [Query] Query: {query}")
            logging.error(f"[MySQL Service] [Query] Parameters: {params}")
            return False
        finally:
            cursor.close()
            self.close_connection(conn)

    def fetch_one(self, query, params=None):
        conn = self.get_connection()
        if not conn:
            return None
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            result = cursor.fetchone()
            conn.commit()
            logging.info(
                f"[MySQL Service] [Query] Successfully executed query: {query}"
            )
            return result
        except Exception as e:
            conn.rollback()
            logging.error(f"[MySQL Service] [Query] Failed to fetch one: {e}")
            return None
        finally:
            cursor.close()
            self.close_connection(conn)


mysql_connector = MySQLConnector.get_instance()
