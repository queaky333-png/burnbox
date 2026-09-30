import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import re
import time
import sys
import subprocess
import socket
import shutil
import json
import urllib.error
import urllib.request

# ==========================================================================
# 👑 НАСТРОЙКИ АДМИН-БОТА
# ==========================================================================
ADMIN_TOKEN = "8729007201:AAHIfqw9NmKSa7tEGfEF3AytaN9zc9d8hXU"
bot = telebot.TeleBot(ADMIN_TOKEN)

# ==========================================================================
# 🌍 НАСТРОЙКИ СЕРВЕРА
# ==========================================================================
CLOUD_API = "https://burnbox-me3b.onrender.com"  # Адрес бэкенда в облаке
LOCAL_API = "http://127.0.0.1:5005"
ADMIN_KEY = os.environ.get('ADMIN_KEY', "0bec47b3339752c8e30c3468")

PLAYER_RANKS = ["PLAYER [ 1 ]", "BASIC [ 2 ]", "STRIKE [ 3 ]", "FLARE [ 4 ]", "SPARK [ 5 ]", "OPHION [ 6 ]"]
ADMIN_RANKS = ["HELPER [ 1 ]", "MODERATOR [ 2 ]", "ADMIN [ 3 ]", "OWNER"]
active_admins = {}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_PORT = 5005
SERVER_PROC = None

PANEL_HELP = (
    "👑 <b>ПАНЕЛЬ УПРАВЛЕНИЯ</b> 👑\n"
    "<code>/users</code> — база\n"
    "<code>/priv [ID]</code> — ранг\n"
    "<code>/balance [ID]</code> — баланс\n"
    "<code>/upg [ID] [x]</code> — удача\n"
    "<code>/ban [ID] [Мин] [Причина]</code> — бан\n"
    "<code>/unban [ID]</code> — разбан\n"
    "<code>/clear</code> — очистка консоли\n"
    "<code>/srv</code> — управление сервером и техработами"
)

def api_bases():
    bases = []
    if CLOUD_API and "USERNAME" not in CLOUD_API:
        bases.append(CLOUD_API)
    bases.append(LOCAL_API)
    return bases

def api_post(path, payload):
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

def is_admin_rank(rank_string):
    return any(r in rank_string.upper() for r in ["HELPER", "MODERATOR", "ADMIN", "OWNER"])

def update_user_field(target_id, field, value):
    try:
        data = api_post("/api/admin/update_field", {
            "key": ADMIN_KEY,
            "target": target_id,
            "field": field,
            "value": value,
        })
        return data.get("status") == "success"
    except Exception:
        return False

def check_auth(message):
    if message.from_user.id not in active_admins:
        bot.reply_to(message, "🛑 <b>Доступ закрыт.</b>\nВведите логин и пароль от сайта:\n<code>Логин:Пароль</code>", parse_mode="HTML")
        return False
    return True

@bot.message_handler(commands=['start'])
def start_auth(message):
    if message.from_user.id in active_admins:
        bot.reply_to(message, PANEL_HELP, parse_mode="HTML")
    else:
        bot.reply_to(message, "🔐 <b>Вход в Панель Управления</b>\nОтправьте: <code>Логин:Пароль</code>\n\n" + PANEL_HELP, parse_mode="HTML")

@bot.message_handler(func=lambda m: ":" in m.text and m.from_user.id not in active_admins)
def process_login(message):
    try:
        login, password = message.text.split(":", 1)
        login, password = login.strip(), password.strip()
        if not login or not password: return
        try:
            data = api_post("/api/admin/auth", {
                "key": ADMIN_KEY,
                "username": login,
                "password": password,
            })
        except Exception:
            bot.reply_to(message, "❌ Сервер недоступен.")
            return
        if data.get("status") == "success":
            rank = data.get("rank", "PLAYER")
            if is_admin_rank(rank):
                active_admins[message.from_user.id] = login
                bot.reply_to(message, f"✅ <b>Вход выполнен!</b>\nРады видеть, {login}\nВведите /help", parse_mode="HTML")
            else:
                bot.reply_to(message, "❌ Нет прав администратора.")
        else:
            bot.reply_to(message, "❌ Неверные данные.")
    except Exception:
        bot.reply_to(message, "⚠️ Ошибка формата. Нужно: <code>Логин:Пароль</code>", parse_mode="HTML")

