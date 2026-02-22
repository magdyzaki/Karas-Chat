import { Router } from 'express';
import { db } from '../db.js';

const router = Router();

router.get('/', (req, res) => {
  const list = db.getConversationsForUser(req.userId);
  const withLabel = list.map((c) => {
    const others = (c.members || db.getMemberIds(c.id)).filter((id) => id !== req.userId);
    const names = others.map((id) => { const u = db.findUserById(id); return u ? (u.name || u.email || u.phone || '') : ''; });
    const label = c.type === 'group' ? c.name : names.join('، ');
    return { ...c, label };
  });
  res.json({ conversations: withLabel });
});

router.get('/:id', (req, res) => {
  const conv = db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  const others = (conv.members || db.getMemberIds(conv.id)).filter((id) => id !== req.userId);
  const label = conv.type === 'group' ? conv.name : others.map((id) => { const u = db.findUserById(id); return u ? (u.name || u.email || u.phone || '') : ''; }).join('، ');
  res.json({ ...conv, label });
});

router.get('/:id/messages', (req, res) => {
  const conv = db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  const limit = Math.min(parseInt(req.query.limit, 10) || 100, 200);
  const before = req.query.before ? parseInt(req.query.before, 10) : null;
  const messages = db.getMessagesForConversation(conv.id, limit, before);
  const withSenders = messages.map((m) => {
    const u = db.findUserById(m.sender_id);
    return { ...m, sender: u ? { id: u.id, name: u.name, email: u.email, phone: u.phone } : null };
  });
  res.json({ messages: withSenders });
});

router.post('/direct', (req, res) => {
  const { otherUserId } = req.body || {};
  if (!otherUserId) return res.status(400).json({ error: 'معرف المستخدم مطلوب' });
  const other = db.findUserById(otherUserId);
  if (!other) return res.status(404).json({ error: 'المستخدم غير موجود' });
  const { conversation } = db.getOrCreateDirectConversation(req.userId, otherUserId);
  const label = other.name || other.email || other.phone || 'محادثة';
  res.json({ ...conversation, label, memberIds: db.getMemberIds(conversation.id) });
});

router.post('/group', (req, res) => {
  const { name, memberIds } = req.body || {};
  const conv = db.createGroupConversation(req.userId, name || 'مجموعة', Array.isArray(memberIds) ? memberIds : []);
  res.json({ ...conv, label: conv.name, memberIds: db.getMemberIds(conv.id) });
});

export default router;
