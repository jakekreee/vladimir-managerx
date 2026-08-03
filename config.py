import os

# Загружаем переменные из окружения (секреты Amvera)
TOKEN = os.getenv("TOKEN", "")
GROUP_ID = os.getenv("GROUP_ID", "")
BOT_ID = os.getenv("BOT_ID", None)

# Проверяем, что переменные заданы
if not TOKEN:
    raise ValueError("❌ TOKEN не задан! Добавьте его в секреты Amvera (Settings → Environment Variables).")
if not GROUP_ID:
    raise ValueError("❌ GROUP_ID не задан! Добавьте его в секреты Amvera (Settings → Environment Variables).")

# Преобразуем GROUP_ID в число
try:
    GROUP_ID = int(GROUP_ID)
except ValueError:
    raise ValueError("❌ GROUP_ID должен быть числом. Пример: 123456789")

# Преобразуем BOT_ID, если он передан
if BOT_ID:
    try:
        BOT_ID = int(BOT_ID)
    except ValueError:
        pass  # оставляем как есть

print(f"✅ Конфиг загружен. GROUP_ID = {GROUP_ID}")
print(f"✅ TOKEN загружен (первые 10 символов): {TOKEN[:10]}...")
