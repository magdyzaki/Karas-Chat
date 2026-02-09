const express = require('express');
const db = require('../db');
const { auth } = require('../middleware/auth');

const router = express.Router();
router.use(auth);

// قائمة التنبيهات للمستخدم (للمزامنة)
router.get('/', (req, res) => {
  const rows = db.getRemindersByUserId(req.userId);
  res.json({ reminders: rows });
});

// إضافة تنبيه
router.post('/', (req, res) => {
  const { title, body, remind_at, repeat, notes } = req.body || {};
  if (!title || !remind_at) {
    return res.status(400).json({ error: 'العنوان ووقت التذكير مطلوبان' });
  }
  const row = db.addReminder({
    user_id: req.userId,
    title: (title || '').trim(),
    body: (body || '').trim(),
    remind_at,
    repeat: (repeat || '') || null,
    notes: (notes || '').trim()
  });
  res.status(201).json(row);
});

// تعديل تنبيه
router.put('/:id', (req, res) => {
  const { id } = req.params;
  const { title, body, remind_at, repeat, notes } = req.body || {};
  const existing = db.getReminderByIdAndUser(id, req.userId);
  if (!existing) return res.status(404).json({ error: 'التنبيه غير موجود' });
  const newTitle = title !== undefined ? String(title).trim() : existing.title;
  const newBody = body !== undefined ? String(body || '').trim() : existing.body;
  const newRemindAt = remind_at !== undefined ? remind_at : existing.remind_at;
  const newRepeat = repeat !== undefined ? (repeat || null) : existing.repeat;
  const newNotes = notes !== undefined ? String(notes || '').trim() : (existing.notes !== undefined ? existing.notes : '');
  const row = db.updateReminder(id, req.userId, {
    title: newTitle,
    body: newBody,
    remind_at: newRemindAt,
    repeat: newRepeat,
    notes: newNotes
  });
  res.json(row);
});

// حذف تنبيه
router.delete('/:id', (req, res) => {
  const { id } = req.params;
  const deleted = db.deleteReminder(id, req.userId);
  if (deleted === 0) return res.status(404).json({ error: 'التنبيه غير موجود' });
  res.json({ deleted: true });
});

module.exports = router;
