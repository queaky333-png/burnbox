from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import random
import re
import time
import requests  # <-- Новая библиотека для отправки сообщений

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

DB_FILE = "users.txt"

# ==========================================
# 🤖 ВСТАВЬ СЮДА ТОКЕН ТВОЕГО ОСНОВНОГО БОТА
# ==========================================
BOT_TOKEN = "8835861254:AAGVGXqoEjADMcSA6IHJ8btbXum-Wr-PUdY" 

# Общий секрет для доступа ботов к админ-функциям сервера
ADMIN_KEY = "0bec47b3339752c8e30c3468" 

def send_tg_message(chat_id, text):
    """Функция для отправки сообщения пользователю от имени бота"""
    if not BOT_TOKEN or BOT_TOKEN == "ТВОЙ_ТОКЕН_БОТА": 
        return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=3)
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")

def init_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            pass

def parse_user_data(line):
    data = {"rank": "PLAYER [ 1 ]", "balance": 1250.0, "luck": 1.0, "inventory": [], "banned": False, "ban_until": 0, "ban_reason": ""}
    
    if " | Ранг: " in line:
        data["rank"] = line.split(" | Ранг: ")[1].split(" |")[0].strip()
        
    bal_match = re.search(r"\|\s*Баланс:\s*([0-9.]+)", line)
    if bal_match: data["balance"] = float(bal_match.group(1))
    
    luck_match = re.search(r"\|\s*Удача:\s*([0-9.]+)", line)
    if luck_match: data["luck"] = float(luck_match.group(1))
    
    inv_match = re.search(r"\|\s*Инвентарь:\s*([0-9,]+)", line)
    if inv_match:
        data["inventory"] = [int(x) for x in inv_match.group(1).split(",") if x.isdigit()]
        
    ban_match = re.search(r"\|\s*Бан_до:\s*([0-9.]+)", line)
    if ban_match:
        ban_until = float(ban_match.group(1))
        if time.time() < ban_until:
            data["banned"] = True
            data["ban_until"] = ban_until
            reason_match = re.search(r"\|\s*Бан_причина:\s*([^|]+)", line)
            if reason_match: data["ban_reason"] = reason_match.group(1).strip()
            
    return data

