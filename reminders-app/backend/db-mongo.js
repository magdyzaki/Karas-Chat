/**
 * تخزين التنبيهات في MongoDB (عند ضبط MONGODB_URI).
 * نفس واجهة db لكن كل الدوال async.
 */
const { MongoClient } = require('mongodb');

const DB_NAME = 'reminders';
const COL_USERS = 'users';
const COL_REMINDERS = 'reminders';
const COL_PUSH = 'push_subscriptions';
const COL_INVITE_LINKS = 'invite_links';
const COL_BLOCKED = 'blocked_user_ids';

let client = null;
let db = null;

async function getDb() {
  if (db) return db;
  const uri = (process.env.MONGODB_URI || '').trim();
  if (!uri) throw new Error('MONGODB_URI مطلوب لاستخدام MongoDB');
  // خيارات لتجنب خطأ SSL (tlsv1 alert internal error) على بعض السيرفرات مثل Koyeb
  const options = {
    serverSelectionTimeoutMS: 20000,
    autoSelectFamily: false,
    family: 4
  };
  client = new MongoClient(uri, options);
  await client.connect();
  db = client.db(DB_NAME);
  return db;
}

function now() {
  return new Date().toISOString();
}

async function nextId(collectionName) {
  const d = await getDb();
  const col = d.collection(collectionName);
  const last = await col.find({}).sort({ id: -1 }).limit(1).toArray();
  return (last[0]?.id ?? 0) + 1;
}

