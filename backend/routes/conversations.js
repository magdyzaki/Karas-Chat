import { Router } from 'express';
import { db } from '../db-api.js';

const router = Router();

router.get('/', async (req, res) => {
  const list = await db.getConversationsForUser(req.userId);
  const archivedIds = new Set(await db.getArchivedConversationIds(req.userId));
  const withDetails = await Promise.all(list.map(async (c) => {
    const memberIds = c.members?.length ? c.members : await db.getMemberIds(c.id);
    const others = memberIds.filter((id) => id !== req.userId);
    const memberDetails = await Promise.all(others.map(async (id) => {
      const u = await db.findUserById(id);
      return u ? { id: u.id, name: u.name, email: u.email, phone: u.phone, avatar_url: u.avatar_url || null, last_seen_at: u.last_seen_at || null } : { id, name: '', avatar_url: null, last_seen_at: null };
    }));
    const names = memberDetails.map((m) => m.name || m.email || m.phone || '');
    const label = c.type === 'group' ? c.name : names.join('، ');
    const prefs = await db.getConversationPref(req.userId, c.id);
    return { ...c, label, memberIds, memberDetails, muted: prefs.muted, archived: prefs.archived, disappearing_after: prefs.disappearing_after || null };
  }));
  res.json({ conversations: withDetails });
});

router.get('/:id', async (req, res) => {
  const conv = await db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  const memberIds = conv.members?.length ? conv.members : await db.getMemberIds(conv.id);
  const memberDetails = await Promise.all(memberIds.map(async (id) => {
    const u = await db.findUserById(id);
    return u ? { id: u.id, name: u.name, email: u.email, phone: u.phone, avatar_url: u.avatar_url || null, last_seen_at: u.last_seen_at || null } : { id, name: '', avatar_url: null, last_seen_at: null };
  }));
  const prefs = await db.getConversationPref(req.userId, conv.id);
  res.json({ ...conv, memberIds, memberDetails, muted: prefs.muted, archived: prefs.archived, disappearing_after: prefs.disappearing_after || null });
});

router.patch('/:id/mute', async (req, res) => {
  const conv = await db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  db.setConversationMuted(req.userId, conv.id, true);
  res.json({ ok: true, muted: true });
});

router.patch('/:id/unmute', async (req, res) => {
  const conv = await db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  db.setConversationMuted(req.userId, conv.id, false);
  res.json({ ok: true, muted: false });
});

router.patch('/:id/archive', async (req, res) => {
  const conv = await db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  db.setConversationArchived(req.userId, conv.id, true);
  res.json({ ok: true });
});

router.patch('/:id/unarchive', async (req, res) => {
  const conv = await db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  db.setConversationArchived(req.userId, conv.id, false);
  res.json({ ok: true });
});

router.patch('/:id/disappearing', async (req, res) => {
  const conv = await db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  const { seconds } = req.body || {};
  const val = seconds != null ? Number(seconds) : null;
  const allowed = [null, 86400, 604800, 7776000];
  if (val !== null && !allowed.includes(val)) return res.status(400).json({ error: 'قيمة غير مدعومة. استخدم: null أو 86400 (24 ساعة) أو 604800 (7 أيام) أو 7776000 (90 يوم)' });
  db.setConversationDisappearing(req.userId, conv.id, val);
  res.json({ ok: true, disappearing_after: val });
});

