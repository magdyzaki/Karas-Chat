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
  blocked_user_ids: []
});
low.read();
if (!low.data || !Array.isArray(low.data.users)) {
  low.data = {
    users: [],
    conversations: [],
    conversation_members: [],
    messages: [],
    conversation_reads: [],
    blocked_user_ids: []
  };
  low.write();
}

function nextId(coll) {
  const arr = low.data[coll];
  if (!arr?.length) return 1;
  return Math.max(...arr.map((x) => x.id)) + 1;
}
function now() {
  return new Date().toISOString();
}

/** توحيد أرقام مصر: 01X و 20X = نفس الرقم */
function toCanonicalPhone(input) {
  const d = String(input || '').replace(/\D/g, '');
  if (d.length < 10) return '';
  if (d.startsWith('01') && d.length === 11) return '2' + d;
  if (d.startsWith('20') && d.length >= 11) return d.slice(0, 12);
  return d;
}
function normalizePhone(input) {
  const d = (input || '').replace(/\D/g, '');
  return d.length >= 10 ? d : '';
}

export const db = {
  findUserByEmail(email) {
    low.read();
    const e = (email || '').toLowerCase().trim();
    return e ? low.data.users.find((u) => u.email === e) : null;
  },
  findUserByPhone(phone) {
    low.read();
    const p = toCanonicalPhone(phone);
    return p ? low.data.users.find((u) => u.phone && toCanonicalPhone(u.phone) === p) : null;
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
      verified: false,
      verification_code: verification_code || null,
      verification_expires: verification_expires || null,
      created_at: now()
    };
    low.data.users.push(row);
    low.write();
    return row;
  },
  setUserVerified(userId, v) {
    low.read();
    const u = low.data.users.find((x) => x.id === Number(userId));
    if (!u) return false;
    u.verified = !!v;
    u.verification_code = null;
    u.verification_expires = null;
    low.write();
    return true;
  },
  listUsersExcept(userId) {
    low.read();
    return low.data.users
      .filter((u) => u.id !== Number(userId))
      .map((u) => ({ id: u.id, email: u.email, phone: u.phone, name: u.name }));
  },
  findUsersByPhones(phones, excludeUserId = null) {
    low.read();
    const set = new Set();
    for (const raw of phones || []) {
      const p = toCanonicalPhone(raw);
      if (p) set.add(p);
    }
    if (!set.size) return [];
    const ex = excludeUserId != null ? Number(excludeUserId) : null;
    return low.data.users
      .filter((u) => u.phone && set.has(toCanonicalPhone(u.phone)) && (!ex || u.id !== ex))
      .map((u) => ({ id: u.id, email: u.email, phone: u.phone, name: u.name }));
  },
  isUserBlocked(userId) {
    low.read();
    return (low.data.blocked_user_ids || []).includes(Number(userId));
  },
  setUserLastSeen(userId) {
    low.read();
    const u = low.data.users.find((x) => x.id === Number(userId));
    if (u) { u.last_seen_at = now(); low.write(); }
  },
  getOrCreateDirectConversation(userId1, userId2) {
    low.read();
    const id1 = Number(userId1), id2 = Number(userId2);
    const conv = low.data.conversations.find((c) =>
      c.type === 'direct' &&
      low.data.conversation_members.some((m) => m.conversation_id === c.id && m.user_id === id1) &&
      low.data.conversation_members.some((m) => m.conversation_id === c.id && m.user_id === id2)
    );
    if (conv) return { conversation: conv };
    const convId = nextId('conversations');
    low.data.conversations.push({ id: convId, type: 'direct', name: null, created_at: now(), created_by: id1 });
    low.data.conversation_members.push(
      { conversation_id: convId, user_id: id1, joined_at: now() },
      { conversation_id: convId, user_id: id2, joined_at: now() }
    );
    low.write();
    return { conversation: low.data.conversations.find((c) => c.id === convId) };
  },
  createGroupConversation(creatorId, name, memberIds) {
    low.read();
    const convId = nextId('conversations');
    const all = [Number(creatorId), ...(memberIds || []).map(Number).filter(Boolean)];
    const unique = [...new Set(all)];
    low.data.conversations.push({
      id: convId, type: 'group', name: (name || '').trim() || 'مجموعة', created_at: now(), created_by: Number(creatorId)
    });
    unique.forEach((uid) => low.data.conversation_members.push({ conversation_id: convId, user_id: uid, joined_at: now() }));
    low.write();
    return low.data.conversations.find((c) => c.id === convId);
  },
  getConversationsForUser(userId) {
    low.read();
    const uid = Number(userId);
    const ids = [...new Set(low.data.conversation_members.filter((m) => m.user_id === uid).map((m) => m.conversation_id))];
    return low.data.conversations
      .filter((c) => ids.includes(c.id))
      .map((c) => ({ ...c, members: low.data.conversation_members.filter((m) => m.conversation_id === c.id).map((m) => m.user_id) }))
      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  },
  getConversationByIdAndUser(convId, userId) {
    low.read();
    const c = low.data.conversations.find((x) => x.id === Number(convId));
    if (!c) return null;
    const inConv = low.data.conversation_members.some((m) => m.conversation_id === c.id && m.user_id === Number(userId));
    if (!inConv) return null;
    return { ...c, members: low.data.conversation_members.filter((m) => m.conversation_id === c.id).map((m) => m.user_id) };
  },
  getMemberIds(convId) {
    low.read();
    return low.data.conversation_members.filter((m) => m.conversation_id === Number(convId)).map((m) => m.user_id);
  },
  addMessage({ conversation_id, sender_id, type, content, file_name }) {
    low.read();
    const id = nextId('messages');
    const row = { id, conversation_id: Number(conversation_id), sender_id: Number(sender_id), type: type || 'text', content: content || '', file_name: file_name || null, created_at: now() };
    low.data.messages.push(row);
    low.write();
    return row;
  },
  getMessagesForConversation(convId, limit = 100, beforeId = null) {
    low.read();
    let list = low.data.messages.filter((m) => m.conversation_id === Number(convId));
    if (beforeId) list = list.filter((m) => m.id < beforeId);
    list = list.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)).slice(0, limit).reverse();
    return list;
  }
};
