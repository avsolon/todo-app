# Tasks

## Done
- [x] Bot: fix time-selection callback pattern in `bot/main.py`
      `pattern=r"^(time_\d{2}:\d{2}|time_allday|cancel_add)$"` (was `time_`)
- [x] Verify bot fix with Python regex test (time_07:00, time_00:45 match;
      time_allday, cancel_add still match; time_1:00 impossible — always 2-digit)
- [x] Web: task card opens in static view mode; pencil «✎ Редактировать» button
      switches to edit mode (`setModalMode('view'|'edit')`, `state.modalMode`)
- [x] Web: «✓ Выполнено» button on task card (only when not completed),
      calls `updateTask(task.id, { completed: true })` + refreshTasks
- [x] Web: green «Встреча/Конференция» added to sidebar legend (index.html),
      `.task-card-priority.meeting`, `.task-card-priority-badge.meeting`,
      `.task-card-btn.done:hover` styles (style.css)

## Current
- (none in progress)

## Next
- [ ] Test bot flow end-to-end (create task → pick time)
- [ ] Test web modal view/edit modes + Выполнено button
- [ ] Deploy / commit when user confirms