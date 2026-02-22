import { Router } from 'express';
import { db } from '../db.js';

const router = Router();

router.get('/', (req, res) => {
  const list = db.getConversationsForUser(req.userId);
  const withDetails = list.map((c) => {
    const memberIds = c.members || db.getMemberIds(c.id);
    const others = memberIds.filter((id) => id !== req.userId);
    const names = others.map((id) => db.findUserById(id)?.name || db.findUserById(id)?.email || db.findUserById(id)?.phone || '');
    const label = c.type === 'group' ? c.name : names.join('، ');
    return { ...c, label, memberIds };
  });
  res.json({ conversations: withDetails });
});

router.get('/:id', (req, res) => {
  const conv = db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  res.json(conv);
});

router.get('/:id/messages', (req, res) => {
  const conv = db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  const limit = Math.min(parseInt(req.query.limit, 10) || 100, 200);
  const beforeId = req.query.before ? parseInt(req.query.before, 10) : null;
  const messages = db.getMessagesForConversation(conv.id, limit, beforeId);
  const withSenders = messages.map((m) => ({
    ...m,
    sender: db.findUserById(m.sender_id) ? { id: db.findUserById(m.sender_id).id, name: db.findUserById(m.sender_id).name, email: db.findUserById(m.sender_id).email, phone: db.findUserById(m.sender_id).phone } : null
  }));
  res.json({ messages: withSenders });
});

router.post('/direct', (req, res) => {
  const { otherUserId } = req.body || {};
  if (!otherUserId) return res.status(400).json({ error: 'المستخدم الآخر مطلوب' });
  const other = db.findUserById(otherUserId);
  if (!other) return res.status(404).json({ error: 'المستخدم غير موجود' });
  const { conversation } = db.getOrCreateDirectConversation(req.userId, otherUserId);
  const label = other.name || other.email || other.phone || 'محادثة';
  res.json({ ...conversation, label });
});

router.post('/group', (req, res) => {
  const { name, memberIds } = req.body || {};
  const conv = db.createGroupConversation(req.userId, name, Array.isArray(memberIds) ? memberIds : []);
  res.json({ ...conv, label: conv.name });
});

export default router;
