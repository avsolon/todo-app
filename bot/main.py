import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode
import requests
from datetime import date, datetime, timedelta
from config import BOT_TOKEN, API_URL


# ============================================
# API Helpers
# ============================================
def api_get_tasks(due_date=None, start_date=None, end_date=None):
    """Получить список задач."""
    params = {}
    if due_date:
        params['due_date'] = due_date
    if start_date and end_date:
        params['start_date'] = start_date
        params['end_date'] = end_date

    try:
        r = requests.get(f"{API_URL}/tasks", params=params, timeout=5)
        if r.status_code == 200:
            return r.json()
        return []
    except:
        return []


def api_create_task(title, due_date=None, due_time=None, priority="normal"):
    """Создать задачу."""
    data = {
        "title": title,
        "due_date": due_date,
        "due_time": due_time,
        "priority": priority
    }
    try:
        r = requests.post(f"{API_URL}/tasks", json=data, timeout=5)
        return r.status_code == 201
    except:
        return False


def api_toggle_task(task_id):
    """Отметить задачу как выполненную."""
    try:
        # Сначала получаем задачу
        r = requests.get(f"{API_URL}/tasks/{task_id}", timeout=5)
        if r.status_code != 200:
            return False
        task = r.json()
        # Инвертируем статус
        r = requests.put(f"{API_URL}/tasks/{task_id}",
                         json={"completed": not task['completed']}, timeout=5)
        return r.status_code == 200
    except:
        return False


def api_delete_task(task_id):
    """Удалить задачу."""
    try:
        r = requests.delete(f"{API_URL}/tasks/{task_id}", timeout=5)
        return r.status_code == 204
    except:
        return False


# ============================================
# Форматирование
# ============================================
PRIORITY_ICONS = {
    'low': '🟡',
    'normal': '🔵',
    'high': '🟣',
    'urgent': '🔴'
}

PRIORITY_NAMES = {
    'low': 'Низкий',
    'normal': 'Обычный',
    'high': 'Высокий',
    'urgent': 'Супер важно!'
}


def format_task(task):
    """Форматирование задачи для сообщения."""
    icon = PRIORITY_ICONS.get(task.get('priority', 'normal'), '')
    name = PRIORITY_NAMES.get(task.get('priority', 'normal'), '')

    text = f"{icon} <b>{task['title']}</b>\n"
    if task.get('description'):
        text += f"📝 {task['description']}\n"
    if task.get('due_time'):
        text += f"🕐 {task['due_time']}\n"
    text += f"⭐ {name}\n"
    status = "✅ Выполнено" if task.get('completed') else "⏳ В работе"
    text += f"Статус: {status}"

    return text


def format_date(date_obj):
    """Формат даты ДД.ММ.ГГГГ."""
    if isinstance(date_obj, str):
        date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
    return date_obj.strftime('%d.%m.%Y')


# ============================================
# Команды бота
# ============================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    text = (
        "📅 <b>Календарь дел</b>\n\n"
        "Команды:\n"
        "/today — задачи на сегодня\n"
        "/tomorrow — задачи на завтра\n"
        "/week — задачи на неделю\n"
        "/add — добавить задачу\n"
        "/help — помощь"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    text = (
        "📋 <b>Справка</b>\n\n"
        "<b>Просмотр задач:</b>\n"
        "/today — сегодня\n"
        "/tomorrow — завтра\n"
        "/week — на неделю\n\n"
        "<b>Добавление:</b>\n"
        "/add Название — добавить задачу\n"
        "/add завтра Купить хлеб — задача на завтра\n"
        "/add 31.12 Купить подарки — задача на дату\n\n"
        "<b>Управление:</b>\n"
        "Нажмите ✅ или ❌ под задачей"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задачи на сегодня."""
    today = date.today().isoformat()
    tasks = api_get_tasks(due_date=today)

    if not tasks:
        await update.message.reply_text("📭 На сегодня задач нет")
        return

    text = f"📅 <b>Задачи на сегодня ({format_date(today)})</b>\n\n"
    for i, task in enumerate(tasks, 1):
        text += f"{i}. {format_task(task)}\n\n"

    keyboard = build_task_keyboard(tasks)
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )


async def tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задачи на завтра."""
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    tasks = api_get_tasks(due_date=tomorrow)

    if not tasks:
        await update.message.reply_text("📭 На завтра задач нет")
        return

    text = f"📅 <b>Задачи на завтра ({format_date(tomorrow)})</b>\n\n"
    for i, task in enumerate(tasks, 1):
        text += f"{i}. {format_task(task)}\n\n"

    keyboard = build_task_keyboard(tasks)
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )


