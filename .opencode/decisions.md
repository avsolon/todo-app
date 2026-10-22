# Decisions

- Bot time pattern: use `time_\d{2}:\d{2}` not `time_\d{1,2}` — time buttons
  are always zero-padded 2-digit (`f"{hour:02d}:{minute}"`), so 1-digit never occurs.
- Task card opens in **view** mode (all form fields disabled); editing is an
  explicit action via pencil button. New task still opens directly in edit mode.
- «Отмена» in edit mode returns to view mode (not closes) for existing tasks;
  otherwise closes modal.
- «Выполнено» button shown only for not-completed tasks (redundant with checkbox
  but explicit/visible per user request).
- No backend changes needed: `Task.completed` (bool) already exists; `priority`
  is a free string, so `meeting` works without enum validation.