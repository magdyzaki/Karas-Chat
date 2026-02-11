const express = require('express');
const db = require('../db');
const { auth } = require('../middleware/auth');

const router = express.Router();
router.use(auth);

router.get('/', async (req, res) => {
  try {
    const rows = await db.getRemindersByUserId(req.userId);
    res.json({ reminders: rows });
  } catch (e) {
    res.status(500).json({ error: e.message || 'خطأ في التحميل' });
  }
});

router.post('/', async (req, res) => {
  try {
    const { title, body, remind_at, repeat, notes } = req.body || {};
    if (!title || !remind_at) {
      return res.status(400).json({ error: 'العنوان ووقت التذكير مطلوبان' });
    }
    const row = await db.addReminder({
      user_id: req.userId,
      title: (title || '').trim(),
      body: (body || '').trim(),
      remind_at,
      repeat: (repeat || '') || null,
      notes: (notes || '').trim()
    });
    res.status(201).json(row);
  } catch (e) {
    res.status(500).json({ error: e.message || 'خطأ في الإضافة' });
  }
});

router.put('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { title, body, remind_at, repeat, notes } = req.body || {};
    const existing = await db.getReminderByIdAndUser(id, req.userId);
    if (!existing) return res.status(404).json({ error: 'التنبيه غير موجود' });
    const newTitle = title !== undefined ? String(title).trim() : existing.title;
    const newBody = body !== undefined ? String(body || '').trim() : existing.body;
    const newRemindAt = remind_at !== undefined ? remind_at : existing.remind_at;
    const newRepeat = repeat !== undefined ? (repeat || null) : existing.repeat;
    const newNotes = notes !== undefined ? String(notes || '').trim() : (existing.notes !== undefined ? existing.notes : '');
    const row = await db.updateReminder(id, req.userId, {
      title: newTitle,
      body: newBody,
      remind_at: newRemindAt,
      repeat: newRepeat,
      notes: newNotes
    });
    res.json(row);
  } catch (e) {
    res.status(500).json({ error: e.message || 'خطأ في التعديل' });
  }
});

router.delete('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const deleted = await db.deleteReminder(id, req.userId);
    if (deleted === 0) return res.status(404).json({ error: 'التنبيه غير موجود' });
    res.json({ deleted: true });
  } catch (e) {
    res.status(500).json({ error: e.message || 'خطأ في الحذف' });
  }
});

module.exports = router;
