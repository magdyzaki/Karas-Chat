import path from 'path';
import { fileURLToPath } from 'url';
import { LowSync } from 'lowdb';
import { JSONFileSync } from 'lowdb/node';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dbPath = process.env.DB_PATH || path.join(__dirname, 'db.json');
const adapter = new JSONFileSync(dbPath);
const low = new LowSync(adapter, {
  users: [],
  conversations: [],
  conversation_members: [],
  messages: [],
  conversation_reads: [],
  invite_links: [],
  blocked_user_ids: []
});
low.read();
if (!low.data || !Array.isArray(low.data.users)) {
  low.data = { users: [], conversations: [], conversation_members: [], messages: [], conversation_reads: [], invite_links: [], blocked_user_ids: [] };
  low.write();
}
if (!Array.isArray(low.data.invite_links)) {
  low.data.invite_links = [];
  low.write();
}
if (!Array.isArray(low.data.blocked_user_ids)) {
  low.data.blocked_user_ids = [];
  low.write();
}
if (!Array.isArray(low.data.conversation_reads)) {
  low.data.conversation_reads = [];
  low.write();
}

function nextId(collection) {
  const arr = low.data[collection];
  if (!arr.length) return 1;
  return Math.max(...arr.map((x) => x.id)) + 1;
}

function now() {
  return new Date().toISOString();
}

function normalizePhone(input) {
  const digits = (input || '').replace(/\D/g, '');
  return digits.length >= 10 ? digits : '';
}

