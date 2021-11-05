import database
from config import *
import pymysql
from sshtunnel import SSHTunnelForwarder


class SqlDb:
    def __init__(self):
        global con, cursor, server

        con, cursor, server = self.connect_to_server() # Присоединяемся к удаленному серверу.
        cursor = con.cursor()
        print(f"Successfully connected to серверу")

        database.connect()
        database.create_table()

        self.get_tables()

    @classmethod
    def get_table_info(cls, table: str, time: str) -> str:
        cursor.execute(f"USE {db_name}") # Подключаемся к нужному .db файлу.
        cursor.execute(f"SELECT `label`, `count` FROM `{table}`")
        res = cursor.fetchall()
        result_str = f"<b>Заказ номер {table}:</b>\nВремя заказа:    {time}"
        for order in res:
            label, count = order
            result_str += f"\n    <em>{label}    {count} шт.</em>"
        return result_str

    @staticmethod
    def connect_to_server():
        server = SSHTunnelForwarder(
            (host, port),
            ssh_username=user,
            ssh_password=passwd,
            remote_bind_address=('127.0.0.1', 3306)
        )
        server.start()
        con = pymysql.connect(
            host='127.0.0.1', 
            user=user, passwd=passwd, 
            db=db_name, 
            port=server.local_bind_port
                ) # Подключаемся к базе данных.
        cur = con.cursor()
        return con, cur, server

    @staticmethod
    def get_tables() -> list:
        cursor.execute(f"USE {db_name}") # Подключаемся к нужному .db файлу.
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        tables_array = []
        for table in tables:
            tables_array.append(table[0])
        database.set_table(tables_array)
        if database.get_table()[1] is None:
            database.set_old_table(tables_array)
        return tables_array

    @staticmethod
    def close_connect():
        con.close()
        server.close()
