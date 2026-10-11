import sqlite3

DB_NAME = 'reminders.db'

def init_db():
    """Создает таблицу для напоминаний, если её нет"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            text TEXT,
            remind_at TEXT,
            status TEXT DEFAULT 'pending'
        )
    ''')
    conn.commit()
    conn.close()

def add_reminder(user_id, text, remind_at):
    """Добавляет новое напоминание в базу"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO reminders (user_id, text, remind_at, status) VALUES (?, ?, ?, ?)',
        (user_id, text, remind_at, 'pending')
    )
    conn.commit()
    conn.close()

def get_reminders(user_id):
    """Получает все активные напоминания пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, text, remind_at FROM reminders WHERE user_id = ? AND status = ?',
        (user_id, 'pending')
    )
    reminders = cursor.fetchall()
    conn.close()
    return reminders

def delete_reminder(reminder_id, user_id):
    """Удаляет напоминание (меняет статус на done)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE reminders SET status = ? WHERE id = ? AND user_id = ?',
        ('done', reminder_id, user_id)
    )
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0

def get_due_reminders(now_str):
    """Возвращает напоминания, чьё время пришло (pending и время <= сейчас)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, user_id, text FROM reminders WHERE status = ? AND remind_at <= ?',
        ('pending', now_str)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows

def mark_sent(reminder_id):
    """Помечает напоминание как отправленное"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE reminders SET status = ? WHERE id = ?',
        ('sent', reminder_id)
    )
    conn.commit()
    conn.close()

init_db()