from sqlite3.dbapi2 import SQLITE_ALTER_TABLE
import telebot
from telebot import types

import database
from config import *
from Sql_class import SqlDb


bot = telebot.TeleBot(token=BOT_TOKEN, parse_mode="html")

def send_msg(msg, text, markup=None):
    return bot.send_message(msg.chat.id, text, reply_markup=markup, disable_notification=True)

def done_markup(table: str) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    DONE = types.InlineKeyboardButton("Выполнено", callback_data=f"DONE/{table}")
    markup.row(DONE)
    return markup


@bot.message_handler(commands=["start", "set", "orders"])
def start_handler(msg):
    database.connect()
    match msg.text.lower():
        case "/start":
            send_msg(msg, "Выполнена команда /start .")
        case "/set":
            database.set_new_user(msg)
            send_msg(msg, "Вы успешно добавлены в базу данных.")
        case "/orders":
            text = get_all_tables()
            send_msg(msg, text)


def get_all_tables():
    cursor = SqlDb.connect_to_server()[1]
    cursor.execute(f"USE {db_name}")
    cursor.execute(f"SHOW TABLES")
    tables = cursor.fetchall()
    text = "Невыполненные заказы:"
    for table in tables:
        text += f"\n{table[0]}"
    return text

@bot.message_handler()
def jasdjasd(msg):
    bot.send_message(msg.chat.id, msg.text)


def delete_table_from_main(table: list):
    database.connect()
    SqlDb.close_connect()
    connect, cur, server = SqlDb.connect_to_server()

    cur.execute(f"USE {db_name}")       # Работа с i91881_AR_CAFE_OFFERS
    cur.execute(f"DROP TABLE `{table}`")

    cur.execute(f"USE {db_ready}")# Работа с i91881_ready_orders
    cur.execute(f"INSERT INTO `orders`(`table`) VALUES ({table})")
    connect.commit()
    
    database.delete_table_from_last(table)

    connect.close()
    server.close()
    


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if "DONE" in call.data:
        table = call.data.split("/")[1]
        delete_table_from_main(table)
        bot.send_message(call.message.chat.id, f"Заказ <b>{table}</b> успешно удалён из базы данных")