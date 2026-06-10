import asyncio
from datetime import date, datetime, timedelta
import calendar
import requests
from typing import Optional

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode

from config import BOT_TOKEN, API_URL

# ============================================
# Состояния для ConversationHandler (добавление задачи)
# ============================================
CHOOSE_DATE, CHOOSE_TIME, ENTER_TITLE, ENTER_DESCRIPTION = range(4)

# Временные данные пользователя
user_data = {}

# ============================================
# Клавиатура главного меню (постоянная)
# ============================================
main_keyboard = ReplyKeyboardMarkup(
    [
        ["📅 Сегодня", "📆 Завтра"],
        ["📋 Неделя", "➕ Добавить задачу"],
        ["❓ Помощь"],
    ],
    resize_keyboard=True,
    persistent=True,
)

# ============================================
# API Helpers (без изменений)
# ============================================
def api_get_tasks(due_date=None, start_date=None, end_date=None):
    params = {}
    if due_date:
        params["due_date"] = due_date
    if start_date and end_date:
        params["start_date"] = start_date
        params["end_date"] = end_date
    try:
        r = requests.get(f"{API_URL}/tasks", params=params, timeout=5)
        if r.status_code == 200:
            return r.json()
        return []
    except:
        return []


def api_create_task(title, due_date=None, due_time=None, priority="normal", description=None):
    data = {
        "title": title,
        "due_date": due_date,
        "due_time": due_time,
        "priority": priority,
        "description": description,
    }
    try:
        r = requests.post(f"{API_URL}/tasks", json=data, timeout=5)
        return r.status_code == 201
    except:
        return False


def api_toggle_task(task_id):
    try:
        r = requests.get(f"{API_URL}/tasks/{task_id}", timeout=5)
        if r.status_code != 200:
            return False
        task = r.json()
        r = requests.put(
            f"{API_URL}/tasks/{task_id}",
            json={"completed": not task["completed"]},
            timeout=5,
        )
        return r.status_code == 200
    except:
        return False


def api_delete_task(task_id):
    try:
        r = requests.delete(f"{API_URL}/tasks/{task_id}", timeout=5)
        return r.status_code == 204
    except:
        return False


# ============================================
# Форматирование (без изменений)
# ============================================
PRIORITY_ICONS = {"low": "🟡", "normal": "🔵", "high": "🟣", "urgent": "🔴"}
PRIORITY_NAMES = {"low": "Низкий", "normal": "Обычный", "high": "Высокий", "urgent": "Супер важно!"}


def format_task(task):
    icon = PRIORITY_ICONS.get(task.get("priority", "normal"), "")
    name = PRIORITY_NAMES.get(task.get("priority", "normal"), "")
    text = f"{icon} <b>{task['title']}</b>\n"
    if task.get("description"):
        text += f"📝 {task['description']}\n"
    if task.get("due_time"):
        text += f"🕐 {task['due_time']}\n"
    text += f"⭐ {name}\n"
    status = "✅ Выполнено" if task.get("completed") else "⏳ В работе"
    text += f"Статус: {status}"
    return text


def format_date(date_obj):
    if isinstance(date_obj, str):
        date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()
    return date_obj.strftime("%d.%m.%Y")


