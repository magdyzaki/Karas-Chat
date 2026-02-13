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
  low.data = {
    users: [], conversations: [], conversation_members: [], messages: [], conversation_reads: [],
    invite_links: [], blocked_user_ids: [], user_conversation_prefs: [], message_reactions: [],
    poll_votes: [], stories: [], broadcast_lists: [], user_public_keys: []
  };
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
if (!Array.isArray(low.data.push_subscriptions)) {
  low.data.push_subscriptions = [];
  low.write();
}
if (!Array.isArray(low.data.conversation_reads)) {
  low.data.conversation_reads = [];
  low.write();
}
if (!Array.isArray(low.data.user_conversation_prefs)) {
  low.data.user_conversation_prefs = [];
  low.write();
}
// disappearing_after: null|86400|604800|2592000 (24h, 7d, 90d)
if (!Array.isArray(low.data.message_reactions)) {
  low.data.message_reactions = [];
  low.write();
}
if (!Array.isArray(low.data.stories)) {
  low.data.stories = [];
  low.write();
}
if (!Array.isArray(low.data.poll_votes)) {
  low.data.poll_votes = [];
  low.write();
}
if (!Array.isArray(low.data.broadcast_lists)) {
  low.data.broadcast_lists = [];
  low.write();
}
if (!Array.isArray(low.data.user_public_keys)) {
  low.data.user_public_keys = [];
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
      created_at: now(),
      last_seen_at: null
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
  getUnverifiedUsers() {
    low.read();
    return low.data.users
      .filter((u) => u.verified === false)
      .map((u) => ({ id: u.id, email: u.email, phone: u.phone, name: u.name, created_at: u.created_at }));
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
  setResetCode(userId, code, expires) {
    low.read();
    const u = low.data.users.find((x) => x.id === Number(userId));
    if (!u) return false;
    u.reset_code = code || null;
    u.reset_expires = expires || null;
    low.write();
    return true;
  },
  updateUserPassword(userId, password_hash) {
    low.read();
    const u = low.data.users.find((x) => x.id === Number(userId));
    if (!u) return false;
    u.password_hash = password_hash;
    u.reset_code = null;
    u.reset_expires = null;
    low.write();
    return true;
  },
  blockUser(userId) {
    low.read();
    const id = Number(userId);
    if (!id || low.data.blocked_user_ids.includes(id)) return false;
    low.data.blocked_user_ids.push(id);
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
  resetAll() {
    low.data = {
      users: [],
      conversations: [],
      conversation_members: [],
      messages: [],
      conversation_reads: [],
      invite_links: [],
      blocked_user_ids: [],
      push_subscriptions: low.data.push_subscriptions || [],
      user_conversation_prefs: [],
      message_reactions: [],
      poll_votes: [],
      stories: [],
      broadcast_lists: [],
      user_public_keys: []
    };
    low.write();
    return true;
  },
  getBlockedUsers() {
    low.read();
    return low.data.blocked_user_ids.map((id) => db.findUserById(id)).filter(Boolean);
  },
  setUserLastSeen(userId) {
    low.read();
    const u = low.data.users.find((x) => x.id === Number(userId));
    if (u) { u.last_seen_at = now(); low.write(); }
  },
  setConversationMuted(userId, conversationId, muted) {
    low.read();
    const arr = low.data.user_conversation_prefs || [];
    const idx = arr.findIndex((p) => p.user_id === Number(userId) && p.conversation_id === Number(conversationId));
    const existing = idx >= 0 ? arr[idx] : {};
    const row = { ...existing, user_id: Number(userId), conversation_id: Number(conversationId), muted: !!muted, archived: existing.archived || false, disappearing_after: existing.disappearing_after ?? null };
    if (idx >= 0) arr[idx] = row;
    else arr.push(row);
    low.data.user_conversation_prefs = arr;
    low.write();
    return true;
  },
  setConversationArchived(userId, conversationId, archived) {
    low.read();
    const arr = low.data.user_conversation_prefs || [];
    const idx = arr.findIndex((p) => p.user_id === Number(userId) && p.conversation_id === Number(conversationId));
    const existing = idx >= 0 ? arr[idx] : {};
    const row = { ...existing, user_id: Number(userId), conversation_id: Number(conversationId), archived: !!archived, muted: existing.muted || false, disappearing_after: existing.disappearing_after ?? null };
    if (idx >= 0) arr[idx] = row;
    else arr.push(row);
    low.data.user_conversation_prefs = arr;
    low.write();
    return true;
  },
  isConversationMuted(userId, conversationId) {
    low.read();
    const p = (low.data.user_conversation_prefs || []).find((x) => x.user_id === Number(userId) && x.conversation_id === Number(conversationId));
    return !!p?.muted;
  },
  getArchivedConversationIds(userId) {
    low.read();
    return (low.data.user_conversation_prefs || []).filter((p) => p.user_id === Number(userId) && p.archived).map((p) => p.conversation_id);
  },
  getConversationPref(userId, conversationId) {
    low.read();
    const p = (low.data.user_conversation_prefs || []).find((x) => x.user_id === Number(userId) && x.conversation_id === Number(conversationId));
    return p || { muted: false, archived: false, disappearing_after: null };
  },
  setConversationDisappearing(userId, conversationId, seconds) {
    low.read();
    const arr = low.data.user_conversation_prefs || [];
    const idx = arr.findIndex((p) => p.user_id === Number(userId) && p.conversation_id === Number(conversationId));
    const row = { user_id: Number(userId), conversation_id: Number(conversationId), archived: idx >= 0 ? arr[idx].archived : false, muted: idx >= 0 ? arr[idx].muted : false, disappearing_after: seconds || null };
    if (idx >= 0) arr[idx] = { ...arr[idx], disappearing_after: row.disappearing_after };
    else arr.push(row);
    low.data.user_conversation_prefs = arr;
    low.write();
    return true;
  },
  addMessageReaction(messageId, userId, emoji) {
    low.read();
    const mid = Number(messageId);
    const uid = Number(userId);
    const arr = low.data.message_reactions || [];
    const idx = arr.findIndex((r) => r.message_id === mid && r.user_id === uid);
    if (idx >= 0) arr[idx].emoji = emoji;
    else arr.push({ message_id: mid, user_id: uid, emoji: String(emoji).slice(0, 10) });
    low.data.message_reactions = arr;
    low.write();
    return true;
  },
  removeMessageReaction(messageId, userId) {
    low.read();
    const arr = (low.data.message_reactions || []).filter((r) => !(r.message_id === Number(messageId) && r.user_id === Number(userId)));
    low.data.message_reactions = arr;
    low.write();
    return true;
  },
  isMessageInConversation(messageId, conversationId) {
    low.read();
    return low.data.messages.some((m) => m.id === Number(messageId) && m.conversation_id === Number(conversationId));
  },
  getMessageReactions(conversationId) {
    low.read();
    const msgIds = new Set(low.data.messages.filter((m) => m.conversation_id === Number(conversationId)).map((m) => m.id));
    return (low.data.message_reactions || []).filter((r) => msgIds.has(r.message_id));
  },
  addStory({ user_id, type, content, file_name }) {
    low.read();
    const id = nextId('stories');
    const row = { id, user_id: Number(user_id), type: type || 'text', content: content || '', file_name: file_name || null, created_at: now() };
    low.data.stories.push(row);
    low.write();
    return row;
  },
  getStoriesForFeed(currentUserId) {
    low.read();
    const STORY_MAX_AGE_MS = 24 * 60 * 60 * 1000;
    const cutoff = new Date(Date.now() - STORY_MAX_AGE_MS).toISOString();
    const all = (low.data.stories || []).filter((s) => s.created_at >= cutoff);
    const byUser = {};
    for (const s of all) {
      if (!byUser[s.user_id]) byUser[s.user_id] = [];
      byUser[s.user_id].push(s);
    }
    for (const uid of Object.keys(byUser)) {
      byUser[uid].sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
    }
    return byUser;
  },
  getStoriesByUser(userId) {
    low.read();
    const STORY_MAX_AGE_MS = 24 * 60 * 60 * 1000;
    const cutoff = new Date(Date.now() - STORY_MAX_AGE_MS).toISOString();
    return (low.data.stories || []).filter((s) => s.user_id === Number(userId) && s.created_at >= cutoff).sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
  },
  addPollVote(messageId, conversationId, userId, optionIndex) {
    low.read();
    const mid = Number(messageId);
    const cid = Number(conversationId);
    const uid = Number(userId);
    const msg = low.data.messages.find((m) => m.id === mid && m.conversation_id === cid);
    if (!msg || msg.type !== 'poll') return false;
    let poll;
    try { poll = JSON.parse(msg.content || '{}'); } catch (_) { return false; }
    const opts = poll.options || [];
    if (optionIndex < 0 || optionIndex >= opts.length) return false;
    const arr = low.data.poll_votes || [];
    const idx = arr.findIndex((v) => v.message_id === mid && v.user_id === uid);
    const row = { message_id: mid, conversation_id: cid, user_id: uid, option_index: optionIndex };
    if (idx >= 0) arr[idx] = row;
    else arr.push(row);
    low.data.poll_votes = arr;
    low.write();
    return true;
  },
  getPollVotes(conversationId) {
    low.read();
    return (low.data.poll_votes || []).filter((v) => v.conversation_id === Number(conversationId));
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
  addMessage({ conversation_id, sender_id, type, content, file_name, reply_to_id, reply_to_snippet, encrypted, iv }) {
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
      encrypted: !!encrypted,
      iv: iv || null,
      created_at: now()
    };
    low.data.messages.push(row);
    low.write();
    return row;
  },
  getMessagesForConversation(conversationId, limit = 100, beforeId = null, currentUserId = null) {
    low.read();
    let list = low.data.messages.filter((m) => m.conversation_id === Number(conversationId));
    const prefs = currentUserId != null ? db.getConversationPref(currentUserId, conversationId) : {};
    const disappearingSec = prefs.disappearing_after;
    if (disappearingSec) {
      const cutoff = new Date(Date.now() - disappearingSec * 1000).toISOString();
      list = list.filter((m) => m.created_at >= cutoff);
    }
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
  leaveConversation(conversationId, userId) {
    low.read();
    const cid = Number(conversationId);
    const uid = Number(userId);
    const conv = low.data.conversations.find((c) => c.id === cid);
    if (!conv) return false;
    if (conv.type === 'direct') return false;
    const idx = low.data.conversation_members.findIndex((m) => m.conversation_id === cid && m.user_id === uid);
    if (idx < 0) return false;
    low.data.conversation_members.splice(idx, 1);
    low.write();
    return true;
  },
  deleteConversation(conversationId, userId) {
    low.read();
    const cid = Number(conversationId);
    const uid = Number(userId);
    const conv = low.data.conversations.find((c) => c.id === cid);
    if (!conv) return false;
    if (Number(conv.created_by) !== uid) return false;
    low.data.conversations = low.data.conversations.filter((c) => c.id !== cid);
    low.data.conversation_members = low.data.conversation_members.filter((m) => m.conversation_id !== cid);
    low.data.messages = low.data.messages.filter((m) => m.conversation_id !== cid);
    low.data.conversation_reads = (low.data.conversation_reads || []).filter((r) => r.conversation_id !== cid);
    low.write();
    return true;
  },
  addMemberToGroup(conversationId, actorUserId, newMemberId) {
    low.read();
    const cid = Number(conversationId);
    const conv = low.data.conversations.find((c) => c.id === cid);
    if (!conv || conv.type !== 'group') return false;
    if (Number(conv.created_by) !== Number(actorUserId)) return false;
    const newId = Number(newMemberId);
    const exists = low.data.conversation_members.some((m) => m.conversation_id === cid && m.user_id === newId);
    if (exists) return false;
    const user = db.findUserById(newId);
    if (!user) return false;
    low.data.conversation_members.push({ conversation_id: cid, user_id: newId, joined_at: now() });
    low.write();
    return true;
  },
  removeMemberFromGroup(conversationId, actorUserId, targetUserId) {
    low.read();
    const cid = Number(conversationId);
    const conv = low.data.conversations.find((c) => c.id === cid);
    if (!conv || conv.type !== 'group') return false;
    if (Number(conv.created_by) !== Number(actorUserId)) return false;
    const targetId = Number(targetUserId);
    if (targetId === Number(actorUserId)) return false;
    const idx = low.data.conversation_members.findIndex((m) => m.conversation_id === cid && m.user_id === targetId);
    if (idx < 0) return false;
    low.data.conversation_members.splice(idx, 1);
    low.write();
    return true;
  },
  savePushSubscription(userId, subscription) {
    low.read();
    const uid = Number(userId);
    const sub = subscription && typeof subscription === 'object' ? subscription : null;
    if (!sub || !sub.endpoint) return false;
    const list = low.data.push_subscriptions || [];
    const existing = list.findIndex((s) => s.user_id === uid && s.endpoint === sub.endpoint);
    const row = { user_id: uid, endpoint: sub.endpoint, keys: sub.keys || {}, updated_at: now() };
    if (existing >= 0) list[existing] = row;
    else list.push(row);
    low.data.push_subscriptions = list;
    low.write();
    return true;
  },
  getPushSubscriptionsForUser(userId) {
    low.read();
    const list = low.data.push_subscriptions || [];
    return list.filter((s) => Number(s.user_id) === Number(userId));
  },
  removePushSubscription(userId, endpoint) {
    low.read();
    low.data.push_subscriptions = (low.data.push_subscriptions || []).filter(
      (s) => !(Number(s.user_id) === Number(userId) && s.endpoint === endpoint)
    );
    low.write();
  },
  getBroadcastLists(userId) {
    low.read();
    return (low.data.broadcast_lists || []).filter((b) => b.user_id === Number(userId));
  },
  getBroadcastListById(id, userId) {
    low.read();
    const b = (low.data.broadcast_lists || []).find((x) => x.id === Number(id) && x.user_id === Number(userId));
    return b || null;
  },
  createBroadcastList(userId, name, recipientIds) {
    low.read();
    const id = nextId('broadcast_lists');
    const list = { id, user_id: Number(userId), name: (name || '').trim() || 'قائمة بث', recipient_ids: (recipientIds || []).map(Number).filter(Boolean), created_at: now() };
    low.data.broadcast_lists.push(list);
    low.write();
    return list;
  },
  updateBroadcastList(id, userId, name, recipientIds) {
    low.read();
    const b = low.data.broadcast_lists.find((x) => x.id === Number(id) && x.user_id === Number(userId));
    if (!b) return null;
    if (name !== undefined) b.name = (name || '').trim() || b.name;
    if (recipientIds !== undefined) b.recipient_ids = (recipientIds || []).map(Number).filter(Boolean);
    low.write();
    return b;
  },
  deleteBroadcastList(id, userId) {
    low.read();
    const idx = low.data.broadcast_lists.findIndex((x) => x.id === Number(id) && x.user_id === Number(userId));
    if (idx < 0) return false;
    low.data.broadcast_lists.splice(idx, 1);
    low.write();
    return true;
  },
  setUserPublicKey(userId, publicKey) {
    low.read();
    const uid = Number(userId);
    const arr = low.data.user_public_keys || [];
    const idx = arr.findIndex((r) => r.user_id === uid);
    const row = { user_id: uid, public_key: String(publicKey || '').slice(0, 5000), created_at: now() };
    if (idx >= 0) arr[idx] = row;
    else arr.push(row);
    low.data.user_public_keys = arr;
    low.write();
    return row;
  },
  getUserPublicKey(userId) {
    low.read();
    const r = (low.data.user_public_keys || []).find((x) => x.user_id === Number(userId));
    return r?.public_key || null;
  }
};
