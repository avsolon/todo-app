// ============================================
// Todo Calendar - JavaScript приложение
// ============================================

// API base URL — убедитесь что порт совпадает
const API_BASE = 'http://127.0.0.1:8000';

// ============================================
// Глобальное состояние
// ============================================
const state = {
    currentDate: new Date(),
    currentView: 'week',
    selectedDate: new Date(),
    miniCalendarDate: new Date(),
    tasks: {},
    editingTaskId: null
};

// ============================================
// Утилиты
// ============================================
function formatDate(date) {
    return date.toISOString().split('T')[0];
}

function getMonday(date) {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? -6 : 1);
    return new Date(d.setDate(diff));
}

function getWeekDates(date) {
    const monday = getMonday(date);
    const dates = [];
    for (let i = 0; i < 7; i++) {
        const d = new Date(monday);
        d.setDate(d.getDate() + i);
        dates.push(d);
    }
    return dates;
}

function isToday(date) {
    const today = new Date();
    return date.getDate() === today.getDate() &&
        date.getMonth() === today.getMonth() &&
        date.getFullYear() === today.getFullYear();
}

function isSameDate(d1, d2) {
    return d1.getDate() === d2.getDate() &&
        d1.getMonth() === d2.getMonth() &&
        d1.getFullYear() === d2.getFullYear();
}

// ============================================
// API вызовы
// ============================================
async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        if (!response.ok) {
            const error = await response.text();
            throw new Error(`HTTP ${response.status}: ${error}`);
        }

        if (response.status === 204) return null;
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

async function fetchTasks(startDate, endDate) {
    const url = `${API_BASE}/api/tasks/calendar?start_date=${formatDate(startDate)}&end_date=${formatDate(endDate)}`;
    try {
        const data = await apiCall(url);
        state.tasks = data || {};
        return data;
    } catch (error) {
        console.error('Ошибка загрузки задач:', error);
        return {};
    }
}

async function createTask(taskData) {
    return await apiCall(`${API_BASE}/api/tasks`, {
        method: 'POST',
        body: JSON.stringify(taskData)
    });
}

async function updateTask(taskId, taskData) {
    return await apiCall(`${API_BASE}/api/tasks/${taskId}`, {
        method: 'PUT',
        body: JSON.stringify(taskData)
    });
}

async function deleteTask(taskId) {
    return await apiCall(`${API_BASE}/api/tasks/${taskId}`, {
        method: 'DELETE'
    });
}

// ============================================
// Мини-календарь в сайдбаре
// ============================================
function renderMiniCalendar() {
    const date = state.miniCalendarDate;
    const year = date.getFullYear();
    const month = date.getMonth();

    document.getElementById('mini-month-year').textContent =
        date.toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' });

    const grid = document.getElementById('mini-calendar-days');

    // Удаляем старые дни
    const oldDays = grid.querySelectorAll('.mini-day');
    oldDays.forEach(d => d.remove());

    // Первый день месяца
    const firstDay = new Date(year, month, 1);
    let startDay = firstDay.getDay();
    startDay = startDay === 0 ? 6 : startDay - 1; // Пн = 0

    // Последний день месяца
    const lastDay = new Date(year, month + 1, 0);

    // Дни из предыдущего месяца
    const prevLastDay = new Date(year, month, 0);
    for (let i = startDay - 1; i >= 0; i--) {
        const day = prevLastDay.getDate() - i;
        const cell = createMiniDay(new Date(year, month - 1, day), true);
        grid.appendChild(cell);
    }

    // Дни текущего месяца
    for (let day = 1; day <= lastDay.getDate(); day++) {
        const cell = createMiniDay(new Date(year, month, day), false);
        grid.appendChild(cell);
    }

    // Дни следующего месяца
    const totalCells = startDay + lastDay.getDate();
    const remainingCells = totalCells % 7 === 0 ? 0 : 7 - (totalCells % 7);
    for (let day = 1; day <= remainingCells; day++) {
        const cell = createMiniDay(new Date(year, month + 1, day), true);
        grid.appendChild(cell);
    }
}

function createMiniDay(date, isOtherMonth) {
    const div = document.createElement('div');
    div.className = 'mini-day';
    div.textContent = date.getDate();

    if (isOtherMonth) div.classList.add('other-month');
    if (isToday(date)) div.classList.add('today');
    if (isSameDate(date, state.selectedDate)) div.classList.add('selected');

    // Проверяем есть ли задачи в этот день
    const dateStr = formatDate(date);
    if (state.tasks[dateStr] && state.tasks[dateStr].length > 0) {
        div.classList.add('has-tasks');
    }

    div.addEventListener('click', () => {
        state.selectedDate = date;
        state.miniCalendarDate = date;
        renderMiniCalendar();
        renderCalendar();
    });

    return div;
}

// ============================================
// Основной календарь
// ============================================
function renderCalendar() {
    updateHeader();

    if (state.currentView === 'day') {
        renderDayView();
    } else {
        renderWeekView();
    }
}

