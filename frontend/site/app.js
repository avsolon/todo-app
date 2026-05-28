const API_BASE = '/api/tasks';

async function fetchTasks() {
    const res = await fetch(API_BASE);
    if (!res.ok) throw new Error('Ошибка загрузки');
    return await res.json();
}

async function createTask(title, description) {
    const res = await fetch(API_BASE, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({title, description: description || null})
    });
    if (!res.ok) throw new Error('Ошибка создания');
    return await res.json();
}

async function updateTask(id, data) {
    const res = await fetch(`${API_BASE}/${id}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error('Ошибка обновления');
    return await res.json();
}

async function deleteTask(id) {
    await fetch(`${API_BASE}/${id}`, { method: 'DELETE' });
}

function renderTasks(tasks) {
    const list = document.getElementById('task-list');
    list.innerHTML = '';
    tasks.forEach(task => {
        const li = document.createElement('li');
        li.innerHTML = `
            <input type="checkbox" class="task-checkbox" data-id="${task.id}" ${task.completed ? 'checked' : ''}>
            <div class="task-text ${task.completed ? 'completed' : ''}">
                <strong>${escapeHtml(task.title)}</strong>
                ${task.description ? `<br><small>${escapeHtml(task.description)}</small>` : ''}
            </div>
            <div class="task-actions">
                <button class="edit-btn" data-id="${task.id}">✎</button>
                <button class="delete-btn" data-id="${task.id}">✕</button>
            </div>
        `;
        list.appendChild(li);
    });

    // Обработчики чекбоксов
    document.querySelectorAll('.task-checkbox').forEach(cb => {
        cb.addEventListener('change', async (e) => {
            const id = parseInt(e.target.getAttribute('data-id'));
            await updateTask(id, { completed: e.target.checked });
            refresh();
        });
    });

    // Удаление
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const id = parseInt(e.target.getAttribute('data-id'));
            await deleteTask(id);
            refresh();
        });
    });

    // Заглушка редактирования: просто запрашиваем новое название
    document.querySelectorAll('.edit-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const id = parseInt(e.target.getAttribute('data-id'));
            const newTitle = prompt('Новое название:');
            if (newTitle !== null && newTitle.trim() !== '') {
                await updateTask(id, { title: newTitle });
                refresh();
            }
        });
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function refresh() {
    try {
        const tasks = await fetchTasks();
        renderTasks(tasks);
    } catch (e) {
        console.error(e);
        alert('Не удалось загрузить список дел');
    }
}

document.getElementById('task-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const title = document.getElementById('task-title').value.trim();
    const desc = document.getElementById('task-desc').value.trim();
    if (!title) return;
    try {
        await createTask(title, desc || null);
        document.getElementById('task-title').value = '';
        document.getElementById('task-desc').value = '';
        refresh();
    } catch (err) {
        alert('Ошибка при добавлении');
    }
});

// Загрузка при старте
refresh();