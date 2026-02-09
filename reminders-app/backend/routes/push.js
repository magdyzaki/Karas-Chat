const express = require('express');
const webpush = require('web-push');
const db = require('../db');
const { auth } = require('../middleware/auth');

const router = express.Router();

// مفتاح VAPID العام (يُعرَض للواجهة للاشتراك) — إزالة أي مسافات أو أسطر جديدة
router.get('/vapid-public', (req, res) => {
  const pub = (process.env.VAPID_PUBLIC_KEY || '').trim().replace(/\s/g, '');
  if (!pub) return res.status(503).json({ error: 'VAPID غير مضبوط' });
  res.json({ publicKey: pub });
});

// حفظ اشتراك الجهاز لإرسال التنبيهات حتى مع إطفاء الشاشة
router.post('/subscribe', auth, (req, res) => {
  const subscription = req.body;
  if (!subscription || !subscription.endpoint || !subscription.keys) {
    return res.status(400).json({ error: 'صيغة الاشتراك غير صحيحة' });
  }
  db.addPushSubscription(req.userId, subscription);
  res.json({ ok: true });
});

module.exports = router;

function getVapidKeys() {
  const pub = process.env.VAPID_PUBLIC_KEY;
  const priv = process.env.VAPID_PRIVATE_KEY;
  if (pub && priv) return { publicKey: pub, privateKey: priv };
  return null;
}

function sendPushToSubscriptions(subscriptions, payload) {
  const keys = getVapidKeys();
  if (!keys) return Promise.resolve();
  webpush.setVapidDetails('mailto:reminders@local', keys.publicKey, keys.privateKey);
  return Promise.all(
    subscriptions.map((sub) => {
      const pushSub = { endpoint: sub.endpoint, keys: sub.keys };
      return webpush.sendNotification(pushSub, JSON.stringify(payload)).catch((err) => {
        console.error('Push failed:', err.message);
      });
    })
  );
}

module.exports.sendPushToSubscriptions = sendPushToSubscriptions;
module.exports.getVapidKeys = getVapidKeys;
