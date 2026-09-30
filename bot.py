import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import urllib.error
import urllib.parse
import urllib.request
import json

# ==========================================================================
# 🔑 ТОКЕН ОСНОВНОГО БОТА (ДЛЯ ИГРОКОВ)
# ==========================================================================
TOKEN = "8835861254:AAGVGXqoEjADMcSA6IHJ8btbXum-Wr-PUdY"

bot = telebot.TeleBot(TOKEN)

# ==========================================================================
# 🌍 НАСТРОЙКИ СЕРВЕРА И САЙТА
# ==========================================================================
CLOUD_API = "https://burnbox-me3b.onrender.com"  # ← адрес бэкенда в облаке
LOCAL_API = "http://127.0.0.1:5005"
SITE_URL = "https://adorable-druid-8f7a9c.netlify.app"  # ← твой фронт на Netlify


def api_bases():
    """Облако, если адрес реальный, иначе сразу локальный сервер"""
    bases = []
    if CLOUD_API and "USERNAME" not in CLOUD_API:
        bases.append(CLOUD_API)
    bases.append(LOCAL_API)
    return bases


def api_post(path, payload):
    """POST-запрос к бэкенду: облако, при недоступности — локальный сервер"""
    last = None
    for base in api_bases():
        try:
            req = urllib.request.Request(
                base + path,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError:
            raise
        except Exception as e:
            last = e
    raise last


@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = "🔥 <b>Добро пожаловать в BurnBox Vault!</b> 🔥\n\nЧтобы увидеть список доступных команд, введи команду /help"
    bot.reply_to(message, welcome_text, parse_mode="HTML")


@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "🔥 <b>Список команд</b> 🔥\n"
        "/help - список всех команд\n"
        "/reg - регистрация\n"
        "/ent - вход в аккаунт\n"
        "/q - выход из аккаунта"
    )
    bot.reply_to(message, help_text, parse_mode="HTML")


@bot.message_handler(commands=['reg'])
def send_reg_info(message):
    reg_text = "📝 <b>Регистрация аккаунта</b>\n\nЧтобы зарегистрироваться, пришли данные <b>строго через двоеточие (без пробелов)</b>:\n\n<code>логин:пароль</code>"
    bot.reply_to(message, reg_text, parse_mode="HTML")


@bot.message_handler(commands=['ent'])
def send_ent_info(message):
    ent_text = f"🔑 <b>Вход в аккаунт</b>\n\nНажмите на ссылку ниже:\n👉 <a href='{SITE_URL}'>ОТКРЫТЬ BURNBOX VAULT</a>"
    bot.reply_to(message, ent_text, parse_mode="HTML", disable_web_page_preview=True)


@bot.message_handler(commands=['q'])
def send_logout_confirm(message):
    markup = InlineKeyboardMarkup()
    btn_yes = InlineKeyboardButton("✅ Да, выйти", callback_data="logout_yes")
    btn_no = InlineKeyboardButton("❌ Отмена", callback_data="logout_no")
    markup.add(btn_yes, btn_no)
    bot.reply_to(message, "⚠️ <b>Вы уверены, что хотите отвязать свой аккаунт от Telegram?</b>", reply_markup=markup, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data.startswith("logout_"))
def callback_logout(call):
    if call.data == "logout_no":
        bot.edit_message_text("Действие отменено.", chat_id=call.message.chat.id, message_id=call.message.message_id)
    elif call.data == "logout_yes":
        try:
            result = api_post("/api/tg_logout", {"tg_id": call.from_user.id})
            is_logged_out = result.get("status") == "success"
        except Exception:
            is_logged_out = False
        if is_logged_out:
            bot.edit_message_text("✅ Вы успешно вышли из аккаунта. Ваш Telegram больше не привязан к профилю.", chat_id=call.message.chat.id, message_id=call.message.message_id)
        else:
            bot.edit_message_text("❌ У вас нет привязанного аккаунта.", chat_id=call.message.chat.id, message_id=call.message.message_id)


@bot.message_handler(func=lambda message: True)
def handle_registration(message):
    text = message.text.strip()
    if ":" not in text:
        bot.reply_to(message, "❌ Неверный формат. Нужно: <code>логин:пароль</code>", parse_mode="HTML")
        return

    data = text.split(":", 1)
    username = data[0].strip()
    password = data[1].strip()

    if not username or not password:
        bot.reply_to(message, "❌ Логин или пароль не могут быть пустыми!", parse_mode="HTML")
        return

    # Отправляем регистрацию на сервер (база живёт в облаке)
    try:
        result = api_post("/api/tg_register", {
            "tg_id": message.from_user.id,
            "username": username,
            "password": password,
        })
    except Exception:
        bot.reply_to(message, "❌ Сервер недоступен. Попробуйте позже.", parse_mode="HTML")
        return

    if result.get("status") == "error":
        text_error = result.get("message", "Не удалось зарегистрироваться.")
        if "занят" in text_error.lower():
            bot.reply_to(message, f"⚠️ <b>Этот логин уже занят!</b> Придумайте другой.", parse_mode="HTML")
        else:
            bot.reply_to(message, f"❌ {text_error}", parse_mode="HTML")
        return

    # Кодируем данные для безопасной передачи в ссылке
    encoded_user = urllib.parse.quote(username)
    encoded_pass = urllib.parse.quote(password)
    activation_link = f"{SITE_URL}?reg_user={encoded_user}&reg_pass={encoded_pass}"

    success_text = (
        "✅ <b>Регистрация успешна!</b>\n\n"
        f"👤 Логин: <code>{username}</code>\n"
        f"🔑 Пароль: <code>{password}</code>\n\n"
        f"👉 <a href='{activation_link}'>ПОДТВЕРДИТЬ РЕГИСТРАЦИЮ НА САЙТЕ</a>"
    )
    bot.reply_to(message, success_text, parse_mode="HTML", disable_web_page_preview=True)


if __name__ == "__main__":
    print("🎮 Игровой бот запущен!")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"Произошла ошибка во время работы бота: {e}")