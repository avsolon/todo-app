// ============================================
// Todo Calendar - JavaScript приложение
// ============================================

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
// Константы
// ============================================
const PRIORITY_COLORS = {
    'low': '#FFF9C4',
    'normal': '#BBDEFB',
    'high': '#E1BEE7',
    'urgent': '#FFCDD2',
};

const PRIORITY_NAMES = {
    'low': 'Низкий',
    'normal': 'Обычный',
    'high': 'Высокий',
    'urgent': 'Супер важно!',
};

const PRIORITY_ICONS = {
    'low': '🟡',
    'normal': '🔵',
    'high': '🟣',
    'urgent': '🔴',
};

// ============================================
// Защита от XSS и валидация на фронте
// ============================================

/**
 * Очистка строки от HTML-тегов и опасных символов
 */
function sanitizeInput(str) {
    if (!str) return '';

    // Удаляем HTML-теги
    str = str.replace(/<[^>]*>/g, '');

    // Удаляем потенциально опасные конструкции
    str = str.replace(/javascript:/gi, '');
    str = str.replace(/on\w+\s*=/gi, '');
    str = str.replace(/&#/g, '');
    str = str.replace(/\\x/g, '');

    // Удаляем управляющие символы
    str = str.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '');

    return str.trim();
}

/**
 * Валидация заголовка задачи
 */
function validateTitle(title) {
    if (!title || title.trim().length === 0) {
        return { valid: false, error: 'Введите название задачи' };
    }

    if (title.length > 200) {
        return { valid: false, error: 'Название не должно превышать 200 символов' };
    }

    // Проверка на подозрительные паттерны
    const suspicious = /(\b(select|insert|update|delete|drop|union|alter|create|exec|execute|script|javascript)\b)/i;
    if (suspicious.test(title)) {
        return { valid: false, error: 'Название содержит недопустимые символы' };
    }

    return { valid: true };
}

/**
 * Валидация описания задачи
 */
function validateDescription(desc) {
    if (!desc) return { valid: true };

    if (desc.length > 2000) {
        return { valid: false, error: 'Описание не должно превышать 2000 символов' };
    }

    return { valid: true };
}