export const db = {
  findUserByEmail(email) {
    low.read();
    const e = (email || '').toLowerCase().trim();
    return e ? low.data.users.find((u) => u.email === e) : null;
  },
  findUserByPhone(phone) {
    low.read();
    const p = normalizePhone(phone);
    return p ? low.data.users.find((u) => u.phone && normalizePhone(u.phone) === p) : null;
  },
  findUserByEmailOrPhone(input) {
    const s = (input || '').trim();
    if (!s) return null;
    if (s.includes('@')) return db.findUserByEmail(s);
    return db.findUserByPhone(s);
  },
  findUserById(id) {
    low.read();
    return low.data.users.find((u) => u.id === Number(id));
  },
  addUser({ email, password_hash, name, phone, verification_code, verification_expires }) {
    low.read();
    const id = nextId('users');
    const row = {
      id,
      email: (email || '').toLowerCase().trim() || null,
      phone: phone ? normalizePhone(phone) || null : null,
      password_hash,
      name: (name || '').trim(),
      avatar_url: null,
      verified: false,
      verification_code: verification_code || null,
      verification_expires: verification_expires || null,
      created_at: now()
    };
    low.data.users.push(row);
    low.write();
    return row;
  },
  listUsersExcept(userId) {
    low.read();
    return low.data.users
      .filter((u) => u.id !== Number(userId))
      .map((u) => ({ id: u.id, email: u.email, phone: u.phone, name: u.name, avatar_url: u.avatar_url || null }));
  },

  findUsersByPhones(phoneNumbers, excludeUserId = null) {
    low.read();
    const normalizedSet = new Set();
    for (const raw of phoneNumbers || []) {
      const p = normalizePhone(raw);
      if (p) normalizedSet.add(p);
    }
    if (!normalizedSet.size) return [];
    const exclude = excludeUserId != null ? Number(excludeUserId) : null;
    return low.data.users
      .filter((u) => u.phone && normalizedSet.has(normalizePhone(u.phone)) && (!exclude || u.id !== exclude))
      .map((u) => ({ id: u.id, email: u.email, phone: u.phone, name: u.name, avatar_url: u.avatar_url || null }));
  },

  updateUserProfile(userId, { name, avatar_url }) {
    low.read();
    const u = low.data.users.find((x) => x.id === Number(userId));
    if (!u) return null;
    if (name !== undefined) u.name = (name || '').trim();
    if (avatar_url !== undefined) u.avatar_url = avatar_url || null;
    low.write();
    return u;
  },

  getOrCreateDirectConversation(userId1, userId2) {
    low.read();
    const id1 = Number(userId1);
    const id2 = Number(userId2);
    const conv = low.data.conversations.find(
      (c) =>
        c.type === 'direct' &&
        low.data.conversation_members.some((m) => m.conversation_id === c.id && m.user_id === id1) &&
        low.data.conversation_members.some((m) => m.conversation_id === c.id && m.user_id === id2)
    );
    if (conv) return { conversation: conv, created: false };
    const convId = nextId('conversations');
    low.data.conversations.push({
      id: convId,
      type: 'direct',
      name: null,
      created_at: now(),
      created_by: id1
    });
    low.data.conversation_members.push(
      { conversation_id: convId, user_id: id1, joined_at: now() },
      { conversation_id: convId, user_id: id2, joined_at: now() }
    );
    low.write();
    return {
      conversation: low.data.conversations.find((c) => c.id === convId),
      created: true
    };
  },
  createGroupConversation(creatorId, name, memberIds) {
    low.read();
    const convId = nextId('conversations');
    const allIds = [Number(creatorId), ...(memberIds || []).map(Number).filter(Boolean)];
    const unique = [...new Set(allIds)];
    low.data.conversations.push({
      id: convId,
      type: 'group',
      name: (name || '').trim() || 'مجموعة جديدة',
      created_at: now(),
      created_by: Number(creatorId)
    });
    unique.forEach((uid) => {
      low.data.conversation_members.push({
        conversation_id: convId,
        user_id: uid,
        joined_at: now()
      });
    });
    low.write();
    return low.data.conversations.find((c) => c.id === convId);
  },
  getConversationsForUser(userId) {
    low.read();
    const uid = Number(userId);
    const convIds = [...new Set(low.data.conversation_members.filter((m) => m.user_id === uid).map((m) => m.conversation_id))];
    return low.data.conversations
      .filter((c) => convIds.includes(c.id))
      .map((c) => ({
        ...c,
        members: low.data.conversation_members.filter((m) => m.conversation_id === c.id).map((m) => m.user_id)
      }))
      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  },
  getConversationByIdAndUser(convId, userId) {
    low.read();
    const c = low.data.conversations.find((x) => x.id === Number(convId));
    if (!c) return null;
    const isMember = low.data.conversation_members.some((m) => m.conversation_id === c.id && m.user_id === Number(userId));
    if (!isMember) return null;
    return {
      ...c,
      members: low.data.conversation_members.filter((m) => m.conversation_id === c.id).map((m) => m.user_id)
    };
  },
  getMemberIds(conversationId) {
    low.read();
    return low.data.conversation_members.filter((m) => m.conversation_id === Number(conversationId)).map((m) => m.user_id);
  },

  addMessage({ conversation_id, sender_id, type, content, file_name, reply_to_id, reply_to_snippet }) {
    low.read();
    const id = nextId('messages');
    const row = {
      id,
      conversation_id: Number(conversation_id),
      sender_id: Number(sender_id),
      type: type || 'text',
      content: content || '',
      file_name: file_name || null,
      reply_to_id: reply_to_id ? Number(reply_to_id) : null,
      reply_to_snippet: (reply_to_snippet && String(reply_to_snippet).slice(0, 100)) || null,
      created_at: now()
    };
    low.data.messages.push(row);
    low.write();
    return row;
  },
  getMessagesForConversation(conversationId, limit = 100, beforeId = null, currentUserId = null) {
    low.read();
    let list = low.data.messages.filter((m) => m.conversation_id === Number(conversationId));
    if (beforeId) list = list.filter((m) => m.id < beforeId);
    list = list.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)).slice(0, limit);
    list = list.reverse();
    const uid = currentUserId != null ? Number(currentUserId) : null;
    return list.map((m) => {
      const deletedForAll = !!m.deleted_for_everyone;
      const deletedForMe = Array.isArray(m.deleted_for_me) && uid != null && m.deleted_for_me.includes(uid);
      if (deletedForAll || deletedForMe) {
        return { ...m, content: '', file_name: null, type: 'text', deleted: true };
      }
      return m;
    });
  },

  deleteMessageForMe(messageId, conversationId, userId) {
    low.read();
    const msg = low.data.messages.find((m) => m.id === Number(messageId) && m.conversation_id === Number(conversationId));
    if (!msg) return false;
    if (!Array.isArray(msg.deleted_for_me)) msg.deleted_for_me = [];
    if (!msg.deleted_for_me.includes(Number(userId))) msg.deleted_for_me.push(Number(userId));
    low.write();
    return true;
  },

  deleteMessageForEveryone(messageId, conversationId, userId) {
    low.read();
    const msg = low.data.messages.find((m) => m.id === Number(messageId) && m.conversation_id === Number(conversationId));
    if (!msg || msg.sender_id !== Number(userId)) return false;
    msg.deleted_for_everyone = true;
    msg.content = '';
    msg.file_name = null;
    low.write();
    return true;
  },

  setConversationRead(conversationId, userId, lastMessageId) {
    low.read();
    const cid = Number(conversationId);
    const uid = Number(userId);
    const mid = lastMessageId != null ? Number(lastMessageId) : null;
    const arr = low.data.conversation_reads || [];
    const idx = arr.findIndex((r) => r.conversation_id === cid && r.user_id === uid);
    const row = { conversation_id: cid, user_id: uid, last_message_id: mid, last_read_at: now() };
    if (idx >= 0) arr[idx] = row;
    else arr.push(row);
    low.data.conversation_reads = arr;
    low.write();
    return row;
  },

  getConversationReads(conversationId) {
    low.read();
    const arr = low.data.conversation_reads || [];
    return arr.filter((r) => r.conversation_id === Number(conversationId));
  },

  createInviteLink(userId) {
    low.read();
    const token = 'i_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 10);
    const row = {
      token,
      created_by: Number(userId),
      created_at: now(),
      used_at: null
    };
    low.data.invite_links.push(row);
    low.write();
    return row;
  },
  consumeInviteLink(token) {
    low.read();
    const row = low.data.invite_links.find((l) => l.token === token && !l.used_at);
    if (!row) return false;
    row.used_at = now();
    low.write();
    return true;
  },
  getInviteLink(token) {
    low.read();
    return low.data.invite_links.find((l) => l.token === token);
  },

  blockUser(userId) {
    low.read();
    const id = Number(userId);
    if (!id || low.data.blocked_user_ids.includes(id)) return false;
    low.data.blocked_user_ids.push(id);
    low.write();
    return true;
  },
  setUserVerified(userId, verified) {
    low.read();
    const u = low.data.users.find((x) => x.id === Number(userId));
    if (!u) return false;
    u.verified = !!verified;
    u.verification_code = null;
    u.verification_expires = null;
    low.write();
    return true;
  },

  unblockUser(userId) {
    low.read();
    const id = Number(userId);
    low.data.blocked_user_ids = low.data.blocked_user_ids.filter((x) => x !== id);
    low.write();
    return true;
  },
  isUserBlocked(userId) {
    low.read();
    return low.data.blocked_user_ids.includes(Number(userId));
  },
  getBlockedUsers() {
    low.read();
    return low.data.blocked_user_ids.map((id) => db.findUserById(id)).filter(Boolean);
  }
};
