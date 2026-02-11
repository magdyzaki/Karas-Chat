const path = require('path');
const fs = require('fs');
const os = require('os');
const { LowSync } = require('lowdb');
const { JSONFileSync } = require('lowdb/node');

function getDbPath() {
  if (process.env.DB_PATH) return process.env.DB_PATH;
  if (process.env.PORT) return path.join(os.tmpdir(), 'reminders-db.json');
  return path.join(__dirname, 'db.json');
}

const dbPath = getDbPath();
const dbDir = path.dirname(dbPath);
try {
  if (!fs.existsSync(dbDir)) fs.mkdirSync(dbDir, { recursive: true });
} catch (_) {}

const adapter = new JSONFileSync(dbPath);
const low = new LowSync(adapter, { users: [], reminders: [], push_subscriptions: [], invite_links: [], blocked_user_ids: [] });
low.read();
if (!Array.isArray(low.data.push_subscriptions)) {
  low.data.push_subscriptions = [];
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
low.read();

function nextId(collection) {
  const arr = low.data[collection];
  if (!arr.length) return 1;
  return Math.max(...arr.map((x) => x.id)) + 1;
}

function now() {
  return new Date().toISOString();
}

const db = {
  findUserByEmail(email) {
    low.read();
    return low.data.users.find((u) => u.email === email.toLowerCase());
  },
  findUserById(id) {
    low.read();
    return low.data.users.find((u) => u.id === Number(id));
  },
  addUser({ email, password_hash, name }) {
    low.read();
    const id = nextId('users');
    const row = {
      id,
      email: email.toLowerCase(),
      password_hash,
      name: name || '',
      created_at: now()
    };
    low.data.users.push(row);
    low.write();
    return row;
  },
  getRemindersByUserId(userId) {
    low.read();
    return low.data.reminders
      .filter((r) => r.user_id === Number(userId))
      .sort((a, b) => new Date(a.remind_at) - new Date(b.remind_at))
      .map(({ id, title, body, remind_at, repeat, created_at, notes }) => ({
        id,
        title,
        body,
        remind_at,
        repeat,
        created_at,
        notes: notes || ''
      }));
  },
  addReminder({ user_id, title, body, remind_at, repeat, notes }) {
    low.read();
    const id = nextId('reminders');
    const row = {
      id,
      user_id: Number(user_id),
      title: String(title).trim(),
      body: String(body || '').trim(),
      remind_at,
      repeat: repeat || null,
      created_at: now(),
      notified_at: null,
      notes: String((notes !== undefined && notes !== null ? notes : '') || '').trim()
    };
    low.data.reminders.push(row);
    low.write();
    return row;
  },
  getReminderByIdAndUser(id, userId) {
    low.read();
    return low.data.reminders.find(
      (r) => r.id === Number(id) && r.user_id === Number(userId)
    );
  },
  updateReminder(id, userId, { title, body, remind_at, repeat, notes }) {
    low.read();
    const r = low.data.reminders.find(
      (x) => x.id === Number(id) && x.user_id === Number(userId)
    );
    if (!r) return null;
    if (title !== undefined) r.title = String(title).trim();
    if (body !== undefined) r.body = String(body || '').trim();
    if (remind_at !== undefined) r.remind_at = remind_at;
    if (repeat !== undefined) r.repeat = repeat || null;
    if (notes !== undefined) r.notes = String(notes || '').trim();
    low.write();
    return r;
  },
  deleteReminder(id, userId) {
    low.read();
    const idx = low.data.reminders.findIndex(
      (r) => r.id === Number(id) && r.user_id === Number(userId)
    );
    if (idx === -1) return 0;
    low.data.reminders.splice(idx, 1);
    low.write();
    return 1;
  },
  addPushSubscription(userId, sub) {
    low.read();
    const endpoint = sub.endpoint;
    const existing = low.data.push_subscriptions.findIndex(
      (s) => s.user_id === Number(userId) && s.endpoint === endpoint
    );
    const row = {
      user_id: Number(userId),
      endpoint: sub.endpoint,
      keys: sub.keys
    };
    if (existing >= 0) low.data.push_subscriptions[existing] = row;
    else low.data.push_subscriptions.push(row);
    low.write();
  },
  getPushSubscriptionsByUserId(userId) {
    low.read();
    return low.data.push_subscriptions.filter((s) => s.user_id === Number(userId));
  },
  getDueRemindersNotNotified() {
    low.read();
    const nowMs = Date.now();
    return low.data.reminders.filter((r) => {
      const at = new Date(r.remind_at).getTime();
      return at <= nowMs && (r.notified_at == null || r.notified_at === '');
    });
  },
  markReminderNotified(id) {
    low.read();
    const r = low.data.reminders.find((x) => x.id === Number(id));
    if (!r) return;
    r.notified_at = now();
    low.write();
  },
  getStats() {
    low.read();
    const due = this.getDueRemindersNotNotified();
    return {
      push_subscriptions_count: (low.data.push_subscriptions || []).length,
      reminders_count: (low.data.reminders || []).length,
      due_not_notified_count: due.length
    };
  },

  createInviteLink(userId) {
    low.read();
    const token = 'i_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 10);
    const row = { token, created_by: Number(userId), created_at: now(), used_at: null };
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
    return low.data.blocked_user_ids.map((id) => low.data.users.find((u) => u.id === id)).filter(Boolean);
  },
  getAllUsers() {
    low.read();
    return low.data.users.map((u) => ({ id: u.id, email: u.email, name: u.name }));
  }
};

module.exports = db;
