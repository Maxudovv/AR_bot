import threading
from datetime import datetime
import time

import pymysql.err
import schedule

from Sql_class import SqlDb
import database
from handlers import bot, inline_markup


def polling():
    # print("polling...")
    database.connect()
    new_tables = SqlDb.get_tables()
    old_tables = database.get_table(new_tables)[1]
    if [table for table in new_tables if table not in old_tables]:
        database.set_old_table(new_tables)
        new_table_list = list(set(new_tables).difference(old_tables))
        times = datetime.now().strftime("%H:%M")
        for table in new_table_list:
            try:
                text = SqlDb.get_table_info(table, times)
            except pymysql.err.ProgrammingError:
                return
            for user in database.get_users_id():
                bot.send_message(user, text, reply_markup=inline_markup(table))
        SqlDb.close_connect()


def scheduler():
    # schedule.every().minute.do(polling)
    schedule.every(15).seconds.do(polling)
    while True:
        schedule.run_pending()
        time.sleep(2)


if __name__ == "__main__":
    obj = SqlDb()
    threading.Thread(target=bot.infinity_polling).start()
    polling()
    scheduler()
    obj.server.close()
