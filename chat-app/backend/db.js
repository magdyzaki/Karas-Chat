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
  messages: []
});
low.read();
if (!low.data || !Array.isArray(low.data.users)) {
  low.data = { users: [], conversations: [], conversation_members: [], messages: [] };
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
  // المستخدمون
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
  addUser({ email, password_hash, name, phone }) {
    low.read();
    const id = nextId('users');
    const row = {
      id,
      email: (email || '').toLowerCase().trim() || null,
      phone: phone ? normalizePhone(phone) || null : null,
      password_hash,
      name: (name || '').trim(),
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
      .map(({ id, email, phone, name }) => ({ id, email, phone, name }));
  },

  // المحادثات
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

  // الرسائل
  addMessage({ conversation_id, sender_id, type, content, file_name }) {
    low.read();
    const id = nextId('messages');
    const row = {
      id,
      conversation_id: Number(conversation_id),
      sender_id: Number(sender_id),
      type: type || 'text',
      content: content || '',
      file_name: file_name || null,
      created_at: now()
    };
    low.data.messages.push(row);
    low.write();
    return row;
  },
  getMessagesForConversation(conversationId, limit = 100, beforeId = null) {
    low.read();
    let list = low.data.messages.filter((m) => m.conversation_id === Number(conversationId));
    if (beforeId) list = list.filter((m) => m.id < beforeId);
    list = list.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)).slice(0, limit);
    return list.reverse();
  }
};
