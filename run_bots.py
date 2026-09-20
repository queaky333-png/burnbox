import subprocess
import sys

print("🤖 Запускаем ботов BurnBox (сервер теперь живёт в облаке)...\n")

processes = [
    subprocess.Popen([sys.executable, "bot.py"]),
    subprocess.Popen([sys.executable, "admin_bot.py"])
]

print("✅ Боты запущены!")
print("🛑 Остановка: нажми Ctrl + C здесь.\n")

try:
    for p in processes:
        p.wait()
except KeyboardInterrupt:
    print("\n⚠️ Останавливаем ботов...")
    for p in processes:
        p.terminate()
    print("🛑 Боты остановлены.")