# ============================================
# Генерация календаря (inline-кнопки)
# ============================================
def build_calendar(year: int, month: int) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру с днями месяца."""
    # Заголовок с месяцем и годом
    month_name = calendar.month_name[month]
    header = [
        InlineKeyboardButton(
            f"← {month_name} {year} →", callback_data="ignore"
        )
    ]
    # Дни недели
    days_of_week = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    week_row = [InlineKeyboardButton(day, callback_data="ignore") for day in days_of_week]

    # Дни месяца
    cal = calendar.monthcalendar(year, month)
    day_rows = []
    for week in cal:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(" ", callback_data="ignore"))
            else:
                day_str = str(day)
                callback = f"day_{year}_{month}_{day:02d}"
                row.append(InlineKeyboardButton(day_str, callback_data=callback))
        day_rows.append(row)

    # Кнопки навигации
    nav_row = [
        InlineKeyboardButton("⬅️", callback_data=f"prev_month_{year}_{month}"),
        InlineKeyboardButton("➡️", callback_data=f"next_month_{year}_{month}"),
    ]

    keyboard = [header, week_row] + day_rows + [nav_row]
    return InlineKeyboardMarkup(keyboard)


# ============================================
# Обработчики команд
# ============================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветствие и показ главного меню."""
    await update.message.reply_text(
        "📅 <b>Календарь дел</b>\n\n"
        "Используйте кнопки ниже или команды:\n"
        "/today — задачи на сегодня\n"
        "/tomorrow — задачи на завтра\n"
        "/week — задачи на неделю\n"
        "/add — добавить задачу",
        parse_mode=ParseMode.HTML,
        reply_markup=main_keyboard,
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 <b>Справка</b>\n\n"
        "<b>Просмотр:</b> Сегодня, Завтра, Неделя\n"
        "<b>Добавление:</b> кнопка «Добавить задачу»\n"
        "Пошагово: дата → время → название → описание\n\n"
        "Также работают старые команды: /add, /today...",
        parse_mode=ParseMode.HTML,
    )


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today_str = date.today().isoformat()
    tasks = api_get_tasks(due_date=today_str)
    if not tasks:
        await update.message.reply_text("📭 На сегодня задач нет")
        return
    text = f"📅 <b>Сегодня ({format_date(today_str)})</b>\n\n"
    for i, task in enumerate(tasks, 1):
        text += f"{i}. {format_task(task)}\n\n"
    keyboard = build_task_keyboard(tasks)
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)


async def tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tomorrow_str = (date.today() + timedelta(days=1)).isoformat()
    tasks = api_get_tasks(due_date=tomorrow_str)
    if not tasks:
        await update.message.reply_text("📭 На завтра задач нет")
        return
    text = f"📅 <b>Завтра ({format_date(tomorrow_str)})</b>\n\n"
    for i, task in enumerate(tasks, 1):
        text += f"{i}. {format_task(task)}\n\n"
    keyboard = build_task_keyboard(tasks)
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)


async def week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today_date = date.today()
    start = today_date.isoformat()
    end = (today_date + timedelta(days=7)).isoformat()
    tasks = api_get_tasks(start_date=start, end_date=end)
    if not tasks:
        await update.message.reply_text("📭 На этой неделе задач нет")
        return
    grouped = {}
    for task in tasks:
        d = task.get("due_date")
        if d:
            grouped.setdefault(d, []).append(task)
    text = "📅 <b>Задачи на неделю</b>\n\n"
    for d in sorted(grouped.keys()):
        day_name = datetime.strptime(d, "%Y-%m-%d").strftime("%A")
        text += f"<b>{format_date(d)} ({day_name})</b>\n"
        for task in grouped[d]:
            icon = "✅" if task["completed"] else "⏳"
            text += f"  {icon} {task['title']}\n"
        text += "\n"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


def build_task_keyboard(tasks):
    keyboard = []
    for task in tasks:
        row = [
            InlineKeyboardButton(
                f"{'✅' if task['completed'] else '⏳'} {task['title'][:30]}",
                callback_data=f"toggle_{task['id']}",
            ),
            InlineKeyboardButton("❌", callback_data=f"delete_{task['id']}"),
        ]
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("toggle_"):
        task_id = int(data.split("_")[1])
        if api_toggle_task(task_id):
            await query.message.reply_text("✅ Статус обновлён!")
        else:
            await query.message.reply_text("❌ Ошибка")
    elif data.startswith("delete_"):
        task_id = int(data.split("_")[1])
        if api_delete_task(task_id):
            await query.message.reply_text("🗑 Задача удалена")
        else:
            await query.message.reply_text("❌ Ошибка удаления")


