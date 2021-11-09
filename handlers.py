import time

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


def inline_markup(table: str = None, _exit=None) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    if _exit:
        conf = types.InlineKeyboardButton("+", callback_data="delete")
        ref = types.InlineKeyboardButton("-", callback_data="not delete")
        return markup.row(conf, ref)
    if table:
        done = types.InlineKeyboardButton("Выполнено", callback_data=f"DONE/{table}")
        markup.row(done)
    else:
        confirm = types.InlineKeyboardButton("Подтвердить", callback_data="login")
        refuse = types.InlineKeyboardButton("Отказаться", callback_data="refuse")
        markup.row(confirm, refuse)
    return markup


def reply_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item = types.KeyboardButton("/заказы")
    item2 = types.KeyboardButton("/помощь")
    item_last = types.KeyboardButton("/выйти")
    markup.row(item, item2)
    markup.add(item_last)
    return markup


@bot.message_handler(content_types=["text"])
def start_handler(msg):
    database.connect()
    text = msg.text.lower()
    if text == "/start":
        if msg.chat.id not in database.get_users_id():
            send_msg(msg, "Бот для работы с кафе, для начала работы вводите /set")
        else:
            send_msg(msg, "Бот запущен, для получения помощи вводите /help.")
        return
    elif text == "/set":
        if msg.chat.id not in database.get_users_id():
            send_msg(msg,
                     f"<b>Имя:</b> {msg.from_user.first_name}\n<b>Фамиля: </b>{msg.from_user.last_name}"
                     f"\n<b>ID: </b><code>{msg.from_user.id}</code>\nПодвердите регистрацию.",
                     markup=inline_markup()
                     )
        else:
            send_msg(msg, "Вы уже зарегестрированы и можете продолжать работу", reply_markup())
        return
    if msg.chat.id in database.get_users_id():
        if text == "/orders" or text == "/заказы":
            text_message = get_all_tables()
            send_msg(msg, text_message)
            SqlDb.close_connect()

        elif text == "/выйти":
            send_msg(msg, "Вы уверены, что хотите прекратить работу с ботом?\nВы сможете начать работать снова позже.",
                     markup=inline_markup(_exit=True))

        elif text == "/помощь" or text == "/help":
            message_text = """/start - Начать работу с ботом (необязательно)
/set - Зарегестрироваться для работы
/orders | /заказы - Получить список невыполненных заказов
/выйти - Прекратить работу с ботом
/help | /помощь - получить помощь.

Если вы столкнулись с проблемой при работе с ботом, просим вас связаться с владельцем бота - @IDeives"""
            send_msg(msg, message_text)

        elif "/done" in text:
            if len(text.split()) <= 1:
                send_msg(msg, "Вводите команду <code>/done {название заказа}</code> без символов <code>{ }</code>")
                return
            table = text.split()[1]
            if check_table_exists(table):
                delete_table_from_main(table)
                send_msg(msg, f"Заказ {table.upper()} успешно выполнен")
                mailing(msg, table)
            else:
                send_msg(msg, f'Не существует заказа {table.upper()}, для получения списков заказов вводите /orders')
        else:
            table = msg.text.lower()
            if check_table_exists(table):
                text_message = SqlDb.get_table_info(table)
                send_msg(msg, text_message, inline_markup(table))
            else:
                send_msg(msg, f'Не существует заказа {table.upper()}, для получения списков заказов вводите /orders')
    else:
        send_msg(msg, "Вы не зарегестрированы в базе данных. Для регистрации вводите команду /set")


def get_all_tables():
    tables = SqlDb.get_tables()
    if not tables:
        return "Нет невыполненных заказов."
    text = "Невыполненные заказы:"
    for table in tables:
        text += f"\n{table[0].upper()}"
    return text


def delete_table_from_main(table: str):
    try:
        SqlDb.close_connect()
    except pymysql.err.Error:
        pass
    connect, cur = SqlDb.connect_to_mysql()

    cur.execute(f"USE {db_name}")  # Работа с i91881_AR_CAFE_OFFERS

    try:
        cur.execute(f"DROP TABLE `{table}`")
    except pymysql.err.OperationalError:
        return
    cur.execute(f"DELETE FROM `comments` WHERE name=\"{table}\"")

    cur.execute(f"USE {db_ready}")  # Работа с i91881_ready_orders
    cur.execute(f"INSERT INTO orders (`name`) VALUES (%s)", table)
    connect.commit()
    SqlDb.get_tables()
    last = database.get_table()[1]
    database.delete_table_from_last(table, last)


def check_table_exists(table):
    SqlDb.connect_to_mysql()
    tables_array = SqlDb.get_tables()
    return table in tables_array


def mailing(msg, table):
    users_id = database.get_users_id()
    users_id.remove(int(msg.chat.id))
    for users_chat_id in users_id:
        bot.send_message(users_chat_id, f"Заказ <b>{table.upper()}</b> успешно удалён из базы данных")


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if "DONE" in call.data:
        table = call.data.split("/")[1]
        if table not in SqlDb.get_tables():
            bot.delete_message(call.message.chat.id, call.message.message_id)
            return
        delete_table_from_main(table)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        mailing(call.message, table)

    elif "login" in call.data:
        database.set_new_user(call.message)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_msg(call.message,
                 "Вы успешно зарегестрированы, можете начать работу с ботом.\nДля получения помощи вводите /help",
                 markup=reply_markup())

    elif "refuse" in call.data:
        bot.edit_message_text("Регистрация прервана", call.message.chat.id, call.message.message_id)

    elif call.data == "delete":
        database.delete_user(call.message)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True).row(types.KeyboardButton("/start"),
                                                                     types.KeyboardButton("/set"))
        bot.delete_message(call.message.chat.id, call.message.message_id)
        time.sleep(0.5)
        send_msg(call.message, "Ваша сессия работы с ботом прекращена, вы можете начать её снова командой /set.",
                 markup=markup)

    elif call.data == "not delete":
        bot.edit_message_text("Команда удаления прервана.", call.message.chat.id, call.message.message_id)

    SqlDb.close_connect()
