import { Router } from 'express';
import { db } from '../db.js';

const router = Router();

router.get('/', (req, res) => {
  const list = db.getConversationsForUser(req.userId);
  const archivedIds = new Set(db.getArchivedConversationIds(req.userId));
  const withDetails = list.map((c) => {
    const memberIds = c.members || db.getMemberIds(c.id);
    const others = memberIds.filter((id) => id !== req.userId);
    const memberDetails = others.map((id) => {
      const u = db.findUserById(id);
      return u ? { id: u.id, name: u.name, email: u.email, phone: u.phone, avatar_url: u.avatar_url || null, last_seen_at: u.last_seen_at || null } : { id, name: '', avatar_url: null, last_seen_at: null };
    });
    const names = memberDetails.map((m) => m.name || m.email || m.phone || '');
    const label = c.type === 'group' ? c.name : names.join('، ');
    const prefs = db.getConversationPref(req.userId, c.id);
    return { ...c, label, memberIds, memberDetails, muted: prefs.muted, archived: prefs.archived, disappearing_after: prefs.disappearing_after || null };
  });
  res.json({ conversations: withDetails });
});

router.get('/:id', (req, res) => {
  const conv = db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  const memberIds = conv.members || db.getMemberIds(conv.id);
  const memberDetails = memberIds.map((id) => {
    const u = db.findUserById(id);
    return u ? { id: u.id, name: u.name, email: u.email, phone: u.phone, avatar_url: u.avatar_url || null, last_seen_at: u.last_seen_at || null } : { id, name: '', avatar_url: null, last_seen_at: null };
  });
  const prefs = db.getConversationPref(req.userId, conv.id);
  res.json({ ...conv, memberIds, memberDetails, muted: prefs.muted, archived: prefs.archived, disappearing_after: prefs.disappearing_after || null });
});

router.patch('/:id/mute', (req, res) => {
  const conv = db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  db.setConversationMuted(req.userId, conv.id, true);
  res.json({ ok: true, muted: true });
});

router.patch('/:id/unmute', (req, res) => {
  const conv = db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  db.setConversationMuted(req.userId, conv.id, false);
  res.json({ ok: true, muted: false });
});

router.patch('/:id/archive', (req, res) => {
  const conv = db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  db.setConversationArchived(req.userId, conv.id, true);
  res.json({ ok: true });
});

router.patch('/:id/unarchive', (req, res) => {
  const conv = db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  db.setConversationArchived(req.userId, conv.id, false);
  res.json({ ok: true });
});

router.patch('/:id/disappearing', (req, res) => {
  const conv = db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  const { seconds } = req.body || {};
  const val = seconds != null ? Number(seconds) : null;
  const allowed = [null, 86400, 604800, 7776000];
  if (val !== null && !allowed.includes(val)) return res.status(400).json({ error: 'قيمة غير مدعومة. استخدم: null أو 86400 (24 ساعة) أو 604800 (7 أيام) أو 7776000 (90 يوم)' });
  db.setConversationDisappearing(req.userId, conv.id, val);
  res.json({ ok: true, disappearing_after: val });
});

router.post('/:id/forward', (req, res) => {
  const conv = db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  const { fromConversationId, messageId } = req.body || {};
  if (!fromConversationId || !messageId) return res.status(400).json({ error: 'المحادثة الأصل والرسالة مطلوبان' });
  const fromConv = db.getConversationByIdAndUser(fromConversationId, req.userId);
  if (!fromConv) return res.status(404).json({ error: 'المحادثة الأصل غير موجودة' });
  const msgs = db.getMessagesForConversation(fromConversationId, 500, null, req.userId);
  const orig = msgs.find((m) => m.id === Number(messageId) && !m.deleted_for_everyone);
  if (!orig) return res.status(404).json({ error: 'الرسالة غير موجودة' });
  if (orig.encrypted) return res.status(400).json({ error: 'لا يمكن إعادة توجيه الرسائل المشفرة' });
  const snippet = orig.type === 'text' ? (orig.content || '').slice(0, 100) : orig.type === 'image' ? '🖼 صورة' : orig.type === 'video' ? '🎬 فيديو' : orig.type === 'voice' ? '🎤 صوت' : orig.type === 'location' ? '📍 موقع' : orig.type === 'poll' ? '📊 استطلاع' : '📎 ملف';
  const msg = db.addMessage({
    conversation_id: conv.id,
    sender_id: req.userId,
    type: orig.type,
    content: orig.content || '',
    file_name: orig.file_name || null,
    reply_to_id: null,
    reply_to_snippet: '↩ ' + snippet
  });
  const user = db.findUserById(req.userId);
  const payload = { ...msg, conversation_id: conv.id, sender: user ? { id: user.id, name: user.name, email: user.email, phone: user.phone } : null };
  const io = req.app.get('io');
  if (io) io.to('conv_' + conv.id).emit('new_message', payload);
  res.json({ message: payload });
});

