import database
from config import *
import pymysql
from sshtunnel import SSHTunnelForwarder


def connect_to_server():
    server = SSHTunnelForwarder(
        (host, port),
        ssh_username=user,
        ssh_password=passwd,
        remote_bind_address=('127.0.0.1', 3306)
    )
    server.start()
    return server


class SqlDb:
    def __init__(self):
        global server, con
        server = connect_to_server()

        con, cursor = self.connect_to_mysql()  # Присоединяемся к удаленному серверу.
        print(f"Successfully connected to серверу")
        database.connect()
        database.create_table()

        self.get_tables()

    @classmethod
    def get_table_info(cls, table: str, time: str) -> str:
        cursor = SqlDb.connect_to_mysql()[1]
        cursor.execute(f"USE {db_name}")  # Подключаемся к нужному .db файлу.
        cursor.execute(f"SELECT `label`, `count` FROM `{table}`")
        res = cursor.fetchall()
        result_str = f"<b>Заказ номер {table.upper()}:</b>\nВремя заказа:    {time}"
        for order in res:
            label, count = order
            result_str += f"\n    <em>{label}    {count} шт.</em>"
        return result_str

    @staticmethod
    def connect_to_mysql():
        global server
        # try:
        con = pymysql.connect(
            host='127.0.0.1',
            user=user, passwd=passwd,
            db=db_name,
            port=server.local_bind_port
                )  # Подключаемся к базе данных.
        # except Exception:
        #     time.sleep(20)
        #     server.close()
        #     return SqlDb.connect_to_server()
        cur = con.cursor()
        return con, cur

    @staticmethod
    def get_tables() -> list:
        cursor = SqlDb.connect_to_mysql()[1]
        cursor.execute(f"USE {db_name}")  # Подключаемся к нужному .db файлу.
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        tables_array = []
        for table in tables:
            tables_array.append(table[0])
        database.set_table(tables_array)
        return tables_array

    @staticmethod
    def close_connect():
        try:
            con.close()
        except Exception:
            return