// ============================================
// Утилиты
// ============================================
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function formatDateDisplay(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${day}.${month}.${year}`;
}

function formatTime(timeStr) {
    if (!timeStr) return '';
    return timeStr;
}

function getMonday(date) {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? -6 : 1);
    d.setDate(diff);
    d.setHours(0, 0, 0, 0);
    return d;
}

function getWeekDates(date) {
    const monday = getMonday(date);
    return Array.from({length: 7}, (_, i) => {
        const d = new Date(monday);
        d.setDate(d.getDate() + i);
        return d;
    });
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

function generateTimeSlots() {
    const slots = [];
    for (let hour = 0; hour < 24; hour++) {
        for (let minute of [0, 15, 30, 45]) {
            const h = String(hour).padStart(2, '0');
            const m = String(minute).padStart(2, '0');
            slots.push(`${h}:${m}`);
        }
    }
    return slots;
}

function timeToMinutes(timeStr) {
    if (!timeStr) return 0;
    const [h, m] = timeStr.split(':').map(Number);
    return h * 60 + m;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================
// API вызовы
// ============================================
async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: { 'Content-Type': 'application/json', ...options.headers },
            ...options
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const detail = errorData.detail || `HTTP ${response.status}`;

            if (Array.isArray(detail)) {
                const messages = detail.map(e => e.msg).join('\n');
                throw new Error(messages);
            }

            throw new Error(detail);
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
// Мини-календарь
// ============================================
function renderMiniCalendar() {
    const date = state.miniCalendarDate;
    const year = date.getFullYear();
    const month = date.getMonth();

    document.getElementById('mini-month-year').textContent =
        date.toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' });

    const grid = document.getElementById('mini-calendar-days');
    grid.querySelectorAll('.mini-day').forEach(d => d.remove());

    const firstDay = new Date(year, month, 1);
    let startDay = firstDay.getDay();
    startDay = startDay === 0 ? 6 : startDay - 1;

    const lastDay = new Date(year, month + 1, 0);

    // Предыдущий месяц
    const prevLastDay = new Date(year, month, 0);
    for (let i = startDay - 1; i >= 0; i--) {
        grid.appendChild(createMiniDay(new Date(year, month - 1, prevLastDay.getDate() - i), true));
    }

    // Текущий месяц
    for (let day = 1; day <= lastDay.getDate(); day++) {
        grid.appendChild(createMiniDay(new Date(year, month, day), false));
    }

    // Следующий месяц
    const totalCells = startDay + lastDay.getDate();
    const remainingCells = totalCells % 7 === 0 ? 0 : 7 - (totalCells % 7);
    for (let day = 1; day <= remainingCells; day++) {
        grid.appendChild(createMiniDay(new Date(year, month + 1, day), true));
    }
}

function createMiniDay(date, isOtherMonth) {
    const div = document.createElement('div');
    div.className = 'mini-day';
    div.textContent = date.getDate();

    if (isOtherMonth) div.classList.add('other-month');
    if (isToday(date)) div.classList.add('today');
    if (isSameDate(date, state.selectedDate)) div.classList.add('selected');

    const dateStr = formatDate(date);
    if (state.tasks[dateStr]?.length > 0) {
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

    const calendarContainer = document.getElementById('calendar-container');
    const dayListContainer = document.getElementById('day-list-container');

    if (state.currentView === 'day') {
        // Показываем список задач, скрываем календарь
        calendarContainer.style.display = 'none';
        dayListContainer.style.display = 'block';
        renderDayListView();
    } else {
        // Показываем календарь, скрываем список
        calendarContainer.style.display = 'flex';
        dayListContainer.style.display = 'none';
        renderWeekView();
    }
}

function updateHeader() {
    if (state.currentView === 'week') {
        const dates = getWeekDates(getMonday(state.currentDate));
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

    // ===== Очищаем всё =====
    // Удаляем все day-header (кроме time-column-header)
    weekHeader.querySelectorAll('.day-header').forEach(el => el.remove());

    // Очищаем контейнеры
    daysContainer.innerHTML = '';
    timeColumn.innerHTML = '';

    // ===== 1. Строим колонку времени =====
    const timeSlots = generateTimeSlots();

    timeSlots.forEach((slot) => {
        const [h, m] = slot.split(':');
        const timeSlotDiv = document.createElement('div');
        timeSlotDiv.className = 'time-slot';
        timeSlotDiv.style.height = '15px'; // 15 минут = 15px

        // Показываем метку только для целых часов
        if (m === '00') {
            timeSlotDiv.textContent = `${h}:00`;
            timeSlotDiv.classList.add('full-hour');
        }

        timeColumn.appendChild(timeSlotDiv);
    });

    // ===== 2. Строим заголовки дней недели =====
    dates.forEach((date) => {
        const dayHeader = document.createElement('div');
        dayHeader.className = 'day-header';

        if (isToday(date)) {
            dayHeader.classList.add('today');
        }

        dayHeader.innerHTML = `
            <div class="day-name">${date.toLocaleDateString('ru-RU', { weekday: 'short' })}</div>
            <div class="day-number">${date.getDate()}</div>
        `;

        // Добавляем в week-header (после time-column-header)
        weekHeader.appendChild(dayHeader);
    });

    // ===== 3. Строим колонки дней с задачами =====
    dates.forEach((date) => {
        const dayColumn = document.createElement('div');
        dayColumn.className = 'day-column';

        if (isToday(date)) {
            dayColumn.classList.add('today');
        }

        // Добавляем ячейки для каждого временного слота
        timeSlots.forEach((slot) => {
            const [h, m] = slot.split(':');
            const hourCell = document.createElement('div');
            hourCell.className = 'hour-cell';
            hourCell.style.height = '15px'; // 15 минут = 15px

            // Разделители для целых часов
            if (m === '00' && h !== '00') {
                hourCell.classList.add('full-hour');
            }
            // Пунктирные разделители для получасов
            if (m === '30') {
                hourCell.classList.add('half-hour');
            }

            // Клик для создания задачи в этом слоте
            hourCell.addEventListener('click', () => {
                const clickedDate = new Date(date);
                openTaskModal(null, clickedDate, slot);
            });

            dayColumn.appendChild(hourCell);
        });

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

function renderDayListView() {
    const dateStr = formatDate(state.selectedDate);
    const dayTasks = state.tasks[dateStr] || [];

    // Заголовок
    document.getElementById('day-list-title').textContent =
        `Задачи на ${state.selectedDate.toLocaleDateString('ru-RU', {
            weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
        })}`;

    // Статистика
    const total = dayTasks.length;
    const completed = dayTasks.filter(t => t.completed).length;
    const urgent = dayTasks.filter(t => t.priority === 'urgent' && !t.completed).length;

    document.getElementById('day-stats').innerHTML = `
        <div class="stat">
            Всего: <span class="stat-value">${total}</span>
        </div>
        <div class="stat">
            Выполнено: <span class="stat-value">${completed}</span>
        </div>
        ${urgent > 0 ? `
        <div class="stat" style="color: #D32F2F;">
            🔴 Срочных: <span class="stat-value">${urgent}</span>
        </div>` : ''}
        ${total > 0 ? `
        <div class="stat">
            Осталось: <span class="stat-value">${total - completed}</span>
        </div>` : ''}
    `;

    // Список задач
    const dayList = document.getElementById('day-list');
    dayList.innerHTML = '';

    if (dayTasks.length === 0) {
        dayList.innerHTML = `
            <div class="day-list-empty">
                <div class="empty-icon">📝</div>
                <h3>Нет задач на этот день</h3>
                <p>Нажмите кнопку ниже чтобы добавить задачу</p>
                <button class="btn-primary" onclick="document.getElementById('add-task-btn').click()">
                    + Создать задачу
                </button>
            </div>
        `;
        return;
    }

    // Сортируем: сначала по времени, потом по приоритету
    const sortedTasks = [...dayTasks].sort((a, b) => {
        // Задачи без времени в конце
        if (!a.due_time && b.due_time) return 1;
        if (a.due_time && !b.due_time) return -1;

        // Сортировка по времени
        if (a.due_time && b.due_time) {
            const timeCompare = a.due_time.localeCompare(b.due_time);
            if (timeCompare !== 0) return timeCompare;
        }

        // Сортировка по приоритету
        const priorityOrder = { urgent: 0, high: 1, normal: 2, low: 3 };
        return priorityOrder[a.priority] - priorityOrder[b.priority];
    });

    sortedTasks.forEach(task => {
        dayList.appendChild(createTaskCard(task));
    });
}

function createTaskCard(task) {
    const card = document.createElement('div');
    card.className = 'task-card';
    if (task.completed) card.classList.add('completed');

    const bgColor = task.color || PRIORITY_COLORS[task.priority] || '#BBDEFB';

    card.innerHTML = `
        <!-- Чекбокс -->
        <input type="checkbox"
               class="task-card-checkbox"
               ${task.completed ? 'checked' : ''}
               title="Отметить как выполненное">

        <!-- Индикатор приоритета -->
        <div class="task-card-priority ${task.priority}"></div>

        <!-- Контент -->
        <div class="task-card-content">
            <div class="task-card-title">${escapeHtml(task.title)}</div>
            ${task.description ? `
                <div class="task-card-description">${escapeHtml(task.description)}</div>
            ` : ''}
            <div class="task-card-meta">
                ${task.due_time ? `
                    <span class="task-card-time">🕐 ${task.due_time}</span>
                ` : `
                    <span class="task-card-time">📅 Весь день</span>
                `}
                <span class="task-card-priority-badge ${task.priority}">
                    ${PRIORITY_ICONS[task.priority]} ${PRIORITY_NAMES[task.priority]}
                </span>
                ${task.completed ? '<span style="color: #34a853; font-size: 12px;">✅ Выполнено</span>' : ''}
            </div>
        </div>

        <!-- Кнопки действий -->
        <div class="task-card-actions">
            <button class="task-card-btn edit" title="Редактировать">✎</button>
            <button class="task-card-btn delete" title="Удалить">✕</button>
        </div>
    `;

    // Обработчик чекбокса
    const checkbox = card.querySelector('.task-card-checkbox');
    checkbox.addEventListener('click', async (e) => {
        e.stopPropagation();
        try {
            await updateTask(task.id, { completed: checkbox.checked });
            await refreshTasks();
        } catch (error) {
            checkbox.checked = !checkbox.checked;
            alert('Ошибка обновления');
        }
    });

    // Клик по карточке — редактирование
    card.addEventListener('click', (e) => {
        // Не открываем если кликнули по кнопкам или чекбоксу
        if (e.target.closest('.task-card-btn') || e.target.closest('.task-card-checkbox')) {
            return;
        }
        openTaskModal(task);
    });

    // Кнопка редактирования
    card.querySelector('.task-card-btn.edit').addEventListener('click', (e) => {
        e.stopPropagation();
        openTaskModal(task);
    });

    // Кнопка удаления
    card.querySelector('.task-card-btn.delete').addEventListener('click', async (e) => {
        e.stopPropagation();
        if (!confirm('Удалить задачу?')) return;
        try {
            await deleteTask(task.id);
            await refreshTasks();
        } catch (error) {
            alert('Ошибка удаления');
        }
    });

    return card;
}

function createTaskElement(task) {
    const el = document.createElement('div');
    el.className = 'task-event';

    if (task.completed) el.classList.add('completed');
    if (task.priority) el.classList.add(`priority-${task.priority}`);

    // Позиционирование по времени
    if (task.due_time) {
        const minutes = timeToMinutes(task.due_time);
        const topPx = minutes * 1; // 1 минута = 1px (15 минут = 15px)
        el.style.top = `${topPx}px`;
        el.style.minHeight = '18px';
    } else {
        el.style.top = '0px';
        el.style.minHeight = '24px';
    }

    // Цвет фона
    const bgColor = task.color || PRIORITY_COLORS[task.priority] || '#BBDEFB';
    el.style.backgroundColor = bgColor;

    // Для urgent добавляем красную рамку
    if (task.priority === 'urgent') {
        el.style.border = '2px solid #D32F2F';
        el.style.borderLeft = '3px solid #D32F2F';
    }

    el.innerHTML = `
        <div class="event-time">${task.due_time ? formatTime(task.due_time) : 'Весь день'}</div>
        <div class="event-title">${PRIORITY_ICONS[task.priority] || ''} ${escapeHtml(task.title)}</div>
    `;

    // Всплывающая подсказка
    el.title = [
        task.title,
        task.description || '',
        task.due_date ? formatDateDisplay(new Date(task.due_date)) : '',
        task.due_time || '',
        PRIORITY_NAMES[task.priority] || task.priority
    ].filter(Boolean).join('\n');

    // Клик для редактирования
    el.addEventListener('click', (e) => {
        e.stopPropagation();
        openTaskModal(task);
    });

    // Drag and drop
    el.draggable = true;
    el.addEventListener('dragstart', (e) => {
        e.dataTransfer.setData('text/plain', JSON.stringify({
            taskId: task.id
        }));
        el.style.opacity = '0.5';
    });

    el.addEventListener('dragend', () => {
        el.style.opacity = '1';
    });

    return el;
}

// ============================================
// Модальное окно задачи
// ============================================
function populateTimeSelect(selectedTime = null) {
    const select = document.getElementById('task-time-select');
    select.innerHTML = '<option value="">Весь день</option>';

    const timeSlots = generateTimeSlots();
    timeSlots.forEach(slot => {
        const option = document.createElement('option');
        option.value = slot;
        option.textContent = slot;
        if (slot === selectedTime) {
            option.selected = true;
        }
        select.appendChild(option);
    });
}

function openTaskModal(task = null, date = null, time = null) {
    const modal = document.getElementById('task-modal');
    const form = document.getElementById('task-form');

    form.reset();
    populateTimeSelect();

    if (task) {
        // Редактирование
        document.getElementById('modal-title').textContent = 'Редактировать задачу';
        document.getElementById('task-id').value = task.id;
        document.getElementById('task-title-input').value = task.title;
        document.getElementById('task-desc-input').value = task.description || '';
        document.getElementById('task-date-input').value = task.due_date || '';
        document.getElementById('task-priority').value = task.priority || 'normal';
        document.getElementById('task-color').value = task.color || PRIORITY_COLORS[task.priority] || '#BBDEFB';
        document.getElementById('delete-task-btn').style.display = 'block';

        if (task.due_time) {
            populateTimeSelect(task.due_time);
        }

        state.editingTaskId = task.id;
    } else {
        // Создание новой
        document.getElementById('modal-title').textContent = 'Новая задача';
        document.getElementById('task-id').value = '';
        document.getElementById('delete-task-btn').style.display = 'none';
        state.editingTaskId = null;

        // Предзаполняем дату
        if (date) {
            document.getElementById('task-date-input').value = formatDate(date);
        } else {
            document.getElementById('task-date-input').value = formatDate(state.selectedDate);
        }

        // Предзаполняем время
        if (time) {
            populateTimeSelect(time);
        }

        // Цвет по умолчанию для обычного приоритета
        document.getElementById('task-priority').value = 'normal';
        document.getElementById('task-color').value = PRIORITY_COLORS['normal'];
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

    // Получаем и очищаем данные
    const rawTitle = document.getElementById('task-title-input').value;
    const rawDesc = document.getElementById('task-desc-input').value;

    // Валидация заголовка
    const titleValidation = validateTitle(rawTitle);
    if (!titleValidation.valid) {
        alert(titleValidation.error);
        return;
    }

    // Валидация описания
    const descValidation = validateDescription(rawDesc);
    if (!descValidation.valid) {
        alert(descValidation.error);
        return;
    }

    // Очищаем данные
    const cleanTitle = sanitizeInput(rawTitle);
    const cleanDesc = rawDesc ? sanitizeInput(rawDesc) : null;

    const taskData = {
        title: cleanTitle,
        description: cleanDesc || null,
        due_date: document.getElementById('task-date-input').value || null,
        due_time: document.getElementById('task-time-select').value || null,
        priority: document.getElementById('task-priority').value,
        color: document.getElementById('task-color').value,
    };

    // Проверяем что после очистки заголовок не стал пустым
    if (!taskData.title) {
        alert('Название задачи не может быть пустым после очистки');
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
        alert('Ошибка сохранения: ' + error.message);
    }
}

async function handleDeleteTask() {
    const taskId = document.getElementById('task-id').value;
    if (!taskId) return;

    if (!confirm('Удалить задачу?')) return;

    try {
        await deleteTask(taskId);
        console.log('✅ Задача удалена');
        closeModal();
        await refreshTasks();
    } catch (error) {
        alert('Ошибка удаления: ' + error.message);
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
    miniStart.setDate(miniStart.getDate() - 7);
    const miniEnd = new Date(state.miniCalendarDate.getFullYear(), state.miniCalendarDate.getMonth() + 1, 0);
    miniEnd.setDate(miniEnd.getDate() + 7);

    const fetchStart = miniStart < startDate ? miniStart : startDate;
    const fetchEnd = miniEnd > endDate ? miniEnd : endDate;

    await fetchTasks(fetchStart, fetchEnd);
    renderMiniCalendar();
    renderCalendar();
}

// ============================================
// Обработчики событий
// ============================================
function initEventListeners() {
    // Кнопка "Сегодня"
    document.getElementById('today-btn').addEventListener('click', () => {
        const today = new Date();
        state.currentDate = today;
        state.selectedDate = today;
        state.miniCalendarDate = today;
        refreshTasks();
    });

    // Навигация по неделям
    document.getElementById('prev-period').addEventListener('click', () => {
        if (state.currentView === 'day') {
            // Переход на предыдущий день
            const newDate = new Date(state.selectedDate);
            newDate.setDate(newDate.getDate() - 1);
            state.selectedDate = newDate;
            state.currentDate = newDate;
            state.miniCalendarDate = newDate;
        } else {
            // Переход на предыдущую неделю
            const monday = getMonday(state.currentDate);
            monday.setDate(monday.getDate() - 7);
            state.currentDate = new Date(monday);
            state.selectedDate = new Date(monday);
            state.miniCalendarDate = new Date(monday);
        }
        refreshTasks();
    });

    document.getElementById('next-period').addEventListener('click', () => {
        if (state.currentView === 'day') {
            // Переход на следующий день
            const newDate = new Date(state.selectedDate);
            newDate.setDate(newDate.getDate() + 1);
            state.selectedDate = newDate;
            state.currentDate = newDate;
            state.miniCalendarDate = newDate;
        } else {
            // Переход на следующую неделю
            const monday = getMonday(state.currentDate);
            monday.setDate(monday.getDate() + 7);
            state.currentDate = new Date(monday);
            state.selectedDate = new Date(monday);
            state.miniCalendarDate = new Date(monday);
        }
        refreshTasks();
    });

    // Навигация по месяцам
    document.getElementById('prev-month').addEventListener('click', () => {
        state.miniCalendarDate = new Date(
            state.miniCalendarDate.getFullYear(),
            state.miniCalendarDate.getMonth() - 1,
            1
        );
        refreshTasks();
    });

    document.getElementById('next-month').addEventListener('click', () => {
        state.miniCalendarDate = new Date(
            state.miniCalendarDate.getFullYear(),
            state.miniCalendarDate.getMonth() + 1,
            1
        );
        refreshTasks();
    });

    // Переключение вида
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.currentView = btn.dataset.view;
            if (state.currentView === 'day') {
                state.currentDate = new Date(state.selectedDate);
            }
            renderCalendar();
        });
    });

    // Кнопка добавления задачи
    document.getElementById('add-task-btn').addEventListener('click', () => {
        openTaskModal(null, state.selectedDate);
    });

    // Модальное окно
    document.getElementById('close-modal').addEventListener('click', closeModal);
    document.getElementById('cancel-btn').addEventListener('click', closeModal);
    document.getElementById('task-modal').addEventListener('click', (e) => {
        if (e.target === document.getElementById('task-modal')) {
            closeModal();
        }
    });

    // Форма
    document.getElementById('task-form').addEventListener('submit', handleFormSubmit);
    document.getElementById('delete-task-btn').addEventListener('click', handleDeleteTask);

    // Автоматическая смена цвета при выборе приоритета
    const prioritySelect = document.getElementById('task-priority');
    const colorInput = document.getElementById('task-color');

    prioritySelect.addEventListener('change', () => {
        const priority = prioritySelect.value;
        if (PRIORITY_COLORS[priority]) {
            colorInput.value = PRIORITY_COLORS[priority];
        }
    });

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
        alert('Не удалось подключиться к серверу.\nПроверьте что backend запущен на порту 8000');
        return;
    }

    await refreshTasks();
    console.log('✅ Приложение готово!');
}

// Запуск при загрузке страницы
document.addEventListener('DOMContentLoaded', init);