# ============================================
# Пошаговое добавление задачи (Conversation)
# ============================================
async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало добавления: показываем календарь."""
    today = date.today()
    context.user_data["add_year"] = today.year
    context.user_data["add_month"] = today.month
    markup = build_calendar(today.year, today.month)
    await update.message.reply_text(
        "📅 Выберите дату задачи:", reply_markup=markup
    )
    return CHOOSE_DATE


async def choose_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора даты из календаря."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "ignore":
        return CHOOSE_DATE

    # Навигация по месяцам
    if data.startswith("prev_month"):
        _, year, month = data.split("_")
        year, month = int(year), int(month)
        month -= 1
        if month < 1:
            month = 12
            year -= 1
        context.user_data["add_year"] = year
        context.user_data["add_month"] = month
        markup = build_calendar(year, month)
        await query.edit_message_text("📅 Выберите дату задачи:", reply_markup=markup)
        return CHOOSE_DATE

    if data.startswith("next_month"):
        _, year, month = data.split("_")
        year, month = int(year), int(month)
        month += 1
        if month > 12:
            month = 1
            year += 1
        context.user_data["add_year"] = year
        context.user_data["add_month"] = month
        markup = build_calendar(year, month)
        await query.edit_message_text("📅 Выберите дату задачи:", reply_markup=markup)
        return CHOOSE_DATE

    # Выбор конкретного дня
    if data.startswith("day_"):
        _, year, month, day = data.split("_")
        selected_date = date(int(year), int(month), int(day))
        # Нельзя выбрать прошедшую дату
        if selected_date < date.today():
            await query.answer("Нельзя выбрать прошедшую дату", show_alert=True)
            return CHOOSE_DATE

        context.user_data["add_date"] = selected_date.isoformat()
        await query.edit_message_text(
            f"📅 Выбрана дата: {format_date(selected_date)}\nТеперь выберите время:"
        )
        # Показываем кнопки времени (15-минутные слоты)
        time_keyboard = build_time_keyboard()
        await query.message.reply_text("🕐 Выберите время:", reply_markup=time_keyboard)
        return CHOOSE_TIME


def build_time_keyboard():
    """Создаёт клавиатуру с временными слотами (группировка по часам)."""
    # Показываем слоты с 7:00 до 22:00, по 4 кнопки в ряд
    buttons = []
    for hour in range(7, 23):
        row = []
        for minute in ["00", "15", "30", "45"]:
            time_str = f"{hour:02d}:{minute}"
            row.append(InlineKeyboardButton(time_str, callback_data=f"time_{time_str}"))
        buttons.append(row)
    # Добавляем опцию "Весь день"
    buttons.append([InlineKeyboardButton("Весь день", callback_data="time_allday")])
    return InlineKeyboardMarkup(buttons)


async def choose_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора времени."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "time_allday":
        context.user_data["add_time"] = None
        await query.edit_message_text("🕐 Выбрано: Весь день")
    elif data.startswith("time_"):
        time_str = data[5:]
        context.user_data["add_time"] = time_str
        await query.edit_message_text(f"🕐 Выбрано время: {time_str}")

    await query.message.reply_text("📝 Введите название задачи:")
    return ENTER_TITLE


async def enter_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получаем название задачи."""
    title = update.message.text.strip()
    if not title:
        await update.message.reply_text("❌ Название не может быть пустым. Введите ещё раз:")
        return ENTER_TITLE
    context.user_data["add_title"] = title
    await update.message.reply_text(
        "📝 Введите описание (или отправьте /skip чтобы пропустить):"
    )
    return ENTER_DESCRIPTION


async def enter_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получаем описание и создаём задачу."""
    description = update.message.text.strip()
    if description == "/skip":
        description = None

    # Создаём задачу через API
    success = api_create_task(
        title=context.user_data["add_title"],
        due_date=context.user_data.get("add_date"),
        due_time=context.user_data.get("add_time"),
        description=description,
    )

    if success:
        date_str = format_date(context.user_data.get("add_date", date.today()))
        time_str = context.user_data.get("add_time") or "весь день"
        text = (
            f"✅ Задача создана!\n"
            f"📝 {context.user_data['add_title']}\n"
            f"📅 {date_str} в {time_str}"
        )
        if description:
            text += f"\n📄 {description}"
        await update.message.reply_text(text, reply_markup=main_keyboard)
    else:
        await update.message.reply_text("❌ Не удалось создать задачу", reply_markup=main_keyboard)

    # Очищаем временные данные
    for key in ("add_date", "add_time", "add_title", "add_year", "add_month"):
        context.user_data.pop(key, None)

    return ConversationHandler.END


async def cancel_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена добавления."""
    await update.message.reply_text("❌ Добавление отменено", reply_markup=main_keyboard)
    for key in ("add_date", "add_time", "add_title", "add_year", "add_month"):
        context.user_data.pop(key, None)
    return ConversationHandler.END