async def week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задачи на неделю."""
    today = date.today()
    start = today.isoformat()
    end = (today + timedelta(days=7)).isoformat()

    tasks = api_get_tasks(start_date=start, end_date=end)

    if not tasks:
        await update.message.reply_text("📭 На этой неделе задач нет")
        return

    # Группируем по датам
    grouped = {}
    for task in tasks:
        d = task.get('due_date')
        if d:
            if d not in grouped:
                grouped[d] = []
            grouped[d].append(task)

    text = "📅 <b>Задачи на неделю</b>\n\n"
    for d in sorted(grouped.keys()):
        day_name = datetime.strptime(d, '%Y-%m-%d').strftime('%A')
        text += f"<b>{format_date(d)} ({day_name})</b>\n"
        for task in grouped[d]:
            icon = "✅" if task['completed'] else "⏳"
            text += f"  {icon} {task['title']}\n"
        text += "\n"

    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавить задачу. /add [дата] Название"""
    args = context.args

    if not args:
        await update.message.reply_text(
            "❌ Укажите название задачи\n"
            "Пример: /add Купить хлеб\n"
            "С датой: /add завтра Купить хлеб"
        )
        return

    task_date = date.today().isoformat()
    title_start = 0

    # Проверяем особые слова
    if args[0].lower() == 'завтра':
        task_date = (date.today() + timedelta(days=1)).isoformat()
        title_start = 1
    elif args[0].lower() == 'сегодня':
        title_start = 1
    elif len(args[0].split('.')) == 3:
        # Пробуем распарсить дату ДД.ММ.ГГГГ
        try:
            parts = args[0].split('.')
            d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
            task_date = date(y, m, d).isoformat()
            title_start = 1
        except:
            pass

    title = ' '.join(args[title_start:])

    if not title:
        await update.message.reply_text("❌ Укажите название задачи")
        return

    if api_create_task(title, due_date=task_date):
        await update.message.reply_text(
            f"✅ Задача создана!\n📝 {title}\n📅 {format_date(task_date)}"
        )
    else:
        await update.message.reply_text("❌ Ошибка создания задачи")


def build_task_keyboard(tasks):
    """Создаёт клавиатуру с кнопками для задач."""
    keyboard = []
    for task in tasks:
        row = [
            InlineKeyboardButton(
                f"{'✅' if task['completed'] else '⏳'} {task['title'][:30]}",
                callback_data=f"toggle_{task['id']}"
            ),
            InlineKeyboardButton(
                "❌",
                callback_data=f"delete_{task['id']}"
            )
        ]
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки."""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith('toggle_'):
        task_id = int(data.split('_')[1])
        if api_toggle_task(task_id):
            await query.message.reply_text("✅ Статус обновлён!")
        else:
            await query.message.reply_text("❌ Ошибка")

    elif data.startswith('delete_'):
        task_id = int(data.split('_')[1])
        if api_delete_task(task_id):
            await query.message.reply_text("🗑 Задача удалена")
        else:
            await query.message.reply_text("❌ Ошибка удаления")


# ============================================
# Запуск бота
# ============================================
def main():
    """Запуск бота."""
    print("🤖 Запуск Telegram бота...")

    app = Application.builder().token(BOT_TOKEN).build()

    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("tomorrow", tomorrow))
    app.add_handler(CommandHandler("week", week))
    app.add_handler(CommandHandler("add", add_task))

    # Кнопки
    app.add_handler(CallbackQueryHandler(button_handler))

    print("✅ Бот запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()