router.post('/:id/messages', (req, res) => {
  const conv = db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  const { type, content, file_name, reply_to_id, reply_to_snippet, encrypted, iv } = req.body || {};
  if (!content && (type === 'text' || type === 'poll' || !type)) return res.status(400).json({ error: 'محتوى الرسالة مطلوب' });
  const msg = db.addMessage({
    conversation_id: conv.id,
    sender_id: req.userId,
    type: type || 'text',
    content: content || '',
    file_name: file_name || null,
    reply_to_id: reply_to_id || null,
    reply_to_snippet: reply_to_snippet || null,
    encrypted: !!encrypted,
    iv: iv || null
  });
  const user = db.findUserById(req.userId);
  const payload = { ...msg, sender: user ? { id: user.id, name: user.name, email: user.email, phone: user.phone } : null };
  if (msg.encrypted) payload.sender_public_key = db.getUserPublicKey(req.userId);
  const io = req.app.get('io');
  if (io) io.to('conv_' + conv.id).emit('new_message', payload);
  res.json({ message: payload });
});

router.get('/:id/messages', (req, res) => {
  const conv = db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  const limit = Math.min(parseInt(req.query.limit, 10) || 100, 200);
  const beforeId = req.query.before ? parseInt(req.query.before, 10) : null;
  const messages = db.getMessagesForConversation(conv.id, limit, beforeId, req.userId);
  const withSenders = messages.map((m) => {
    const u = db.findUserById(m.sender_id);
    return {
      ...m,
      sender: u ? { id: u.id, name: u.name, email: u.email, phone: u.phone, avatar_url: u.avatar_url || null } : null,
      sender_public_key: m.encrypted ? db.getUserPublicKey(m.sender_id) : null
    };
  });
  const readReceipts = db.getConversationReads(conv.id);
  const reactions = db.getMessageReactions(conv.id);
  const pollVotes = db.getPollVotes(conv.id);
  res.json({ messages: withSenders, readReceipts, reactions, pollVotes });
});

router.post('/:id/messages/:msgId/vote', (req, res) => {
  const conv = db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  const messageId = parseInt(req.params.msgId, 10);
  const { optionIndex } = req.body || {};
  if (messageId == null || optionIndex == null) return res.status(400).json({ error: 'معرف الرسالة والخيار مطلوبان' });
  const ok = db.addPollVote(messageId, conv.id, req.userId, Number(optionIndex));
  if (!ok) return res.status(400).json({ error: 'فشل التصويت' });
  const io = req.app.get('io');
  if (io) io.to('conv_' + conv.id).emit('poll_voted', { conversationId: conv.id, messageId, userId: req.userId, optionIndex: Number(optionIndex) });
  res.json({ ok: true });
});

router.post('/:id/messages/:msgId/delete', (req, res) => {
  const conv = db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  const { forEveryone } = req.body || {};
  const messageId = parseInt(req.params.msgId, 10);
  if (!messageId) return res.status(400).json({ error: 'معرف الرسالة غير صالح' });
  const ok = forEveryone
    ? db.deleteMessageForEveryone(messageId, conv.id, req.userId)
    : db.deleteMessageForMe(messageId, conv.id, req.userId);
  if (!ok) return res.status(400).json({ error: forEveryone ? 'لا يمكنك حذف الرسالة للجميع (ليست رسالتك أو غير موجودة)' : 'فشل حذف الرسالة' });
  res.json({ ok: true });
});

router.post('/direct', (req, res) => {
  const { otherUserId } = req.body || {};
  if (!otherUserId) return res.status(400).json({ error: 'المستخدم الآخر مطلوب' });
  const other = db.findUserById(otherUserId);
  if (!other) return res.status(404).json({ error: 'المستخدم غير موجود' });
  const { conversation } = db.getOrCreateDirectConversation(req.userId, otherUserId);
  const label = other.name || other.email || other.phone || 'محادثة';
  const memberIds = db.getMemberIds(conversation.id);
  res.json({ ...conversation, label, memberIds });
});

router.post('/group', (req, res) => {
  const { name, memberIds } = req.body || {};
  const conv = db.createGroupConversation(req.userId, name, Array.isArray(memberIds) ? memberIds : []);
  const memberIdsList = db.getMemberIds(conv.id);
  res.json({ ...conv, label: conv.name, memberIds: memberIdsList });
});

router.post('/:id/leave', (req, res) => {
  const conv = db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  if (conv.type === 'direct') return res.status(400).json({ error: 'لا يمكن مغادرة محادثة فردية' });
  const ok = db.leaveConversation(conv.id, req.userId);
  if (!ok) return res.status(400).json({ error: 'فشل مغادرة المجموعة' });
  res.json({ ok: true });
});

router.delete('/:id', (req, res) => {
  const conv = db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  const ok = db.deleteConversation(conv.id, req.userId);
  if (!ok) return res.status(403).json({ error: 'فقط منشئ المجموعة يمكنه حذفها' });
  res.json({ ok: true });
});

router.post('/:id/add-member', (req, res) => {
  const { targetUserId } = req.body || {};
  if (!targetUserId) return res.status(400).json({ error: 'معرف العضو مطلوب' });
  const conv = db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  const ok = db.addMemberToGroup(conv.id, req.userId, targetUserId);
  if (!ok) return res.status(403).json({ error: 'فقط منشئ المجموعة يمكنه إضافة الأعضاء' });
  res.json({ ok: true });
});

router.post('/:id/remove-member', (req, res) => {
  const { targetUserId } = req.body || {};
  if (!targetUserId) return res.status(400).json({ error: 'معرف العضو مطلوب' });
  const conv = db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  const ok = db.removeMemberFromGroup(conv.id, req.userId, targetUserId);
  if (!ok) return res.status(403).json({ error: 'فقط منشئ المجموعة يمكنه طرد الأعضاء' });
  res.json({ ok: true });
});

export default router;
