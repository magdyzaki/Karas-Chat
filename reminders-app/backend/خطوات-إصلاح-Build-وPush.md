# خطوات إصلاح الـ Build ودعم Push — ملف بملف

افتح **https://github.com/magdyzaki/reminders-backend** ونفّذ الخطوات بالترتيب.  
لو الملف موجود فعّل **Edit** ثم استبدل المحتوى. لو غير موجود فعّل **Create new file** واسم الملف كما مكتوب.

---

## 1) الملف: package.json (في الجذر)

**اسم الملف:** `package.json`

**المحتوى (نسخ كامل):**

```json
{
  "name": "reminders-backend",
  "version": "1.0.0",
  "description": "سيرفر التنبيهات - مزامنة بين الموبايل والكمبيوتر",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "dev": "node --watch index.js"
  },
  "engines": {
    "node": ">=18"
  },
  "dependencies": {
    "bcryptjs": "^2.4.3",
    "cors": "^2.8.5",
    "express": "^4.21.1",
    "jsonwebtoken": "^9.0.2",
    "lowdb": "^7.0.1",
    "web-push": "^3.6.7"
  }
}
```

ثم **Commit changes**.

---

## 2) الملف: middleware/auth.js

**اسم الملف:** `middleware/auth.js`

**المحتوى:**

```javascript
const jwt = require('jsonwebtoken');
const JWT_SECRET = process.env.JWT_SECRET || 'reminders-secret-change-in-production';

function auth(req, res, next) {
  const header = req.headers.authorization;
  if (!header || !header.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'يجب تسجيل الدخول' });
  }
  const token = header.slice(7);
  try {
    const payload = jwt.verify(token, JWT_SECRET);
    req.userId = payload.userId;
    next();
  } catch (e) {
    return res.status(401).json({ error: 'انتهت الجلسة، سجّل الدخول مرة أخرى' });
  }
}

module.exports = { auth, JWT_SECRET };
```

**Commit changes.**

---

## 3) الملف: routes/auth.js

**اسم الملف:** `routes/auth.js`

**المحتوى:**

```javascript
const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const db = require('../db');
const { JWT_SECRET } = require('../middleware/auth');

const router = express.Router();

router.post('/register', (req, res) => {
  const { email, password, name } = req.body || {};
  if (!email || !password) {
    return res.status(400).json({ error: 'البريد الإلكتروني وكلمة المرور مطلوبان' });
  }
  const emailNorm = email.trim().toLowerCase();
  if (db.findUserByEmail(emailNorm)) {
    return res.status(400).json({ error: 'البريد الإلكتروني مستخدم بالفعل' });
  }
  const hash = bcrypt.hashSync(password.trim(), 10);
  const row = db.addUser({
    email: emailNorm,
    password_hash: hash,
    name: (name || '').trim()
  });
  const token = jwt.sign({ userId: row.id }, JWT_SECRET, { expiresIn: '30d' });
  return res.json({
    user: { id: row.id, email: row.email, name: row.name },
    token
  });
});

router.post('/login', (req, res) => {
  const { email, password } = req.body || {};
  if (!email || !password) {
    return res.status(400).json({ error: 'البريد الإلكتروني وكلمة المرور مطلوبان' });
  }
  const row = db.findUserByEmail(email.trim().toLowerCase());
  if (!row || !bcrypt.compareSync(password.trim(), row.password_hash)) {
    return res.status(401).json({ error: 'البريد أو كلمة المرور غير صحيحة' });
  }
  const token = jwt.sign({ userId: row.id }, JWT_SECRET, { expiresIn: '30d' });
  res.json({ user: { id: row.id, email: row.email, name: row.name }, token });
});

module.exports = router;
```

**Commit changes.**

---

## 4) الملف: routes/reminders.js

**اسم الملف:** `routes/reminders.js`

**المحتوى:**