@bot.message_handler(commands=['help'])
def admin_help(message):
    if not check_auth(message): return
    bot.reply_to(message, PANEL_HELP, parse_mode="HTML")

@bot.message_handler(commands=['srv'])
def server_menu(message):
    if not check_auth(message): return
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("▶️ Запустить", callback_data="srv_start"),
        InlineKeyboardButton("⏹️ Остановить", callback_data="srv_stop"),
        InlineKeyboardButton("📡 Статус", callback_data="srv_status"),
        InlineKeyboardButton("📱 Ссылка", callback_data="srv_link"),
    )
    bot.reply_to(message, "⚙️ <b>Управление сервером (Техработы)</b>", reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("srv_"))
def handle_server_callbacks(call):
    action = call.data.split("_", 1)[1]
    chat_id = call.message.chat.id
    msg_id = call.message.message_id

    if action == "start":
        try:
            res = api_post("/api/admin/toggle_maintenance", {"key": ADMIN_KEY, "action": "off"})
            if res.get("status") == "success":
                bot.edit_message_text("✅ <b>Сервер запущен!</b>\nДоступ для игроков открыт.", chat_id, msg_id, parse_mode="HTML")
            else:
                bot.edit_message_text("❌ Ошибка при включении.", chat_id, msg_id)
        except Exception:
            bot.edit_message_text("❌ Сервер недоступен.", chat_id, msg_id)

    elif action == "stop":
        try:
            res = api_post("/api/admin/toggle_maintenance", {"key": ADMIN_KEY, "action": "on"})
            if res.get("status") == "success":
                bot.edit_message_text("⏹️ <b>Сервер остановлен!</b>\nВключен режим технических работ.", chat_id, msg_id, parse_mode="HTML")
            else:
                bot.edit_message_text("❌ Ошибка при остановке.", chat_id, msg_id)
        except Exception:
            bot.edit_message_text("❌ Сервер недоступен.", chat_id, msg_id)

    elif action == "status":
        try:
            res = api_post("/api/admin/toggle_maintenance", {"key": ADMIN_KEY, "action": "status"})
            is_maint = res.get("maintenance", False)
            text = "🔴 <b>Сервер на тех. обслуживании (Остановлен)</b>" if is_maint else "🟢 <b>Сервер работает в штатном режиме</b>"
            bot.edit_message_text(text, chat_id, msg_id, parse_mode="HTML")
        except Exception:
            bot.edit_message_text("🔴 <b>Сервер полностью недоступен (Лежит).</b>", chat_id, msg_id, parse_mode="HTML")

    elif action == "link":
        bot.edit_message_text(f"🌍 <b>Ссылка на проект:</b>\n👉 {CLOUD_API}", chat_id, msg_id, parse_mode="HTML", disable_web_page_preview=True)

@bot.message_handler(commands=['users'])
def show_all_users(message):
    if not check_auth(message): return
    try:
        data = api_post("/api/admin/users", {"key": ADMIN_KEY})
    except Exception:
        bot.reply_to(message, "❌ Сервер недоступен.")
        return
    content = data.get("content", "").strip()
    if not content:
        bot.reply_to(message, "📂 База данных пока пуста.")
        return
    if len(content) > 4000:
        import io
        doc = io.BytesIO(content.encode("utf-8"))
        doc.name = "users.txt"
        bot.send_document(message.chat.id, doc, caption="📂 База")
    else:
        bot.reply_to(message, f"📋 <b>База:</b>\n\n{content}", parse_mode="HTML")

