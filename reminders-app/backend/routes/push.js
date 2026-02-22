const express = require('express');
const webpush = require('web-push');
const db = require('../db');
const { auth } = require('../middleware/auth');

const router = express.Router();

router.get('/vapid-public', (req, res) => {
  const pub = (process.env.VAPID_PUBLIC_KEY || '').trim().replace(/\s/g, '');
  if (!pub) return res.status(503).json({ error: 'VAPID غير مضبوط' });
  res.json({ publicKey: pub });
});

router.post('/subscribe', auth, async (req, res) => {
  try {
    const subscription = req.body;
    if (!subscription || !subscription.endpoint || !subscription.keys) {
      return res.status(400).json({ error: 'صيغة الاشتراك غير صحيحة' });
    }
    await db.addPushSubscription(req.userId, subscription);
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ error: e.message || 'خطأ في حفظ الاشتراك' });
  }
});

module.exports = router;
