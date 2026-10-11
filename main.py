import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import db
import os
from dotenv import load_dotenv
   
load_dotenv() # Эта команда открывает наш сейф

load_dotenv()

# ВНИМАНИЕ: Вставьте ваш токен между кавычками
TOKEN = os.getenv('VK_TOKEN')

vk_session = vk_api.VkApi(token=TOKEN)
longpoll = VkLongPoll(vk_session)
vk = vk_session.get_api()

def send_message(user_id, message):
    """Удобная функция для отправки сообщений"""
    vk.messages.send(user_id=user_id, message=message, random_id=0)

def check_reminders():
    """Фоновая задача: проверяет базу каждые 30 секунд и шлёт напоминания"""
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    due = db.get_due_reminders(now_str)
    for reminder_id, user_id, text in due:
        send_message(user_id, f"⏰ Напоминание!\n📝 {text}")
        db.mark_sent(reminder_id)
        print(f"✅ Напоминание №{reminder_id} отправлено пользователю {user_id}")

# --- Запускаем планировщик (работает сам по себе, в фоне) ---
scheduler = BackgroundScheduler()
scheduler.add_job(check_reminders, 'interval', seconds=30)
scheduler.start()

print("✅ Бот запущен! Планировщик работает: проверка каждые 30 секунд.")

for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW:
        if event.to_me:
            user_id = event.user_id
            text = event.text.strip()

            print(f"👤 Пользователь {user_id} написал: {text}")

            if text.lower() in ['начать', '/start', 'привет']:
                send_message(user_id,
                    "👋 Привет! Я бот-напоминалка.\n\n"
                    "Мои команды:\n"
                    "➕ /add 2026-12-31 10:00 Поздравить с НГ - добавить\n"
                    "📋 /list - посмотреть список\n"
                    "❌ /delete ID - удалить по номеру")

            elif text.lower().startswith('/add'):
                try:
                    parts = text.split(' ', 3)
                    if len(parts) < 4:
                        send_message(user_id, "❌ Ошибка формата!\nПример: /add 2026-10-15 10:00 Позвонить завучу")
                        continue

                    date_str = parts[1]
                    time_str = parts[2]
                    reminder_text = parts[3]

                    remind_at = f"{date_str} {time_str}"
                    remind_dt = datetime.strptime(remind_at, '%Y-%m-%d %H:%M')

                    # Проверка: время не должно быть в прошлом
                    if remind_dt <= datetime.now():
                        send_message(user_id, "❌ Это время уже в прошлом!\nУкажите будущую дату и время.")
                        continue

                    db.add_reminder(user_id, reminder_text, remind_at)
                    send_message(user_id, f"✅ Напоминание добавлено!\n📅 {remind_at}\n📝 {reminder_text}")

                except ValueError:
                    send_message(user_id, "❌ Неверный формат даты или времени!\nИспользуйте: ГГГГ-ММ-ДД ЧЧ:ММ\nПример: 2026-10-15 14:30")
                except Exception as e:
                    send_message(user_id, f"Произошла ошибка: {e}")

            elif text.lower() == '/list':
                reminders = db.get_reminders(user_id)
                if not reminders:
                    send_message(user_id, "📭 У вас пока нет активных напоминаний.")
                else:
                    response = "📋 Ваши напоминания:\n\n"
                    for r_id, r_text, r_time in reminders:
                        response += f"🔹 ID: {r_id}\n📅 {r_time}\n📝 {r_text}\n\n"
                    response += "Чтобы удалить, напишите: /delete ID"
                    send_message(user_id, response)

            elif text.lower().startswith('/delete'):
                try:
                    r_id = int(text.split()[1])
                    success = db.delete_reminder(r_id, user_id)
                    if success:
                        send_message(user_id, f"🗑 Напоминание №{r_id} успешно удалено!")
                    else:
                        send_message(user_id, "❌ Не найдено напоминание с таким ID или оно вам не принадлежит.")
                except (IndexError, ValueError):
                    send_message(user_id, "❌ Укажите ID напоминания.\nПример: /delete 1")

            else:
                send_message(user_id, "🤔 Я не знаю такой команды.\nНапишите /start, чтобы увидеть список команд.")