router.post('/:id/forward', async (req, res) => {
  const conv = await db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  const { fromConversationId, messageId } = req.body || {};
  if (!fromConversationId || !messageId) return res.status(400).json({ error: 'المحادثة الأصل والرسالة مطلوبان' });
  const fromConv = await db.getConversationByIdAndUser(fromConversationId, req.userId);
  if (!fromConv) return res.status(404).json({ error: 'المحادثة الأصل غير موجودة' });
  const msgs = await db.getMessagesForConversation(fromConversationId, 500, null, req.userId);
  const orig = msgs.find((m) => m.id === Number(messageId) && !m.deleted_for_everyone);
  if (!orig) return res.status(404).json({ error: 'الرسالة غير موجودة' });
  if (orig.encrypted) return res.status(400).json({ error: 'لا يمكن إعادة توجيه الرسائل المشفرة' });
  const snippet = orig.type === 'text' ? (orig.content || '').slice(0, 100) : orig.type === 'image' ? '🖼 صورة' : orig.type === 'video' ? '🎬 فيديو' : orig.type === 'voice' ? '🎤 صوت' : orig.type === 'location' ? '📍 موقع' : orig.type === 'poll' ? '📊 استطلاع' : '📎 ملف';
  const msg = await db.addMessage({
    conversation_id: conv.id,
    sender_id: req.userId,
    type: orig.type,
    content: orig.content || '',
    file_name: orig.file_name || null,
    reply_to_id: null,
    reply_to_snippet: '↩ ' + snippet
  });
  const user = await db.findUserById(req.userId);
  const payload = { ...msg, conversation_id: conv.id, sender: user ? { id: user.id, name: user.name, email: user.email, phone: user.phone } : null };
  const io = req.app.get('io');
  if (io) io.to('conv_' + conv.id).emit('new_message', payload);
  res.json({ message: payload });
});

