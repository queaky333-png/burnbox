BurnBox Vault — развертывание бэкенда на PythonAnywhere (бесплатно, 24/7)
=========================================================================

Что загружается сюда:
  server.py        — Flask-бэкенд (API + база users.txt)
  wsgi.py          — точка входа для PythonAnywhere
  users.txt        — база пользователей (переносится как есть)
  requirements.txt — зависимости

ШАГ 1. Создать аккаунт
  https://www.pythonanywhere.com/pricing -> "Explore with a limited free account"
  Подтвердить email. Никакой карты не нужно.

ШАГ 2. Добавить Web-приложение (один раз)
  Зайдите на сайт PythonAnywhere -> вкладка "Web" -> "Add a new web app"
  - Next -> Next (оставить "Manual configuration")
  - Выбрать Python 3.10 (или любую 3.x) -> Next
  Должна появиться запись вида USERNAME.pythonanywhere.com.

ШАГ 3. Загрузить файлы
  Вкладка "Files" -> открыть папку /home/USERNAME -> создать папку burnbox
  Открыть burnbox и загрузить туда: server.py, wsgi.py, users.txt, requirements.txt
  (кнопка "Upload a file" вверху страницы).

ШАГ 4. Установить зависимости
  Вкладка "Consoles" -> "Bash" -> выполнить:
      pip3.10 install --user flask flask_cors requests
  (если нужна другая версия — pip3.11 и т.п.)

ШАГ 5. Указать WSGI-файл
  Вкладка "Web" -> блок вашего приложения:
  - Source code:       /home/USERNAME/burnbox
  - Working directory: /home/USERNAME/burnbox
  - WSGI configuration file: нажать ссылку чтобы открыть файл, очистить его
    и вставить одну строку:
        from wsgi import application
  Сохранить (Save).

ШАГ 6. Перезапустить
  Вкладка "Web" -> кнопка Reload (напротив вашего приложения).

ШАГ 7. Проверить
  Открыть в браузере:  https://USERNAME.pythonanywhere.com/
  Должен вернуться index.html либо 404 на / — но API работает.
  Проверить API:  https://USERNAME.pythonanywhere.com/api/... (и т.п.)
  Например открыть /login без параметров — вернётся JSON error, значит сервер жив.

ПОСЛЕ ДЕПЛОЯ укажи реальный USERNAME здесь:
  - C:\Users\lev20\Desktop\BurnBoxProject\app.js     (константа API_BASE)
  - C:\Users\lev20\Desktop\BurnBoxProject\bot.py     (константа API_BASE)
  - C:\Users\lev20\Desktop\BurnBoxProject\admin_bot.py (константа API_BASE)
  Чтобы заменить: USERNAME -> твой логин.
  И перезалей обновлённый app.js на Netlify.