const express = require('express');
const cors = require('cors');
const webpush = require('web-push');
const authRoutes = require('./routes/auth');
const reminderRoutes = require('./routes/reminders');
const pushRoutes = require('./routes/push');
const db = require('./db');

const app = express();
const PORT = process.env.PORT || 4000;

// إعداد مفاتيح VAPID لإشعارات الدفع (حتى تعمل مع الشاشة مطفية)
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

// التحقق من التنبيهات المستحقة وإرسال Push
function runPushCheck() {
  if (!vapidKeys.publicKey || !vapidKeys.privateKey) return;
  const due = db.getDueRemindersNotNotified();
  due.forEach((r) => {
    const subs = db.getPushSubscriptionsByUserId(r.user_id);
    if (subs.length === 0) return;
    const payload = { id: r.id, title: r.title, body: r.body || '' };
    webpush.setVapidDetails('mailto:reminders@local', vapidKeys.publicKey, vapidKeys.privateKey);
    subs.forEach((sub) => {
      const keys = sub.keys || {};
      const pushSub = {
        endpoint: sub.endpoint,
        keys: {
          p256dh: keys.p256dh || keys.P256dh || '',
          auth: keys.auth || keys.Auth || ''
        }
      };
      if (!pushSub.keys.p256dh || !pushSub.keys.auth) return;
      webpush.sendNotification(pushSub, JSON.stringify(payload)).catch((err) => {
        console.error('Push failed:', err.message);
      });
    });
    db.markReminderNotified(r.id);
  });
}

runPushCheck(); // فور بدء السيرفر
const CHECK_PUSH_MS = 60 * 1000;
setInterval(runPushCheck, CHECK_PUSH_MS); // ثم كل دقيقة (يتوقف عند نوم السيرفر على Koyeb)

// مسار لتفعيل الفحص من كرون خارجي (حتى يعمل التنبيه عندما السيرفر نائم - Scale to Zero)
app.get('/api/push/check', (req, res) => {
  const secret = process.env.CRON_SECRET;
  if (!secret) return res.status(503).json({ error: 'CRON_SECRET غير مضبوط في Koyeb' });
  if (req.query.secret !== secret) return res.status(401).json({ error: 'غير مصرح' });
  runPushCheck();
  res.json({ ok: true, message: 'تم فحص التنبيهات' });
});

// تشخيص: عدد الاشتراكات والتنبيهات (للتأكد من أن البيانات موجودة على السيرفر)
app.get('/api/push/status', (req, res) => {
  const secret = process.env.CRON_SECRET;
  if (!secret || req.query.secret !== secret) return res.status(401).json({ error: 'غير مصرح' });
  const stats = db.getStats();
  res.json({
    ok: true,
    push_subscriptions_count: stats.push_subscriptions_count,
    reminders_count: stats.reminders_count,
    due_not_notified_count: stats.due_not_notified_count,
    vapid_set: !!(vapidKeys.publicKey && vapidKeys.privateKey)
  });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log('سيرفر التنبيهات يعمل على المنفذ', PORT);
});