const dbMongo = {
  async findUserByEmail(email) {
    const d = await getDb();
    return d.collection(COL_USERS).findOne({ email: (email || '').toLowerCase() });
  },

  async findUserById(id) {
    const d = await getDb();
    return d.collection(COL_USERS).findOne({ id: Number(id) });
  },

  async addUser({ email, password_hash, name }) {
    const d = await getDb();
    const id = await nextId(COL_USERS);
    const row = {
      id,
      email: (email || '').toLowerCase(),
      password_hash,
      name: (name || '').trim(),
      created_at: now()
    };
    await d.collection(COL_USERS).insertOne(row);
    return row;
  },

  async getRemindersByUserId(userId) {
    const d = await getDb();
    const rows = await d
      .collection(COL_REMINDERS)
      .find({ user_id: Number(userId) })
      .sort({ remind_at: 1 })
      .toArray();
    return rows.map(({ id, title, body, remind_at, repeat, created_at, notes }) => ({
      id,
      title,
      body,
      remind_at,
      repeat,
      created_at,
      notes: notes || ''
    }));
  },

  async addReminder({ user_id, title, body, remind_at, repeat, notes }) {
    const d = await getDb();
    const id = await nextId(COL_REMINDERS);
    const row = {
      id,
      user_id: Number(user_id),
      title: String(title || '').trim(),
      body: String(body || '').trim(),
remind_at: new Date(remind_at),
    repeat: repeat || null,
      created_at: now(),
      notified_at: null,
      notes: String((notes !== undefined && notes !== null ? notes : '') || '').trim()
    };
    await d.collection(COL_REMINDERS).insertOne(row);
    return row;
  },

  async getReminderByIdAndUser(id, userId) {
    const d = await getDb();
    return d.collection(COL_REMINDERS).findOne({
      id: Number(id),
      user_id: Number(userId)
    });
  },

  async updateReminder(id, userId, { title, body, remind_at, repeat, notes }) {
    const d = await getDb();
    const r = await d.collection(COL_REMINDERS).findOne({
      id: Number(id),
      user_id: Number(userId)
    });
    if (!r) return null;
    const update = {};
    if (title !== undefined) update.title = String(title).trim();
    if (body !== undefined) update.body = String(body || '').trim();
    if (remind_at !== undefined) update.remind_at = new Date(remind_at);
    if (repeat !== undefined) update.repeat = repeat || null;
    if (notes !== undefined) update.notes = String(notes || '').trim();
    await d.collection(COL_REMINDERS).updateOne(
      { id: Number(id), user_id: Number(userId) },
      { $set: update }
    );
    return d.collection(COL_REMINDERS).findOne({ id: Number(id), user_id: Number(userId) });
  },

  async deleteReminder(id, userId) {
    const d = await getDb();
    const result = await d.collection(COL_REMINDERS).deleteOne({
      id: Number(id),
      user_id: Number(userId)
    });
    return result.deletedCount;
  },

  async addPushSubscription(userId, sub) {
    const d = await getDb();
    const endpoint = sub.endpoint;
    const existing = await d.collection(COL_PUSH).findOne({
      user_id: Number(userId),
      endpoint
    });
    const row = {
      user_id: Number(userId),
      endpoint: sub.endpoint,
      keys: sub.keys
    };
    if (existing) {
      await d.collection(COL_PUSH).updateOne(
        { user_id: Number(userId), endpoint },
        { $set: row }
      );
    } else {
      await d.collection(COL_PUSH).insertOne(row);
    }
  },

  async getPushSubscriptionsByUserId(userId) {
    const d = await getDb();
    return d.collection(COL_PUSH).find({ user_id: Number(userId) }).toArray();
  },

  async getDueRemindersNotNotified() {
    const d = await getDb();
    const nowMs = Date.now();
    return d
      .collection(COL_REMINDERS)
      .find({
        remind_at: { $lte: new Date(nowMs) },
        $or: [{ notified_at: null }, { notified_at: '' }]
      })
      .toArray();
  },

  async markReminderNotified(id) {
    const d = await getDb();
    await d.collection(COL_REMINDERS).updateOne(
      { id: Number(id) },
      { $set: { notified_at: now() } }
    );
  },

  async getStats() {
    const d = await getDb();
    const remindersCount = await d.collection(COL_REMINDERS).countDocuments();
    const pushCount = await d.collection(COL_PUSH).countDocuments();
    const due = await this.getDueRemindersNotNotified();
    return {
      push_subscriptions_count: pushCount,
      reminders_count: remindersCount,
      due_not_notified_count: due.length
    };
  },

  async createInviteLink(userId) {
    const d = await getDb();
    const token = 'i_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 10);
    const row = { token, created_by: Number(userId), created_at: now(), used_at: null };
    await d.collection(COL_INVITE_LINKS).insertOne(row);
    return row;
  },
  async consumeInviteLink(token) {
    const d = await getDb();
    const row = await d.collection(COL_INVITE_LINKS).findOne({ token, used_at: null });
    if (!row) return false;
    await d.collection(COL_INVITE_LINKS).updateOne({ token }, { $set: { used_at: now() } });
    return true;
  },
  async getInviteLink(token) {
    const d = await getDb();
    return d.collection(COL_INVITE_LINKS).findOne({ token });
  },
  async blockUser(userId) {
    const d = await getDb();
    const id = Number(userId);
    if (!id) return false;
    const existing = await d.collection(COL_BLOCKED).findOne({ user_id: id });
    if (existing) return false;
    await d.collection(COL_BLOCKED).insertOne({ user_id: id });
    return true;
  },
  async unblockUser(userId) {
    const d = await getDb();
    await d.collection(COL_BLOCKED).deleteMany({ user_id: Number(userId) });
    return true;
  },
  async isUserBlocked(userId) {
    const d = await getDb();
    const doc = await d.collection(COL_BLOCKED).findOne({ user_id: Number(userId) });
    return !!doc;
  },
  async getBlockedUsers() {
    const d = await getDb();
    const blocked = await d.collection(COL_BLOCKED).find({}).toArray();
    const ids = blocked.map((b) => b.user_id);
    const users = await d.collection(COL_USERS).find({ id: { $in: ids } }).toArray();
    return users.map((u) => ({ id: u.id, email: u.email, name: u.name }));
  },
  async getAllUsers() {
    const d = await getDb();
    const users = await d.collection(COL_USERS).find({}).project({ id: 1, email: 1, name: 1 }).toArray();
    return users.map((u) => ({ id: u.id, email: u.email, name: u.name }));
  }
};

module.exports = dbMongo;