router.post('/:id/messages', async (req, res) => {
  const conv = await db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  const { type, content, file_name, reply_to_id, reply_to_snippet, encrypted, iv } = req.body || {};
  if (!content && (type === 'text' || type === 'poll' || !type)) return res.status(400).json({ error: 'محتوى الرسالة مطلوب' });
  const msg = await db.addMessage({
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
  const user = await db.findUserById(req.userId);
  const payload = { ...msg, sender: user ? { id: user.id, name: user.name, email: user.email, phone: user.phone } : null };
  if (msg.encrypted) payload.sender_public_key = await db.getUserPublicKey(req.userId);
  const io = req.app.get('io');
  if (io) io.to('conv_' + conv.id).emit('new_message', payload);
  res.json({ message: payload });
});

router.get('/:id/messages', async (req, res) => {
  const conv = await db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  const limit = Math.min(parseInt(req.query.limit, 10) || 100, 200);
  const beforeId = req.query.before ? parseInt(req.query.before, 10) : null;
  const messages = await db.getMessagesForConversation(conv.id, limit, beforeId, req.userId);
  const withSenders = await Promise.all(messages.map(async (m) => {
    const u = await db.findUserById(m.sender_id);
    return {
      ...m,
      sender: u ? { id: u.id, name: u.name, email: u.email, phone: u.phone, avatar_url: u.avatar_url || null } : null,
      sender_public_key: m.encrypted ? await db.getUserPublicKey(m.sender_id) : null
    };
  }));
  const [readReceipts, reactions, pollVotes] = await Promise.all([
    db.getConversationReads(conv.id),
    db.getMessageReactions(conv.id),
    db.getPollVotes(conv.id)
  ]);
  res.json({ messages: withSenders, readReceipts, reactions, pollVotes });
});

router.post('/:id/messages/:msgId/vote', async (req, res) => {
  const conv = await db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  const messageId = parseInt(req.params.msgId, 10);
  const { optionIndex } = req.body || {};
  if (messageId == null || optionIndex == null) return res.status(400).json({ error: 'معرف الرسالة والخيار مطلوبان' });
  const ok = await db.addPollVote(messageId, conv.id, req.userId, Number(optionIndex));
  if (!ok) return res.status(400).json({ error: 'فشل التصويت' });
  const io = req.app.get('io');
  if (io) io.to('conv_' + conv.id).emit('poll_voted', { conversationId: conv.id, messageId, userId: req.userId, optionIndex: Number(optionIndex) });
  res.json({ ok: true });
});

router.post('/:id/messages/:msgId/delete', async (req, res) => {
  const conv = await db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  const { forEveryone } = req.body || {};
  const messageId = parseInt(req.params.msgId, 10);
  if (!messageId) return res.status(400).json({ error: 'معرف الرسالة غير صالح' });
  const ok = forEveryone
    ? await db.deleteMessageForEveryone(messageId, conv.id, req.userId)
    : await db.deleteMessageForMe(messageId, conv.id, req.userId);
  if (!ok) return res.status(400).json({ error: forEveryone ? 'لا يمكنك حذف الرسالة للجميع (ليست رسالتك أو غير موجودة)' : 'فشل حذف الرسالة' });
  res.json({ ok: true });
});

router.post('/direct', async (req, res) => {
  const { otherUserId } = req.body || {};
  if (!otherUserId) return res.status(400).json({ error: 'المستخدم الآخر مطلوب' });
  const other = await db.findUserById(otherUserId);
  if (!other) return res.status(404).json({ error: 'المستخدم غير موجود' });
  const result = await db.getOrCreateDirectConversation(req.userId, otherUserId);
  const { conversation, created } = result || {};
  if (!conversation) return res.status(500).json({ error: 'فشل إنشاء المحادثة' });
  const label = other.name || other.email || other.phone || 'محادثة';
  const memberIds = await db.getMemberIds(conversation.id);
  const io = req.app.get('io');
  const userSockets = req.app.get('userSockets');
  if (io && userSockets && created) {
    const payload = { conversation: { ...conversation, label, memberIds } };
    const sids = userSockets.get(Number(otherUserId));
    if (sids) sids.forEach((sid) => io.to(sid).emit('conversation_added', payload));
  }
  res.json({ ...conversation, label, memberIds });
});

router.post('/group', async (req, res) => {
  const { name, memberIds } = req.body || {};
  const conv = await db.createGroupConversation(req.userId, name, Array.isArray(memberIds) ? memberIds : []);
  if (!conv) return res.status(500).json({ error: 'فشل إنشاء المجموعة' });
  const memberIdsList = await db.getMemberIds(conv.id);
  const io = req.app.get('io');
  const userSockets = req.app.get('userSockets');
  if (io && userSockets) {
    const payload = { conversation: { ...conv, label: conv.name, memberIds: memberIdsList } };
    const others = (memberIdsList || []).filter((id) => Number(id) !== Number(req.userId));
    others.forEach((mid) => {
      const sids = userSockets.get(Number(mid));
      if (sids) sids.forEach((sid) => io.to(sid).emit('conversation_added', payload));
    });
  }
  res.json({ ...conv, label: conv.name, memberIds: memberIdsList });
});

router.post('/:id/leave', async (req, res) => {
  const conv = await db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  if (conv.type === 'direct') return res.status(400).json({ error: 'لا يمكن مغادرة محادثة فردية' });
  const ok = db.leaveConversation(conv.id, req.userId);
  if (!ok) return res.status(400).json({ error: 'فشل مغادرة المجموعة' });
  res.json({ ok: true });
});

router.delete('/:id', async (req, res) => {
  const conv = await db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  const ok = db.deleteConversation(conv.id, req.userId);
  if (!ok) return res.status(403).json({ error: 'فقط منشئ المجموعة يمكنه حذفها' });
  res.json({ ok: true });
});

router.post('/:id/add-member', async (req, res) => {
  const { targetUserId } = req.body || {};
  if (!targetUserId) return res.status(400).json({ error: 'معرف العضو مطلوب' });
  const conv = await db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  const ok = db.addMemberToGroup(conv.id, req.userId, targetUserId);
  if (!ok) return res.status(403).json({ error: 'فقط منشئ المجموعة يمكنه إضافة الأعضاء' });
  res.json({ ok: true });
});

router.post('/:id/remove-member', async (req, res) => {
  const { targetUserId } = req.body || {};
  if (!targetUserId) return res.status(400).json({ error: 'معرف العضو مطلوب' });
  const conv = await db.getConversationByIdAndUser(req.params.id, req.userId);
  if (!conv) return res.status(404).json({ error: 'المحادثة غير موجودة' });
  const ok = db.removeMemberFromGroup(conv.id, req.userId, targetUserId);
  if (!ok) return res.status(403).json({ error: 'فقط منشئ المجموعة يمكنه طرد الأعضاء' });
  res.json({ ok: true });
});

export default router;
