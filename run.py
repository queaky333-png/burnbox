import subprocess
import sys
import socket

def port_in_use(port=5005):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("127.0.0.1", port)) == 0
    except Exception:
        return False

if port_in_use():
    print("⚠️ BurnBox уже запущен (порт 5005 занят).\n")
    print("Запускается только один экземпляр сервера и ботов.")
    print("Если что-то не работает — сначала закрой все процессы python, потом запусти снова.")
    sys.exit(0)

print("🚀 Запускаем все системы BurnBox...\n")

# Запускаем все три файла одновременно
processes = [
    subprocess.Popen([sys.executable, "server.py"]),
    subprocess.Popen([sys.executable, "bot.py"]),
    subprocess.Popen([sys.executable, "admin_bot.py"])
]

print("✅ Все скрипты успешно запущены в одном терминале!")
print("🛑 Чтобы остановить всё сразу, просто нажми Ctrl + C здесь.\n")

try:
    # Оставляем скрипт работать и следить за процессами
    for p in processes:
        p.wait()
except KeyboardInterrupt:
    # Если ты нажал Ctrl+C, убиваем все три процесса
    print("\n⚠️ Выключаем системы...")
    for p in processes:
        p.terminate()
    print("🛑 Все боты и сервер полностью остановлены.")