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
    DONE = types.InlineKeyboardButton("Заказ выполнен", callback_data=f"DONE/{table}")
    markup.row(DONE)
    return markup


@bot.message_handler(commands=["start", "set"])
def start_handler(msg):
    database.connect()
    match msg.text.lower():
        case "/start":
            send_msg(msg, "Выполнена команда /start .")
        case "/set":
            database.set_new_user(msg)
            send_msg(msg, "Вы успешно добавлены в базу данных.")



@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if "DONE" in call.data:
        database.connect()
        table = call.data.split("/")[1]
        SqlDb.close_connect()
        connect, cur, server = SqlDb.connect_to_server()
        cur.execute(f"USE {db_name}")
        cur.execute(f"DROP TABLE `{table}`")
        connect.close()
        server.close()
        database.delete_table_from_last(table)
        bot.send_message(call.message.chat.id, f"Заказ <b>{table}</b> успешно удалён из базы данных")



@bot.message_handler()
def jasdjasd(msg):
    bot.send_message(msg.chat.id, msg.text)