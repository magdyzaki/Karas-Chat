import { Router } from 'express';
import { db } from '../db.js';

const router = Router();

router.get('/', (req, res) => {
  const list = db.getBroadcastLists(req.userId);
  const withRecipients = list.map((b) => {
    const recipients = (b.recipient_ids || []).map((id) => {
      const u = db.findUserById(id);
      return u ? { id: u.id, name: u.name, email: u.email, phone: u.phone } : { id, name: '?' };
    });
    return { ...b, recipients };
  });
  res.json({ lists: withRecipients });
});

router.post('/', (req, res) => {
  const { name, recipientIds } = req.body || {};
  const ids = Array.isArray(recipientIds) ? recipientIds : [];
  if (!ids.length) return res.status(400).json({ error: 'اختر جهة اتصال واحدة على الأقل' });
  const filtered = ids.filter((id) => Number(id) !== Number(req.userId));
  if (!filtered.length) return res.status(400).json({ error: 'لا يمكنك إرسال لنفسك فقط' });
  const list = db.createBroadcastList(req.userId, name, filtered);
  const recipients = (list.recipient_ids || []).map((id) => {
    const u = db.findUserById(id);
    return u ? { id: u.id, name: u.name, email: u.email, phone: u.phone } : { id, name: '?' };
  });
  res.json({ ...list, recipients });
});

router.patch('/:id', (req, res) => {
  const { name, recipientIds } = req.body || {};
  const list = db.getBroadcastListById(req.params.id, req.userId);
  if (!list) return res.status(404).json({ error: 'القائمة غير موجودة' });
  const ids = recipientIds !== undefined ? (Array.isArray(recipientIds) ? recipientIds : []).filter((id) => Number(id) !== Number(req.userId)) : undefined;
  const updated = db.updateBroadcastList(list.id, req.userId, name, ids);
  if (!updated) return res.status(500).json({ error: 'فشل التحديث' });
  const recipients = (updated.recipient_ids || []).map((id) => {
    const u = db.findUserById(id);
    return u ? { id: u.id, name: u.name, email: u.email, phone: u.phone } : { id, name: '?' };
  });
  res.json({ ...updated, recipients });
});

router.delete('/:id', (req, res) => {
  const list = db.getBroadcastListById(req.params.id, req.userId);
  if (!list) return res.status(404).json({ error: 'القائمة غير موجودة' });
  db.deleteBroadcastList(list.id, req.userId);
  res.json({ ok: true });
});

router.post('/:id/send', (req, res) => {
  const list = db.getBroadcastListById(req.params.id, req.userId);
  if (!list) return res.status(404).json({ error: 'القائمة غير موجودة' });
  const { type = 'text', content, file_name } = req.body || {};
  if (type === 'text' && !content) return res.status(400).json({ error: 'اكتب الرسالة' });
  const ids = (list.recipient_ids || []).filter(Boolean);
  if (!ids.length) return res.status(400).json({ error: 'القائمة فارغة' });
  const user = db.findUserById(req.userId);
  const io = req.app.get('io');
  const results = [];
  for (const rid of ids) {
    const { conversation } = db.getOrCreateDirectConversation(req.userId, rid);
    const msg = db.addMessage({
      conversation_id: conversation.id,
      sender_id: req.userId,
      type,
      content: content || '',
      file_name: file_name || null
    });
    const payload = { ...msg, conversation_id: conversation.id, sender: user ? { id: user.id, name: user.name, email: user.email, phone: user.phone } : null };
    if (io) io.to('conv_' + conversation.id).emit('new_message', payload);
    results.push({ conversationId: conversation.id, messageId: msg.id });
  }
  res.json({ ok: true, sent: results.length });
});

export default router;
