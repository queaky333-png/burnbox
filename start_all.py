import subprocess
import sys
import time

def run_scripts():
    print("🚀 Запускаем все модули BurnBox Vault...\n")
    
    # Список файлов для запуска. 
    # ВНИМАНИЕ: Если твой сервер называется server.py, а не run.py, измени название ниже!
    scripts = [
        ("🌐 Сервер", "run.py"), 
        ("🎮 Основной бот", "bot.py"),
        ("👑 Админ-бот", "admin_bot.py")
    ]

    processes = []

    for name, script in scripts:
        try:
            print(f"⏳ Запуск: {name} ({script})...")
            # Запускаем каждый скрипт как отдельный процесс
            process = subprocess.Popen([sys.executable, script])
            processes.append((name, process))
            time.sleep(1) # Небольшая пауза, чтобы сервер успел встать до ботов
        except Exception as e:
            print(f"❌ Ошибка при запуске {name} ({script}): {e}")

    print("\n✅ Все модули успешно запущены и работают параллельно!")
    print("🛑 Для остановки всех скриптов нажми комбинацию: Ctrl + C\n")

    try:
        # Держим главный скрипт запущенным, пока работают остальные
        for _, process in processes:
            process.wait()
    except KeyboardInterrupt:
        print("\n\n🛑 Получен сигнал остановки. Закрываем все модули...")
        for name, process in processes:
            process.terminate()
            print(f"⏹ {name} успешно остановлен.")
        print("👋 Работа завершена.")

if __name__ == "__main__":
    run_scripts()