function updateHeader() {
    const dates = getWeekDates(getMonday(state.currentDate));

    if (state.currentView === 'week') {
        const startStr = dates[0].toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' });
        const endStr = dates[6].toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' });
        document.getElementById('current-period').textContent = `${startStr} – ${endStr}`;
    } else {
        document.getElementById('current-period').textContent =
            state.selectedDate.toLocaleDateString('ru-RU', {
                weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
            });
    }
}

function renderWeekView() {
    const dates = getWeekDates(getMonday(state.currentDate));
    const weekHeader = document.getElementById('week-header');
    const daysContainer = document.getElementById('days-container');
    const timeColumn = document.getElementById('time-column');

    // Заголовки дней
    weekHeader.innerHTML = '<div class="time-column-header"></div>';
    daysContainer.innerHTML = '';
    timeColumn.innerHTML = '';

    // Временные метки (7:00 - 22:00)
    for (let hour = 7; hour <= 22; hour++) {
        const timeSlot = document.createElement('div');
        timeSlot.className = 'time-slot';
        timeSlot.textContent = `${hour}:00`;
        timeColumn.appendChild(timeSlot);
    }

    dates.forEach((date, index) => {
        // Заголовок дня
        const dayHeader = document.createElement('div');
        dayHeader.className = `day-header${isToday(date) ? ' today' : ''}`;
        dayHeader.innerHTML = `
            <div class="day-name">${date.toLocaleDateString('ru-RU', { weekday: 'short' })}</div>
            <div class="day-number">${date.getDate()}</div>
        `;
        weekHeader.appendChild(dayHeader);

        // Колонка дня
        const dayColumn = document.createElement('div');
        dayColumn.className = `day-column${isToday(date) ? ' today' : ''}`;
        dayColumn.style.gridColumn = index + 2;
        dayColumn.style.gridRow = 1;

        // Ячейки часов
        for (let hour = 7; hour <= 22; hour++) {
            const hourCell = document.createElement('div');
            hourCell.className = 'hour-cell';
            hourCell.addEventListener('click', () => {
                openTaskModal(null, date, `${hour}:00`);
            });
            dayColumn.appendChild(hourCell);
        }

        // Добавляем задачи для этого дня
        const dateStr = formatDate(date);
        const dayTasks = state.tasks[dateStr] || [];

        dayTasks.forEach(task => {
            const taskEl = createTaskElement(task);
            dayColumn.appendChild(taskEl);
        });

        daysContainer.appendChild(dayColumn);
    });
}

function renderDayView() {
    // Упрощенная версия — только один день
    state.currentDate = new Date(state.selectedDate);
    renderWeekView(); // Пока используем недельный вид
}

