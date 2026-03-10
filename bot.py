import requests
from random import randint
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# =============================
# SETTINGS
# =============================

url = "https://leakosintapi.com/"

bot_token = "8635011829:AAEYu7IRhCqbCsbzh5wgBC929CHTpTwbQCs"
api_token = "7315508984:Eap0hdf9"

lang = "en"
limit = 300

bot = telebot.TeleBot(bot_token)

cash_reports = {}

# =============================
# REPORT GENERATOR
# =============================

def generate_report(query, query_id):

    global cash_reports

    data = {
        "token": api_token,
        "request": query,
        "limit": limit,
        "lang": lang
    }

    try:
        response = requests.post(url, json=data).json()
    except:
        return None

    if "Error code" in response:
        print("API Error:", response["Error code"])
        return None

    cash_reports[str(query_id)] = []

    for database_name in response["List"].keys():

        text = f"<b>{database_name}</b>\n\n"

        if database_name != "No results found":

            for report_data in response["List"][database_name]["Data"]:

                for column_name in report_data:
                    text += f"<b>{column_name}</b>: {report_data[column_name]}\n"

                text += "\n"

        if len(text) > 3500:
            text = text[:3500] + "\n\nSome data truncated"

        cash_reports[str(query_id)].append(text)

    return cash_reports[str(query_id)]

# =============================
# KEYBOARD
# =============================

def create_keyboard(query_id, page, total):

    markup = InlineKeyboardMarkup()

    if total <= 1:
        return markup

    markup.row_width = 3

    markup.add(
        InlineKeyboardButton("<<", callback_data=f"page {query_id} {page-1}"),
        InlineKeyboardButton(f"{page+1}/{total}", callback_data="ignore"),
        InlineKeyboardButton(">>", callback_data=f"page {query_id} {page+1}")
    )

    return markup

# =============================
# START COMMAND
# =============================

@bot.message_handler(commands=['start'])
def start(message):

    bot.reply_to(
        message,
        "🔎 LeakOSINT Search Bot\n\nSend phone number, email, or username."
    )

# =============================
# SEARCH HANDLER
# =============================

@bot.message_handler(func=lambda message: True)
def search(message):

    wait_msg = bot.reply_to(message, "🔎 Searching... please wait")

    query_id = randint(100000,999999)

    report = generate_report(message.text, query_id)

    if report is None:
        bot.edit_message_text(
            "⚠️ API Error",
            wait_msg.chat.id,
            wait_msg.message_id
        )
        return

    markup = create_keyboard(query_id,0,len(report))

    bot.edit_message_text(
        report[0],
        wait_msg.chat.id,
        wait_msg.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

# =============================
# PAGE HANDLER
# =============================

@bot.callback_query_handler(func=lambda call: True)
def page_handler(call):

    if call.data.startswith("page"):

        _,query_id,page = call.data.split()

        page = int(page)

        reports = cash_reports.get(query_id)

        if not reports:
            bot.answer_callback_query(call.id,"Expired")
            return

        if page < 0:
            page = len(reports)-1
        if page >= len(reports):
            page = 0

        markup = create_keyboard(query_id,page,len(reports))

        bot.edit_message_text(
            reports[page],
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=markup
        )

print("Bot Started...")

bot.infinity_polling()
