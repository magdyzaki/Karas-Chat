import { Router } from 'express';
import { db } from '../db.js';

const router = Router();

/**
 * تصدير نسخة احتياطية من محادثات ورسائل المستخدم
 */
router.get('/export', (req, res) => {
  const userId = Number(req.userId);
  const conversations = db.getConversationsForUser(userId);
  const backup = {
    version: 1,
    exportedAt: new Date().toISOString(),
    userId,
    conversations: []
  };

  for (const c of conversations) {
    const msgs = db.getMessagesForConversation(c.id, 5000, null, userId);
    const prefs = db.getConversationPref(userId, c.id);
    backup.conversations.push({
      id: c.id,
      type: c.type,
      name: c.name,
      members: c.members || db.getMemberIds(c.id),
      muted: prefs.muted,
      archived: prefs.archived,
      messages: msgs.map((m) => ({
        id: m.id,
        sender_id: m.sender_id,
        type: m.type,
        content: m.content,
        file_name: m.file_name,
        reply_to_id: m.reply_to_id,
        reply_to_snippet: m.reply_to_snippet,
        encrypted: !!m.encrypted,
        iv: m.iv || null,
        created_at: m.created_at
      }))
    });
  }

  const lists = db.getBroadcastLists(userId);
  backup.broadcastLists = lists.map((b) => ({ id: b.id, name: b.name, recipient_ids: b.recipient_ids || [], created_at: b.created_at }));

  res.setHeader('Content-Disposition', `attachment; filename="chat-backup-${Date.now()}.json"`);
  res.setHeader('Content-Type', 'application/json');
  res.json(backup);
});

export default router;
