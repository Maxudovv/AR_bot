import pymysql
import telebot
from telebot import types
from icecream import ic

import database
from config import *
from Sql_class import SqlDb

bot = telebot.TeleBot(token=BOT_TOKEN, parse_mode="html")


def send_msg(msg, text, markup=None):
    return bot.send_message(msg.chat.id, text, reply_markup=markup, disable_notification=True)


def done_markup(table: str) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    done = types.InlineKeyboardButton("Выполнено", callback_data=f"DONE/{table}")
    markup.row(done)
    return markup


@bot.message_handler(commands=["start", "set", "orders"])
def start_handler(msg):
    database.connect()
    text = msg.text.lower()
    if text == "/start":
        send_msg(msg, "Выполнена команда /start .")
    elif text == "/set":
        database.set_new_user(msg)
        send_msg(msg, "Вы успешно добавлены в базу данных.")
    elif text == "/orders":
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
def echo(msg):
    bot.send_message(msg.chat.id, msg.text)


def delete_table_from_main(table: str):
    try:
        SqlDb.close_connect()
    except pymysql.err.Error:
        pass
    connect, cur, server = SqlDb.connect_to_server()

    cur.execute(f"USE {db_name}")  # Работа с i91881_AR_CAFE_OFFERS
    tables_array = SqlDb.get_tables()

    ic(table, tables_array)
    try:
        cur.execute(f"DROP TABLE `{table}`")
    except pymysql.err.OperationalError:
        return

    cur.execute(f"USE {db_ready}")  # Работа с i91881_ready_orders
    cur.execute(f"INSERT INTO `orders`(`name`) VALUES ({table})")
    connect.commit()
    SqlDb.get_tables()
    last = database.get_table()[1]
    database.delete_table_from_last(table, last)

    # SqlDb.close_connect()


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if "DONE" in call.data:
        table = call.data.split("/")[1]
        if table not in SqlDb.get_tables():
            # send_msg(call.message, f"Заказ <b>{table}</b> уже удалён из базы.")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            return
        delete_table_from_main(table)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        users_id = database.get_users_id()
        users_id.remove(int(call.message.chat.id))
        for users_chat_id in users_id:
            bot.send_message(users_chat_id, f"Заказ <b>{table}</b> успешно удалён из базы данных")