```javascript
const express = require('express');
const db = require('../db');
const { auth } = require('../middleware/auth');

const router = express.Router();
router.use(auth);

router.get('/', (req, res) => {
  const rows = db.getRemindersByUserId(req.userId);
  res.json({ reminders: rows });
});

router.post('/', (req, res) => {
  const { title, body, remind_at, repeat } = req.body || {};
  if (!title || !remind_at) {
    return res.status(400).json({ error: 'العنوان ووقت التذكير مطلوبان' });
  }
  const row = db.addReminder({
    user_id: req.userId,
    title: (title || '').trim(),
    body: (body || '').trim(),
    remind_at,
    repeat: (repeat || '') || null
  });
  res.status(201).json(row);
});

router.put('/:id', (req, res) => {
  const { id } = req.params;
  const { title, body, remind_at, repeat } = req.body || {};
  const existing = db.getReminderByIdAndUser(id, req.userId);
  if (!existing) return res.status(404).json({ error: 'التنبيه غير موجود' });
  const newTitle = title !== undefined ? String(title).trim() : existing.title;
  const newBody = body !== undefined ? String(body || '').trim() : existing.body;
  const newRemindAt = remind_at !== undefined ? remind_at : existing.remind_at;
  const newRepeat = repeat !== undefined ? (repeat || null) : existing.repeat;
  const row = db.updateReminder(id, req.userId, {
    title: newTitle,
    body: newBody,
    remind_at: newRemindAt,
    repeat: newRepeat
  });
  res.json(row);
});

router.delete('/:id', (req, res) => {
  const { id } = req.params;
  const deleted = db.deleteReminder(id, req.userId);
  if (deleted === 0) return res.status(404).json({ error: 'التنبيه غير موجود' });
  res.json({ deleted: true });
});

module.exports = router;
```

**Commit changes.**

---

## 5) الملف: routes/push.js

**اسم الملف:** `routes/push.js`

**المحتوى:**

```javascript
const express = require('express');
const db = require('../db');
const { auth } = require('../middleware/auth');

const router = express.Router();

router.get('/vapid-public', (req, res) => {
  const pub = process.env.VAPID_PUBLIC_KEY;
  if (!pub) return res.status(503).json({ error: 'VAPID غير مضبوط' });
  res.json({ publicKey: pub });
});

router.post('/subscribe', auth, (req, res) => {
  const subscription = req.body;
  if (!subscription || !subscription.endpoint || !subscription.keys) {
    return res.status(400).json({ error: 'صيغة الاشتراك غير صحيحة' });
  }
  db.addPushSubscription(req.userId, subscription);
  res.json({ ok: true });
});

module.exports = router;
```

**Commit changes.**

---

## 6) الملف: db.js (في الجذر)

**اسم الملف:** `db.js`

**المحتوى:**

```javascript
const path = require('path');
const os = require('os');
const { LowSync } = require('lowdb');
const { JSONFileSync } = require('lowdb/node');

const dbPath = process.env.DB_PATH || (process.env.PORT ? path.join(os.tmpdir(), 'reminders-db.json') : path.join(__dirname, 'db.json'));
const adapter = new JSONFileSync(dbPath);
const low = new LowSync(adapter, { users: [], reminders: [], push_subscriptions: [] });
low.read();
if (!Array.isArray(low.data.push_subscriptions)) {
  low.data.push_subscriptions = [];
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
    const row = { id, email: email.toLowerCase(), password_hash, name: name || '', created_at: now() };
    low.data.users.push(row);
    low.write();
    return row;
  },
  getRemindersByUserId(userId) {
    low.read();
    return low.data.reminders
      .filter((r) => r.user_id === Number(userId))
      .sort((a, b) => new Date(a.remind_at) - new Date(b.remind_at))
      .map(({ id, title, body, remind_at, repeat, created_at }) => ({ id, title, body, remind_at, repeat, created_at }));
  },
  addReminder({ user_id, title, body, remind_at, repeat }) {
    low.read();
    const id = nextId('reminders');
    const row = {
      id, user_id: Number(user_id), title: String(title).trim(), body: String(body || '').trim(),
      remind_at, repeat: repeat || null, created_at: now(), notified_at: null
    };
    low.data.reminders.push(row);
    low.write();
    return row;
  },
  getReminderByIdAndUser(id, userId) {
    low.read();
    return low.data.reminders.find((r) => r.id === Number(id) && r.user_id === Number(userId));
  },
  updateReminder(id, userId, { title, body, remind_at, repeat }) {
    low.read();
    const r = low.data.reminders.find((x) => x.id === Number(id) && x.user_id === Number(userId));
    if (!r) return null;
    if (title !== undefined) r.title = String(title).trim();
    if (body !== undefined) r.body = String(body || '').trim();
    if (remind_at !== undefined) r.remind_at = remind_at;
    if (repeat !== undefined) r.repeat = repeat || null;
    low.write();
    return r;
  },
  deleteReminder(id, userId) {
    low.read();
    const idx = low.data.reminders.findIndex((r) => r.id === Number(id) && r.user_id === Number(userId));
    if (idx === -1) return 0;
    low.data.reminders.splice(idx, 1);
    low.write();
    return 1;
  },
  addPushSubscription(userId, sub) {
    low.read();
    const endpoint = sub.endpoint;
    const existing = low.data.push_subscriptions.findIndex((s) => s.user_id === Number(userId) && s.endpoint === endpoint);
    const row = { user_id: Number(userId), endpoint: sub.endpoint, keys: sub.keys };
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
  }
};

module.exports = db;
```