@app.route('/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS': return '', 200
    data = request.get_json(force=True) or {}
    username, password = data.get('username', '').strip(), data.get('password', '').strip()
    if not username or not password: return jsonify({"status": "error"}), 400
    init_db()
    with open(DB_FILE, "r", encoding="utf-8") as f:
        if any(f"Логин: {username} |" in line for line in f): return jsonify({"status": "error", "message": "⚠️ Логин занят!"}), 400
    web_id = f"WEB-{random.randint(10000000, 99999999)}"
    with open(DB_FILE, "a", encoding="utf-8") as f:
        f.write(f"ID: {web_id} | Логин: {username} | Пароль: {password} | Ранг: PLAYER [ 1 ] | Баланс: 1250 | Удача: 1.0 | Инвентарь: 101,103,104\n")
    return jsonify({"status": "success"})

@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS': return '', 200
    data = request.get_json(force=True) or {}
    username, password = data.get('username', '').strip(), data.get('password', '').strip()
    init_db()
    
    with open(DB_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in reversed(lines):
            if f"Логин: {username} | Пароль: {password} |" in line:
                user_data = parse_user_data(line)
                if user_data["banned"]: 
                    return jsonify({"status": "banned", "ban_until": user_data["ban_until"], "ban_reason": user_data["ban_reason"]}), 403
                return jsonify({"status": "success", "rank": user_data["rank"], "balance": user_data["balance"], "luck": user_data["luck"], "inventory": user_data["inventory"]}), 200
                
    return jsonify({"status": "error", "message": "❌ Неверные данные!"}), 401

# --- СИСТЕМА АВТОРИЗАЦИИ ТЕЛЕГРАМ С УВЕДОМЛЕНИЯМИ ---
@app.route('/tg_auth', methods=['POST', 'OPTIONS'])
def tg_auth():
    if request.method == 'OPTIONS': return '', 200
    data = request.get_json(force=True) or {}
    tg_id = str(data.get('tg_id', '')).strip()
    username = data.get('username', '').strip()
    first_name = data.get('first_name', 'Игрок').strip()
    
    if not tg_id: return jsonify({"status": "error"}), 400
    
    display_name = username if username else first_name
    search_id = f"TG-{tg_id}"
    
    init_db()
    user_line = None
    with open(DB_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in reversed(lines):
            if f"ID: {search_id} |" in line:
                user_line = line
                break
                
    if user_line:
        user_data = parse_user_data(user_line)
        if user_data["banned"]:
            return jsonify({"status": "banned", "ban_until": user_data["ban_until"], "ban_reason": user_data["ban_reason"]}), 403
            
        # Отправляем сообщение об успешном входе в бота
        send_tg_message(tg_id, "✅ <b>Успешная авторизация!</b>\nВы вошли в систему BurnBox.")
        
        return jsonify({
            "status": "success", "username": display_name, "rank": user_data["rank"],
            "balance": user_data["balance"], "luck": user_data["luck"], "inventory": user_data["inventory"]
        }), 200
    else:
        with open(DB_FILE, "a", encoding="utf-8") as f:
            f.write(f"ID: {search_id} | Логин: {display_name} | Пароль: TG_AUTH | Ранг: PLAYER [ 1 ] | Баланс: 1250 | Удача: 1.0 | Инвентарь: 101,103,104\n")
            
        # Отправляем сообщение об успешной регистрации
        send_tg_message(tg_id, "🎉 <b>Регистрация успешна!</b>\nВам начислено 1250 $B и стартовые предметы.\nДобро пожаловать в BurnBox!")
        
        return jsonify({
            "status": "success", "username": display_name, "rank": "PLAYER [ 1 ]",
            "balance": 1250.0, "luck": 1.0, "inventory": [101, 103, 104]
        }), 200

@app.route('/get_rank', methods=['POST', 'OPTIONS'])
def get_rank():
    if request.method == 'OPTIONS': return '', 200
    data = request.get_json(force=True) or {}
    username = data.get('username', '').strip()
    init_db()
    with open(DB_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in reversed(lines):
            if f"Логин: {username} |" in line:
                user_data = parse_user_data(line)
                if user_data["banned"]: 
                    return jsonify({"status": "banned", "ban_until": user_data["ban_until"], "ban_reason": user_data["ban_reason"]}), 403
                return jsonify({"status": "success", "rank": user_data["rank"], "balance": user_data["balance"], "luck": user_data["luck"], "inventory": user_data["inventory"]}), 200
    return jsonify({"status": "error"}), 404

@app.route('/update_progress', methods=['POST', 'OPTIONS'])
def update_progress():
    if request.method == 'OPTIONS': return '', 200
    data = request.get_json(force=True) or {}
    username = data.get('username')
    balance = data.get('balance')
    inventory = data.get('inventory', [])
    inv_str = ",".join(map(str, inventory))
    
    with open(DB_FILE, "r", encoding="utf-8") as f: lines = f.readlines()
    new_lines = []
    found = False
    for line in lines:
        if f"Логин: {username} |" in line:
            found = True
            if "| Баланс:" in line: line = re.sub(r"\|\s*Баланс:\s*[0-9.]+", f"| Баланс: {balance}", line)
            else: line = line.strip() + f" | Баланс: {balance}\n"
            
            if "| Инвентарь:" in line: line = re.sub(r"\|\s*Инвентарь:\s*[0-9,]*", f"| Инвентарь: {inv_str}", line)
            else: line = line.strip() + f" | Инвентарь: {inv_str}\n"
        new_lines.append(line)
        
    if found:
        with open(DB_FILE, "w", encoding="utf-8") as f: f.writelines(new_lines)
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 404

# ==========================================================================
# 🔌 API ДЛЯ БОТОВ (единая база users.txt живёт на сервере)
# ==========================================================================

def _get_json():
    return request.get_json(force=True) or {}


def _remove_user_by_id(target_id):
    """Удаляет строку пользователя по ID: xxx"""
    init_db()
    with open(DB_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    new_lines = [l for l in lines if f"ID: {target_id} |" not in l]
    if len(new_lines) != len(lines):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        return True
    return False


@app.route('/api/tg_register', methods=['POST', 'OPTIONS'])
def api_tg_register():
    """Регистрация пользователя из игрового бота (ID = tg_id)"""
    if request.method == 'OPTIONS': return '', 200
    data = _get_json()
    tg_id = str(data.get('tg_id', '')).strip()
    username, password = data.get('username', '').strip(), data.get('password', '').strip()
    if not tg_id or not username or not password:
        return jsonify({"status": "error", "message": "Нет данных"}), 400

    init_db()
    with open(DB_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for line in lines:
        if f"Логин: {username} |" in line and f"ID: {tg_id} |" not in line:
            return jsonify({"status": "error", "message": "Этот логин уже занят!"}), 400

    _remove_user_by_id(tg_id)  # перезаписываем свой же старый аккаунт
    with open(DB_FILE, "a", encoding="utf-8") as f:
        f.write(f"ID: {tg_id} | Логин: {username} | Пароль: {password} | Ранг: PLAYER [ 1 ]\n")
    return jsonify({"status": "success"})


@app.route('/api/tg_logout', methods=['POST', 'OPTIONS'])
def api_tg_logout():
    """Отвязка аккаунта по tg_id"""
    if request.method == 'OPTIONS': return '', 200
    data = _get_json()
    tg_id = str(data.get('tg_id', '')).strip()
    if not tg_id:
        return jsonify({"status": "error"}), 400
    return jsonify({"status": "success" if _remove_user_by_id(tg_id) else "error"})


def _admin_ok():
    data = _get_json()
    return data.get("key") == ADMIN_KEY


@app.route('/api/admin/users', methods=['POST', 'OPTIONS'])
def api_admin_users():
    """Отдаёт содержимое базы (для админ-бота)"""
    if request.method == 'OPTIONS': return '', 200
    if not _admin_ok():
        return jsonify({"status": "error", "message": "403"}), 403
    init_db()
    with open(DB_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    return jsonify({"status": "success", "content": content})


@app.route('/api/admin/auth', methods=['POST', 'OPTIONS'])
def api_admin_auth():
    """Проверка логин+пароль и выдача ранга (для входа в админ-панель)"""
    if request.method == 'OPTIONS': return '', 200
    if not _admin_ok():
        return jsonify({"status": "error", "message": "403"}), 403
    data = _get_json()
    login, password = data.get('username', '').strip(), data.get('password', '').strip()
    init_db()
    with open(DB_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for line in reversed(lines):
        if f"Логин: {login} | Пароль: {password} |" in line:
            rank = line.split(" | Ранг: ")[1].split(" |")[0].strip() if " | Ранг: " in line else "PLAYER"
            return jsonify({"status": "success", "rank": rank})
    return jsonify({"status": "error", "message": "Неверные данные"})


@app.route('/api/admin/update_field', methods=['POST', 'OPTIONS'])
def api_admin_update_field():
    """Изменение поля пользователя (Ранг/Баланс/Удача/Бан_до/Бан_причина)"""
    if request.method == 'OPTIONS': return '', 200
    if not _admin_ok():
        return jsonify({"status": "error", "message": "403"}), 403
    import re as _re
    data = _get_json()
    target_id, field, value = data.get('target', '').strip(), data.get('field', '').strip(), data.get('value', '').strip()
    if not target_id or not field:
        return jsonify({"status": "error"}), 400

    init_db()
    with open(DB_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    found = False
    new_lines = []
    for line in lines:
        if f"ID: {target_id} |" in line:
            found = True
            line = line.strip()
            pattern = rf"\|\s*{_re.escape(field)}:\s*[^|]+"
            if _re.search(pattern, line):
                line = _re.sub(pattern, f"| {field}: {value} ", line).strip()
            else:
                line = f"{line} | {field}: {value}"
            line += "\n"
        new_lines.append(line)
    if found:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Пользователь не найден"}), 404


# --- ОТДАЧА СТРАНИЦЫ И СТАТИКИ (всё на одном порту 5005) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_FILES = {"index.html", "style (4).css", "app.js"}

@app.route('/')
def serve_index():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    if filename in STATIC_FILES:
        return send_from_directory(BASE_DIR, filename)
    return 'Not Found', 404

if __name__ == '__main__':
    app.run(host=os.environ.get('HOST', '0.0.0.0'), port=int(os.environ.get('PORT', '5005')))