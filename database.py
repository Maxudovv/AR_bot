import sqlite3
from pickle import loads, dumps
import datetime

def connect():
    global conn, cursor
    conn = sqlite3.connect("tables.db")
    cursor = conn.cursor()

def create_table():
    cursor.execute("""CREATE TABLE IF NOT EXISTS array_table (
        data BLOB,
        last BLOB
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS new_tables_array (
        data BLOB
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS bot_table(
        id BIGINT, 
        reg_time TEXT
        )""")

    conn.commit()

def new_tables_set_data(array: list):
    if check_data_new_tables():
        cursor.execute("UPDATE new_tables_array SET data=?", (dumps(array),))
    else:
        cursor.execute("INSERT INTO new_tables_array VALUES(?)", (dumps(array),))
    conn.commit()

def get_new_tables() -> list:
    data = cursor.execute("SELECT data FROM new_tables_array").fetchone()
    return loads(data[0])

def check_data_new_tables() -> True | False:
    res = cursor.execute("SELECT data FROM new_tables_array").fetchone()
    return bool(res[0])


def set_table(array: list):
    if check_array()[0]:
        cursor.execute(f"UPDATE array_table SET data=?", (dumps(array),))
    else:
        cursor.execute(f"INSERT INTO array_table(data) VALUES(?)", (dumps(array),))
    conn.commit()

def check_array() -> tuple:
    connect()
    _all = cursor.execute("SELECT last, data FROM array_table").fetchone()
    #data = cursor.execute("SELECT data FROM array_table").fetchall()
    return bool(_all[0]), bool(_all[1])

def get_table(tables_array=[]) -> tuple:
    connect()
    data, last = cursor.execute("SELECT data, last FROM array_table").fetchone()
    if last is not None:
        last = loads(last)
    else:
        set_old_table(tables_array)
        last = get_table()[1]
    return loads(data), last

def set_old_table(array: list):
    if check_array()[1]:
        cursor.execute("UPDATE array_table SET last=?", (dumps(array),))
    else:
        cursor.execute("INSERT INTO array_table(last) VALUES(?)", (dumps(array),))
    conn.commit()

def set_new_user(msg):
    time = datetime.datetime.now().strftime("%d.%m.%y : %H:%M")
    cursor.execute("INSERT INTO bot_table VALUES(?,?)", (msg.chat.id, time))
    conn.commit()

def get_users_id():
    connect()
    result = list()
    res = cursor.execute("SELECT id FROM bot_table").fetchall()
    for el in res:
        result.append(el[0])
    return result

def delete_table_from_last(table: str):
    connect()
    last = get_table()[1]
    cursor.execute("UPDATE array_table SET last=?", (last.remove(table),))
    conn.commit()