**Commit changes.**

---

## 7) الملف: index.js (في الجذر)

**اسم الملف:** `index.js`

**المحتوى:**

```javascript
const express = require('express');
const cors = require('cors');
const webpush = require('web-push');
const authRoutes = require('./routes/auth');
const reminderRoutes = require('./routes/reminders');
const pushRoutes = require('./routes/push');
const db = require('./db');

const app = express();
const PORT = process.env.PORT || 4000;

let vapidKeys = { publicKey: process.env.VAPID_PUBLIC_KEY, privateKey: process.env.VAPID_PRIVATE_KEY };
if (!vapidKeys.publicKey || !vapidKeys.privateKey) {
  vapidKeys = webpush.generateVAPIDKeys();
  process.env.VAPID_PUBLIC_KEY = vapidKeys.publicKey;
  process.env.VAPID_PRIVATE_KEY = vapidKeys.privateKey;
  console.log('لتفعيل التنبيه مع الشاشة مطفية، ضع في Environment Variables:');
  console.log('VAPID_PUBLIC_KEY=', vapidKeys.publicKey);
  console.log('VAPID_PRIVATE_KEY=', vapidKeys.privateKey);
} else {
  webpush.setVapidDetails('mailto:reminders@local', vapidKeys.publicKey, vapidKeys.privateKey);
}

app.use(cors({ origin: true, credentials: true }));
app.use(express.json());

app.use('/api/auth', authRoutes);
app.use('/api/reminders', reminderRoutes);
app.use('/api/push', pushRoutes);

app.get('/api/health', (req, res) => {
  res.json({ ok: true });
});

const CHECK_PUSH_MS = 60 * 1000;
setInterval(() => {
  if (!vapidKeys.publicKey || !vapidKeys.privateKey) return;
  const due = db.getDueRemindersNotNotified();
  due.forEach((r) => {
    const subs = db.getPushSubscriptionsByUserId(r.user_id);
    if (subs.length === 0) return;
    const payload = { title: r.title, body: r.body || '' };
    webpush.setVapidDetails('mailto:reminders@local', vapidKeys.publicKey, vapidKeys.privateKey);
    subs.forEach((sub) => {
      const pushSub = { endpoint: sub.endpoint, keys: sub.keys };
      webpush.sendNotification(pushSub, JSON.stringify(payload)).catch((err) => {
        console.error('Push failed:', err.message);
      });
    });
    db.markReminderNotified(r.id);
  });
}, CHECK_PUSH_MS);

app.listen(PORT, '0.0.0.0', () => {
  console.log('سيرفر التنبيهات يعمل على المنفذ', PORT);
});
```

**Commit changes.**

---

## بعد الانتهاء

1. تأكد أن على GitHub عندك: **package.json**، **db.js**، **index.js**، **middleware/auth.js**، **routes/auth.js**، **routes/reminders.js**، **routes/push.js**.
2. في **Koyeb** اضغط **Redeploy** وانتظر حتى يظهر **Healthy**.
3. تأكد أن في Koyeb مضبوط متغيرا البيئة **VAPID_PUBLIC_KEY** و **VAPID_PRIVATE_KEY** (كما سبق).
