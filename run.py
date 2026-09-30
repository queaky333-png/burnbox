import subprocess
import sys
import socket
import os

# Получаем порт из облака (или используем 5005 по умолчанию для телефона/ПК)
PORT = int(os.environ.get('PORT', 5005))

def port_in_use(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("127.0.0.1", port)) == 0
    except Exception:
        return False

if port_in_use(PORT):
    print(f"⚠️ BurnBox уже запущен (порт {PORT} занят).\n")
    print("Запускается только один экземпляр.")
    sys.exit(0)

print(f"🚀 Запускаем все системы BurnBox на порту {PORT}...\n")

# Передаем переменные окружения, чтобы боты знали, на каком порту работает сервер
env = os.environ.copy()
env['PORT'] = str(PORT)

# Запускаем все три файла одновременно
processes = [
    subprocess.Popen([sys.executable, "server.py"], env=env),
    subprocess.Popen([sys.executable, "bot.py"], env=env),
    subprocess.Popen([sys.executable, "admin_bot.py"], env=env)
]

print("✅ Все скрипты успешно запущены!")
print("🛑 Чтобы остановить всё сразу, нажми Ctrl + C.\n")

try:
    for p in processes:
        p.wait()
except KeyboardInterrupt:
    print("\n⚠️ Выключаем системы...")
    for p in processes:
        p.terminate()
    print("🛑 Все боты и сервер полностью остановлены.")