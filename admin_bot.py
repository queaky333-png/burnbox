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
import urllib.request

# ==========================================================================
# 👑 НАСТРОЙКИ АДМИН-БОТА
# ==========================================================================
ADMIN_TOKEN = "8729007201:AAHIfqw9NmKSa7tEGfEF3AytaN9zc9d8hXU"
bot = telebot.TeleBot(ADMIN_TOKEN)

# ==========================================================================
# 🌍 НАСТРОЙКИ СЕРВЕРА
# ==========================================================================
API_BASE = "https://USERNAME.pythonanywhere.com"  # ← адрес бэкенда в облаке
ADMIN_KEY = "0bec47b3339752c8e30c3468"             # ← общий секрет с server.py

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
    "<code>/srv</code> — локальный сервер (для dev)"
)


def api_post(path, payload):
    """POST-запрос к бэкенду"""
    req = urllib.request.Request(
        API_BASE + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ==========================================================================
# ⚙️ СЕРВЕР LOCAL: ЗАПУСК / ОСТАНОВКА / СТАТУС / ССЫЛКА (для разработки)
# ==========================================================================

def get_lan_ip():
    """Определяет локальный IP компьютера в сети (предпочитает домашний Wi-Fi/Ethernet)"""
    ip_pool = []
    try:
        ipcfg = subprocess.run(
            ["ipconfig"], capture_output=True, text=True, encoding="utf-8", errors="replace"
        ).stdout
        for m in re.finditer(r"IPv4[^\n:]*:\s*([0-9.]+)", ipcfg):
            ip = m.group(1)
            if ip not in ip_pool:
                ip_pool.append(ip)
    except Exception:
        pass

    # Приоритет: 192.168.* (домашняя сеть) > 10.* > 172.16-31.* > прочее
    def rank(ip):
        if ip.startswith("192.168."):
            return 0
        if ip.startswith("10."):
            return 1
        if ip.startswith("172."):
            try:
                b = int(ip.split(".")[1])
                if 16 <= b <= 31:
                    return 2
            except Exception:
                pass
        return 3

    if ip_pool:
        return min(ip_pool, key=rank)

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def is_port_open(port=SERVER_PORT, host="127.0.0.1"):
    try:
        with socket.create_connection((host, port), timeout=1.5):
            return True
    except Exception:
        return False


def kill_by_port(port=SERVER_PORT):
    """Убивает процесс, который слушает нужный порт"""
    try:
        result = subprocess.run(
            ['netstat', '-ano'], capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        for line in result.stdout.splitlines():
            if f':{port}' in line and 'LISTENING' in line:
                pid = line.split()[-1]
                subprocess.run(['taskkill', '/PID', pid, '/F'], capture_output=True)
    except Exception:
        pass


def try_allow_firewall(port=SERVER_PORT):
    """Пытается открыть порт в брандмауэре Windows (нужны права админа)"""
    try:
        subprocess.run(
            ['netsh', 'advfirewall', 'firewall', 'add', 'rule',
             f'name=BurnBoxServer{port}', 'dir=in', 'action=allow',
             'protocol=TCP', f'localport={port}'],
            capture_output=True
        )
    except Exception:
        pass


def start_server():
    """Запускает сервер, если он ещё не запущен"""
    global SERVER_PROC
    if is_port_open():
        return "already", None
    try:
        try_allow_firewall()
        SERVER_PROC = subprocess.Popen(
            [sys.executable, "server.py"],
            cwd=BASE_DIR,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        # Ждём до 8 секунд, пока поднимется порт
        for _ in range(16):
            time.sleep(0.5)
            if is_port_open():
                return "started", SERVER_PROC.pid
        return "failed", None
    except Exception as e:
        print(f"Ошибка запуска сервера: {e}")
        return "failed", None


def stop_server():
    """Останавливает сервер"""
    global SERVER_PROC
    if SERVER_PROC and SERVER_PROC.poll() is None:
        try:
            SERVER_PROC.terminate()
            SERVER_PROC.wait(timeout=5)
        except Exception:
            try:
                SERVER_PROC.kill()
            except Exception:
                pass
        SERVER_PROC = None
    # Добиваем всё, что осталось висеть на порту
    kill_by_port(SERVER_PORT)


def start_ngrok(port=SERVER_PORT):
    """Пытается поднять публичный туннель через ngrok"""
    if not shutil.which("ngrok"):
        return None
    try:
        ngrok_proc = subprocess.Popen(
            ["ngrok", "http", str(port), "--log=stdout"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
        # Спрашиваем локальный API ngrok до 10 секунд
        for _ in range(20):
            time.sleep(0.5)
            try:
                with urllib.request.urlopen("http://127.0.0.1:4040/api/tunnels", timeout=2) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                for tunnel in data.get("tunnels", []):
                    pub = tunnel.get("public_url")
                    if pub:
                        return pub
            except Exception:
                continue
        ngrok_proc.terminate()
        return None
    except Exception:
        return None


# ==========================================================================
# ОСНОВНОЙ ФУНКЦИОНАЛ
# ==========================================================================

def is_admin_rank(rank_string):
    return any(r in rank_string.upper() for r in ["HELPER", "MODERATOR", "ADMIN", "OWNER"])


def update_user_field(target_id, field, value):
    """Изменяет поле пользователя через API сервера"""
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
    bot.reply_to(message, "⚙️ <b>Локальный сервер (dev)</b>\nОсновной сервер сейчас в облаке и работает сам.", reply_markup=markup, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data.startswith("srv_"))
def handle_server_callbacks(call):
    action = call.data.split("_", 1)[1]
    chat_id = call.message.chat.id
    msg_id = call.message.message_id

    if action == "start":
        status, pid = start_server()
        if status == "already":
            bot.edit_message_text("ℹ️ Сервер уже запущен.", chat_id, msg_id)
        elif status == "started":
            bot.edit_message_text(f"✅ <b>Сервер запущен!</b> (PID {pid})", chat_id, msg_id, parse_mode="HTML")
        else:
            bot.edit_message_text("❌ Не удалось запустить сервер.\nПроверьте, что не занят порт 5005.", chat_id, msg_id)

    elif action == "stop":
        stop_server()
        bot.edit_message_text("⏹️ Сервер остановлен.", chat_id, msg_id)

    elif action == "status":
        running = is_port_open()
        text = "🟢 <b>Локальный сервер запущен</b>." if running else "🔴 <b>Локальный сервер не запущен.</b>"
        text += "\n\n🌐 Локальный адрес:\n<code>http://{}</code>".format(f"{get_lan_ip()}:{SERVER_PORT}")
        bot.edit_message_text(text, chat_id, msg_id, parse_mode="HTML")

    elif action == "link":
        ip = get_lan_ip()
        text = (
            f"📱 <b>Локальная ссылка:</b>\n"
            f"👉 http://{ip}:{SERVER_PORT}\n\n"
            f"⚠️ Телефон должен быть в <b>одной Wi-Fi сети</b> с компьютером."
        )
        pub_url = start_ngrok()
        if pub_url:
            text += f"\n\n🌍 <b>Публичная ссылка (из любой точки):</b>\n👉 {pub_url}"
        else:
            text += (
                "\n\n💡 Чтобы заходить из любого места, настрой ngrok:\n"
                "<code>ngrok config add-authtoken ТВОЙ_ТОКЕН</code>\n"
                "и нажми «Ссылка» ещё раз."
            )
        bot.edit_message_text(text, chat_id, msg_id, parse_mode="HTML", disable_web_page_preview=True)


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