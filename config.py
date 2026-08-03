import os

# Загружаем переменные из окружения (секреты Amvera или .env)
TOKEN = os.getenv("TOKEN", "")
GROUP_ID = os.getenv("GROUP_ID", "")
BOT_ID = os.getenv("BOT_ID", None)  # можно оставить None, если не знаете

# Проверяем, что основные переменные заданы
if not TOKEN:
    raise ValueError("❌ TOKEN не найден! Добавьте его в секреты Amvera.")
if not GROUP_ID:
    raise ValueError("❌ GROUP_ID не найден! Добавьте его в секреты Amvera.")

# Преобразуем GROUP_ID в число (если нужно)
try:
    GROUP_ID = int(GROUP_ID)
except ValueError:
    raise ValueError("❌ GROUP_ID должно быть числом.")

# Если BOT_ID передан строкой, тоже преобразуем
if BOT_ID:
    try:
        BOT_ID = int(BOT_ID)
    except ValueError:
        pass  # оставляем как есть, если не число

print(f"✅ Конфиг загружен. GROUP_ID = {GROUP_ID}")
