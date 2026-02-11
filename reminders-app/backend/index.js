const express = require('express');
const cors = require('cors');
const webpush = require('web-push');
const authRoutes = require('./routes/auth');
const reminderRoutes = require('./routes/reminders');
const pushRoutes = require('./routes/push');
const inviteRoutes = require('./routes/invite');
const adminRoutes = require('./routes/admin');
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
app.use('/api', inviteRoutes);
app.use('/api/admin', adminRoutes);

app.get('/api/health', (req, res) => {
  res.json({ ok: true });
});

async function runPushCheck() {
  if (!vapidKeys.publicKey || !vapidKeys.privateKey) return;
  const due = await db.getDueRemindersNotNotified();
  for (const r of due) {
    const subs = await db.getPushSubscriptionsByUserId(r.user_id);
    if (subs.length === 0) continue;
    const payload = { id: r.id, title: r.title, body: r.body || '' };
    webpush.setVapidDetails('mailto:reminders@local', vapidKeys.publicKey, vapidKeys.privateKey);
    for (const sub of subs) {
      const keys = sub.keys || {};
      const pushSub = {
        endpoint: sub.endpoint,
        keys: {
          p256dh: keys.p256dh || keys.P256dh || '',
          auth: keys.auth || keys.Auth || ''
        }
      };
      if (!pushSub.keys.p256dh || !pushSub.keys.auth) continue;
      try {
        await webpush.sendNotification(pushSub, JSON.stringify(payload));
      } catch (err) {
        console.error('Push failed:', err.message);
      }
    }
    await db.markReminderNotified(r.id);
  }
}

runPushCheck().catch((err) => console.error('runPushCheck error:', err.message));
const CHECK_PUSH_MS = 60 * 1000;
setInterval(() => runPushCheck().catch((e) => console.error(e.message)), CHECK_PUSH_MS);

app.get('/api/push/check', (req, res) => {
  const secret = process.env.CRON_SECRET;
  if (!secret) return res.status(503).json({ error: 'CRON_SECRET غير مضبوط في Koyeb' });
  if (req.query.secret !== secret) return res.status(401).json({ error: 'غير مصرح' });
  runPushCheck().then(() => res.json({ ok: true, message: 'تم فحص التنبيهات' })).catch((e) => res.status(500).json({ error: e.message }));
});

app.get('/api/push/status', async (req, res) => {
  const secret = process.env.CRON_SECRET;
  if (!secret || req.query.secret !== secret) return res.status(401).json({ error: 'غير مصرح' });
  try {
    const stats = await db.getStats();
    res.json({
      ok: true,
      push_subscriptions_count: stats.push_subscriptions_count,
      reminders_count: stats.reminders_count,
      due_not_notified_count: stats.due_not_notified_count,
      vapid_set: !!(vapidKeys.publicKey && vapidKeys.privateKey)
    });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.listen(PORT, '0.0.0.0', () => {
  console.log('سيرفر التنبيهات يعمل على المنفذ', PORT);
});