# ============================================
# Обработчик текстовых кнопок главного меню
# ============================================
async def handle_menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия на кнопки ReplyKeyboard."""
    text = update.message.text
    if text == "📅 Сегодня":
        await today(update, context)
    elif text == "📆 Завтра":
        await tomorrow(update, context)
    elif text == "📋 Неделя":
        await week(update, context)
    elif text == "➕ Добавить задачу":
        await add_start(update, context)
    elif text == "❓ Помощь":
        await help_cmd(update, context)
    else:
        # Неизвестная команда – игнорируем или подсказываем
        await update.message.reply_text("Используйте кнопки меню или команды.")


# ============================================
# Запуск бота
# ============================================
def main():
    print("🤖 Запуск Telegram бота...")
    app = Application.builder().token(BOT_TOKEN).build()

    # ConversationHandler для добавления задачи
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("add", add_start),
            MessageHandler(filters.Regex("^➕ Добавить задачу$"), add_start),
        ],
        states={
            CHOOSE_DATE: [CallbackQueryHandler(choose_date)],
            CHOOSE_TIME: [CallbackQueryHandler(choose_time)],
            ENTER_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_title)],
            ENTER_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_description)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_add)],
    )

    # Старые команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("tomorrow", tomorrow))
    app.add_handler(CommandHandler("week", week))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler))

    # Обработчик кнопок главного меню
    app.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND
            & filters.Regex(
                "^(📅 Сегодня|📆 Завтра|📋 Неделя|➕ Добавить задачу|❓ Помощь)$"
            ),
            handle_menu_buttons,
        )
    )

    print("✅ Бот запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

# import asyncio
# from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
# from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
# from telegram.constants import ParseMode
# import requests
# from datetime import date, datetime, timedelta
# from config import BOT_TOKEN, API_URL
#
#
# # ============================================
# # API Helpers
# # ============================================
# def api_get_tasks(due_date=None, start_date=None, end_date=None):
#     """Получить список задач."""
#     params = {}
#     if due_date:
#         params['due_date'] = due_date
#     if start_date and end_date:
#         params['start_date'] = start_date
#         params['end_date'] = end_date
#
#     try:
#         r = requests.get(f"{API_URL}/tasks", params=params, timeout=5)
#         if r.status_code == 200:
#             return r.json()
#         return []
#     except:
#         return []
#
#
# def api_create_task(title, due_date=None, due_time=None, priority="normal"):
#     """Создать задачу."""
#     data = {
#         "title": title,
#         "due_date": due_date,
#         "due_time": due_time,
#         "priority": priority
#     }
#     try:
#         r = requests.post(f"{API_URL}/tasks", json=data, timeout=5)
#         return r.status_code == 201
#     except:
#         return False
#
#
# def api_toggle_task(task_id):
#     """Отметить задачу как выполненную."""
#     try:
#         # Сначала получаем задачу
#         r = requests.get(f"{API_URL}/tasks/{task_id}", timeout=5)
#         if r.status_code != 200:
#             return False
#         task = r.json()
#         # Инвертируем статус
#         r = requests.put(f"{API_URL}/tasks/{task_id}",
#                          json={"completed": not task['completed']}, timeout=5)
#         return r.status_code == 200
#     except:
#         return False
#
#
# def api_delete_task(task_id):
#     """Удалить задачу."""
#     try:
#         r = requests.delete(f"{API_URL}/tasks/{task_id}", timeout=5)
#         return r.status_code == 204
#     except:
#         return False
#
#
# # ============================================
# # Форматирование
# # ============================================
# PRIORITY_ICONS = {
#     'low': '🟡',
#     'normal': '🔵',
#     'high': '🟣',
#     'urgent': '🔴'
# }
#
# PRIORITY_NAMES = {
#     'low': 'Низкий',
#     'normal': 'Обычный',
#     'high': 'Высокий',
#     'urgent': 'Супер важно!'
# }
#
#
# def format_task(task):
#     """Форматирование задачи для сообщения."""
#     icon = PRIORITY_ICONS.get(task.get('priority', 'normal'), '')
#     name = PRIORITY_NAMES.get(task.get('priority', 'normal'), '')
#
#     text = f"{icon} <b>{task['title']}</b>\n"
#     if task.get('description'):
#         text += f"📝 {task['description']}\n"
#     if task.get('due_time'):
#         text += f"🕐 {task['due_time']}\n"
#     text += f"⭐ {name}\n"
#     status = "✅ Выполнено" if task.get('completed') else "⏳ В работе"
#     text += f"Статус: {status}"
#
#     return text
#
#
# def format_date(date_obj):
#     """Формат даты ДД.ММ.ГГГГ."""
#     if isinstance(date_obj, str):
#         date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
#     return date_obj.strftime('%d.%m.%Y')
#
#
# # ============================================
# # Команды бота
# # ============================================
# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Команда /start"""
#     text = (
#         "📅 <b>Календарь дел</b>\n\n"
#         "Команды:\n"
#         "/today — задачи на сегодня\n"
#         "/tomorrow — задачи на завтра\n"
#         "/week — задачи на неделю\n"
#         "/add — добавить задачу\n"
#         "/help — помощь"
#     )
#     await update.message.reply_text(text, parse_mode=ParseMode.HTML)
#
#
# async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Команда /help"""
#     text = (
#         "📋 <b>Справка</b>\n\n"
#         "<b>Просмотр задач:</b>\n"
#         "/today — сегодня\n"
#         "/tomorrow — завтра\n"
#         "/week — на неделю\n\n"
#         "<b>Добавление:</b>\n"
#         "/add Название — добавить задачу\n"
#         "/add завтра Купить хлеб — задача на завтра\n"
#         "/add 31.12 Купить подарки — задача на дату\n\n"
#         "<b>Управление:</b>\n"
#         "Нажмите ✅ или ❌ под задачей"
#     )
#     await update.message.reply_text(text, parse_mode=ParseMode.HTML)
#
#
# async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Задачи на сегодня."""
#     today = date.today().isoformat()
#     tasks = api_get_tasks(due_date=today)
#
#     if not tasks:
#         await update.message.reply_text("📭 На сегодня задач нет")
#         return
#
#     text = f"📅 <b>Задачи на сегодня ({format_date(today)})</b>\n\n"
#     for i, task in enumerate(tasks, 1):
#         text += f"{i}. {format_task(task)}\n\n"
#
#     keyboard = build_task_keyboard(tasks)
#     await update.message.reply_text(
#         text,
#         parse_mode=ParseMode.HTML,
#         reply_markup=keyboard
#     )
#
#
# async def tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Задачи на завтра."""
#     tomorrow = (date.today() + timedelta(days=1)).isoformat()
#     tasks = api_get_tasks(due_date=tomorrow)
#
#     if not tasks:
#         await update.message.reply_text("📭 На завтра задач нет")
#         return
#
#     text = f"📅 <b>Задачи на завтра ({format_date(tomorrow)})</b>\n\n"
#     for i, task in enumerate(tasks, 1):
#         text += f"{i}. {format_task(task)}\n\n"
#
#     keyboard = build_task_keyboard(tasks)
#     await update.message.reply_text(
#         text,
#         parse_mode=ParseMode.HTML,
#         reply_markup=keyboard
#     )
#
#
# async def week(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Задачи на неделю."""
#     today = date.today()
#     start = today.isoformat()
#     end = (today + timedelta(days=7)).isoformat()
#
#     tasks = api_get_tasks(start_date=start, end_date=end)
#
#     if not tasks:
#         await update.message.reply_text("📭 На этой неделе задач нет")
#         return
#
#     # Группируем по датам
#     grouped = {}
#     for task in tasks:
#         d = task.get('due_date')
#         if d:
#             if d not in grouped:
#                 grouped[d] = []
#             grouped[d].append(task)
#
#     text = "📅 <b>Задачи на неделю</b>\n\n"
#     for d in sorted(grouped.keys()):
#         day_name = datetime.strptime(d, '%Y-%m-%d').strftime('%A')
#         text += f"<b>{format_date(d)} ({day_name})</b>\n"
#         for task in grouped[d]:
#             icon = "✅" if task['completed'] else "⏳"
#             text += f"  {icon} {task['title']}\n"
#         text += "\n"
#
#     await update.message.reply_text(text, parse_mode=ParseMode.HTML)
#
#
# async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Добавить задачу. /add [дата] Название"""
#     args = context.args
#
#     if not args:
#         await update.message.reply_text(
#             "❌ Укажите название задачи\n"
#             "Пример: /add Купить хлеб\n"
#             "С датой: /add завтра Купить хлеб"
#         )
#         return
#
#     task_date = date.today().isoformat()
#     title_start = 0
#
#     # Проверяем особые слова
#     if args[0].lower() == 'завтра':
#         task_date = (date.today() + timedelta(days=1)).isoformat()
#         title_start = 1
#     elif args[0].lower() == 'сегодня':
#         title_start = 1
#     elif len(args[0].split('.')) == 3:
#         # Пробуем распарсить дату ДД.ММ.ГГГГ
#         try:
#             parts = args[0].split('.')
#             d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
#             task_date = date(y, m, d).isoformat()
#             title_start = 1
#         except:
#             pass
#
#     title = ' '.join(args[title_start:])
#
#     if not title:
#         await update.message.reply_text("❌ Укажите название задачи")
#         return
#
#     if api_create_task(title, due_date=task_date):
#         await update.message.reply_text(
#             f"✅ Задача создана!\n📝 {title}\n📅 {format_date(task_date)}"
#         )
#     else:
#         await update.message.reply_text("❌ Ошибка создания задачи")
#
#
# def build_task_keyboard(tasks):
#     """Создаёт клавиатуру с кнопками для задач."""
#     keyboard = []
#     for task in tasks:
#         row = [
#             InlineKeyboardButton(
#                 f"{'✅' if task['completed'] else '⏳'} {task['title'][:30]}",
#                 callback_data=f"toggle_{task['id']}"
#             ),
#             InlineKeyboardButton(
#                 "❌",
#                 callback_data=f"delete_{task['id']}"
#             )
#         ]
#         keyboard.append(row)
#     return InlineKeyboardMarkup(keyboard)
#
#
# async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Обработчик нажатий на кнопки."""
#     query = update.callback_query
#     await query.answer()
#
#     data = query.data
#
#     if data.startswith('toggle_'):
#         task_id = int(data.split('_')[1])
#         if api_toggle_task(task_id):
#             await query.message.reply_text("✅ Статус обновлён!")
#         else:
#             await query.message.reply_text("❌ Ошибка")
#
#     elif data.startswith('delete_'):
#         task_id = int(data.split('_')[1])
#         if api_delete_task(task_id):
#             await query.message.reply_text("🗑 Задача удалена")
#         else:
#             await query.message.reply_text("❌ Ошибка удаления")
#
#
# # ============================================
# # Запуск бота
# # ============================================
# def main():
#     """Запуск бота."""
#     print("🤖 Запуск Telegram бота...")
#
#     app = Application.builder().token(BOT_TOKEN).build()
#
#     # Команды
#     app.add_handler(CommandHandler("start", start))
#     app.add_handler(CommandHandler("help", help_cmd))
#     app.add_handler(CommandHandler("today", today))
#     app.add_handler(CommandHandler("tomorrow", tomorrow))
#     app.add_handler(CommandHandler("week", week))
#     app.add_handler(CommandHandler("add", add_task))
#
#     # Кнопки
#     app.add_handler(CallbackQueryHandler(button_handler))
#
#     print("✅ Бот запущен!")
#     app.run_polling(allowed_updates=Update.ALL_TYPES)
#
#
# if __name__ == "__main__":
#     main()