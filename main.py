import threading
from datetime import datetime
import time
import sys

from Sql_class import SqlDb
from config import *
import database
from handlers import bot, done_markup

import schedule
from icecream import ic

def polling():
    print("polling...")
    database.connect()
    new_tables = SqlDb.get_tables()
    old_tables = database.get_table(new_tables)[1]
    if [table for table in new_tables if table not in old_tables]:
        database.set_old_table(new_tables)
        new_table_list = list(set(new_tables).difference(old_tables))
        time = datetime.now().strftime("%H:%M")
        for table in new_table_list:                                                      
            text = SqlDb.get_table_info(table, time)
            for user in database.get_users_id():           
                bot.send_message(user, text, reply_markup=done_markup(table))

def scheduler():
    schedule.every().minute.do(polling)
    #schedule.every(10).seconds.do(polling)
    while True:
        schedule.run_pending()
        try:
            time.sleep(2)
        except KeyboardInterrupt:
            sys.exit()


    
if __name__ == "__main__":
    obj = SqlDb()
    threading.Thread(target=bot.infinity_polling).start()
    scheduler()