@bot.message_handler(commands=['upg'])
def cmd_upg(message):
    if not check_auth(message): return
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ Использование: <code>/upg [ID] [x]</code>\nПример: <code>/upg WEB-12345678 2.5</code>", parse_mode="HTML")
        return
    multiplier = args[2].replace(",", ".") if len(args) > 2 else "100.0"
    if update_user_field(args[1], "Удача", multiplier): bot.reply_to(message, f"🍀 Удача для <code>{args[1]}</code>: <b>х{multiplier}</b>", parse_mode="HTML")
    else: bot.reply_to(message, "❌ Пользователь не найден в базе.", parse_mode="HTML")

@bot.message_handler(commands=['balance'])
def cmd_balance(message):
    if not check_auth(message): return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "⚠️ Использование: <code>/balance [ID]</code>", parse_mode="HTML")
        return
    markup = InlineKeyboardMarkup().add(InlineKeyboardButton("💰 Изменить", callback_data=f"editbal_{args[1]}"))
    bot.reply_to(message, f"👤 <b>ID:</b> <code>{args[1]}</code>\nНажмите кнопку для изменения:", reply_markup=markup, parse_mode="HTML")

@bot.message_handler(commands=['ban'])
def cmd_ban(message):
    if not check_auth(message): return
    args = message.text.split(maxsplit=3)
    if len(args) < 4:
        bot.reply_to(message, "⚠️ Использование: <code>/ban [ID] [Минуты] [Причина]</code>\nПример: <code>/ban WEB-12345678 60 Обман</code>", parse_mode="HTML")
        return
    try: minutes = int(args[2])
    except ValueError:
        bot.reply_to(message, "❌ Ошибка: Время должно быть числом!")
        return

    ban_until = int(time.time()) + (minutes * 60)
    if update_user_field(args[1], "Бан_до", str(ban_until)) and update_user_field(args[1], "Бан_причина", args[3]):
        bot.reply_to(message, f"🔨 <code>{args[1]}</code> забанен на {minutes} мин.\nПричина: {args[3]}", parse_mode="HTML")
    else:
        bot.reply_to(message, "❌ Пользователь не найден в базе.", parse_mode="HTML")

@bot.message_handler(commands=['unban'])
def cmd_unban(message):
    if not check_auth(message): return
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ Использование: <code>/unban [ID]</code>", parse_mode="HTML")
        return
    if update_user_field(args[1], "Бан_до", "0"): bot.reply_to(message, f"🕊 <code>{args[1]}</code> разбанен!", parse_mode="HTML")
    else: bot.reply_to(message, "❌ Пользователь не найден в базе.", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("editbal_"))
def callback_editbal(call):
    msg = bot.edit_message_text(f"✍️ Напишите новую сумму:", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, lambda m: update_user_field(call.data.split("_")[1], "Баланс", m.text.strip()) and bot.reply_to(m, "✅ Изменено!"))

@bot.message_handler(commands=['priv'])
def open_privilege_menu(message):
    if not check_auth(message): return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "⚠️ Использование: <code>/priv [ID]</code>", parse_mode="HTML")
        return
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(*[InlineKeyboardButton(text=r, callback_data=f"setrank_{args[1]}_{r}") for r in PLAYER_RANKS])
    bot.reply_to(message, f"👤 Привилегия для <code>{args[1]}</code>:", reply_markup=markup, parse_mode="HTML")

@bot.message_handler(commands=['clear'])
def cmd_clear(message):
    if not check_auth(message): return
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
        bot.reply_to(message, "🧹 Консоль очищена.")
    except Exception:
        bot.reply_to(message, "⚠️ Не удалось очистить консоль.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("setrank_"))
def handle_ranks_callbacks(call):
    parts = call.data.split("_", 2)
    update_user_field(parts[1], "Ранг", parts[2])
    bot.edit_message_text(f"✅ Ранг <b>{parts[2]}</b> выдан!", call.message.chat.id, call.message.message_id, parse_mode="HTML")

if __name__ == "__main__":
    bot.infinity_polling()