function createTaskElement(task) {
    const el = document.createElement('div');
    el.className = `task-event priority-${task.priority}`;
    if (task.completed) el.classList.add('completed');

    el.style.backgroundColor = task.color + '20';
    el.style.borderLeftColor = task.color;

    // Позиционирование по времени
    if (task.due_time) {
        const [hours, minutes] = task.due_time.split(':');
        const topPosition = (parseInt(hours) - 7) * 60 + parseInt(minutes);
        el.style.top = `${topPosition}px`;
        el.style.height = 'auto';
        el.style.minHeight = '24px';
    } else {
        el.style.top = '0px';
        el.style.height = 'auto';
    }

    el.innerHTML = `
        <div class="event-time">${task.due_time || 'Весь день'}</div>
        <div class="event-title">${escapeHtml(task.title)}</div>
    `;

    // Клик для редактирования
    el.addEventListener('click', (e) => {
        e.stopPropagation();
        openTaskModal(task);
    });

    // Drag & drop для перемещения (упрощенно)
    el.draggable = true;
    el.addEventListener('dragstart', (e) => {
        e.dataTransfer.setData('text/plain', task.id);
    });

    return el;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================
// Модальное окно задачи
// ============================================
function openTaskModal(task = null, date = null, time = null) {
    const modal = document.getElementById('task-modal');
    const form = document.getElementById('task-form');

    form.reset();

    if (task) {
        // Редактирование существующей задачи
        document.getElementById('modal-title').textContent = 'Редактировать задачу';
        document.getElementById('task-id').value = task.id;
        document.getElementById('task-title-input').value = task.title;
        document.getElementById('task-desc-input').value = task.description || '';
        document.getElementById('task-date-input').value = task.due_date || '';
        document.getElementById('task-time-input').value = task.due_time || '';
        document.getElementById('task-priority').value = task.priority;
        document.getElementById('task-color').value = task.color;
        document.getElementById('delete-task-btn').style.display = 'block';
        state.editingTaskId = task.id;
    } else {
        // Новая задача
        document.getElementById('modal-title').textContent = 'Новая задача';
        document.getElementById('task-id').value = '';
        document.getElementById('delete-task-btn').style.display = 'none';
        state.editingTaskId = null;

        // Предзаполняем дату и время
        if (date) {
            document.getElementById('task-date-input').value = formatDate(date);
        }
        if (time) {
            document.getElementById('task-time-input').value = time;
        }
    }

    modal.classList.add('active');
    document.getElementById('task-title-input').focus();
}

function closeModal() {
    document.getElementById('task-modal').classList.remove('active');
    state.editingTaskId = null;
}

async function handleFormSubmit(e) {
    e.preventDefault();

    const taskData = {
        title: document.getElementById('task-title-input').value.trim(),
        description: document.getElementById('task-desc-input').value.trim() || null,
        due_date: document.getElementById('task-date-input').value || null,
        due_time: document.getElementById('task-time-input').value || null,
        priority: document.getElementById('task-priority').value,
        color: document.getElementById('task-color').value
    };

    if (!taskData.title) {
        alert('Введите название задачи');
        return;
    }

    try {
        const taskId = document.getElementById('task-id').value;

        if (taskId) {
            await updateTask(taskId, taskData);
        } else {
            await createTask(taskData);
        }

        closeModal();
        await refreshTasks();
    } catch (error) {
        alert('Ошибка сохранения задачи: ' + error.message);
    }
}

async function handleDeleteTask() {
    const taskId = document.getElementById('task-id').value;
    if (!taskId) return;

    if (!confirm('Удалить задачу?')) return;

    try {
        await deleteTask(taskId);
        closeModal();
        await refreshTasks();
    } catch (error) {
        alert('Ошибка удаления задачи: ' + error.message);
    }
}

// ============================================
// Обновление данных
// ============================================
async function refreshTasks() {
    const dates = getWeekDates(getMonday(state.currentDate));
    const startDate = dates[0];
    const endDate = dates[6];

    // Расширяем диапазон для мини-календаря
    const miniStart = new Date(state.miniCalendarDate.getFullYear(), state.miniCalendarDate.getMonth(), 1);
    const miniEnd = new Date(state.miniCalendarDate.getFullYear(), state.miniCalendarDate.getMonth() + 1, 0);

    await fetchTasks(miniStart < startDate ? miniStart : startDate,
                     miniEnd > endDate ? miniEnd : endDate);

    renderMiniCalendar();
    renderCalendar();
}

// ============================================
// Обработчики событий
// ============================================
function initEventListeners() {
    // Кнопка "Сегодня"
    document.getElementById('today-btn').addEventListener('click', () => {
        state.currentDate = new Date();
        state.selectedDate = new Date();
        state.miniCalendarDate = new Date();
        refreshTasks();
    });

    // Навигация
    document.getElementById('prev-week').addEventListener('click', () => {
        const monday = getMonday(state.currentDate);
        monday.setDate(monday.getDate() - 7);
        state.currentDate = monday;
        state.selectedDate = monday;
        state.miniCalendarDate = monday;
        refreshTasks();
    });

    document.getElementById('next-week').addEventListener('click', () => {
        const monday = getMonday(state.currentDate);
        monday.setDate(monday.getDate() + 7);
        state.currentDate = monday;
        state.selectedDate = monday;
        state.miniCalendarDate = monday;
        refreshTasks();
    });

    document.getElementById('prev-month').addEventListener('click', () => {
        state.miniCalendarDate.setMonth(state.miniCalendarDate.getMonth() - 1);
        refreshTasks();
    });

    document.getElementById('next-month').addEventListener('click', () => {
        state.miniCalendarDate.setMonth(state.miniCalendarDate.getMonth() + 1);
        refreshTasks();
    });

    // Переключение вида
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.currentView = btn.dataset.view;
            renderCalendar();
        });
    });

    // Кнопка добавления задачи
    document.getElementById('add-task-btn').addEventListener('click', () => {
        openTaskModal(null, state.selectedDate);
    });

    // Модальное окно
    document.getElementById('close-modal').addEventListener('click', closeModal);
    document.getElementById('task-modal').addEventListener('click', (e) => {
        if (e.target === document.getElementById('task-modal')) {
            closeModal();
        }
    });

    // Форма
    document.getElementById('task-form').addEventListener('submit', handleFormSubmit);
    document.getElementById('delete-task-btn').addEventListener('click', handleDeleteTask);

    // Закрытие по Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeModal();
    });
}

// ============================================
// Инициализация
// ============================================
async function init() {
    console.log('🚀 Инициализация Todo Calendar...');
    console.log('API URL:', API_BASE);

    initEventListeners();

    // Проверяем соединение с API
    try {
        const health = await apiCall(`${API_BASE}/health`);
        console.log('✅ API доступен:', health);
    } catch (error) {
        console.error('❌ API недоступен:', error);
        alert('Не удалось подключиться к серверу. Проверьте что backend запущен на порту 8000');
        return;
    }

    await refreshTasks();
    console.log('✅ Приложение готово!');
}

// Запуск при загрузке страницы
document.addEventListener('DOMContentLoaded', init);