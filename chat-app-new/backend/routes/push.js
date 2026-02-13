import { Router } from 'express';
import webpush from 'web-push';
import { db } from '../db.js';
import { jwtVerify } from '../middleware/auth.js';

const router = Router();
const VAPID_PUBLIC = process.env.VAPID_PUBLIC_KEY;
const VAPID_PRIVATE = process.env.VAPID_PRIVATE_KEY;

if (VAPID_PUBLIC && VAPID_PRIVATE) {
  webpush.setVapidDetails('mailto:chat@karas.app', VAPID_PUBLIC, VAPID_PRIVATE);
}

router.post('/subscribe', jwtVerify, (req, res) => {
  if (!VAPID_PUBLIC || !VAPID_PRIVATE) return res.status(503).json({ error: 'التنبيهات غير مفعّلة. راجع إعدادات السيرفر' });
  const subscription = req.body?.subscription;
  if (!subscription || !subscription.endpoint) return res.status(400).json({ error: 'بيانات الاشتراك مطلوبة' });
  const ok = db.savePushSubscription(req.userId, subscription);
  if (!ok) return res.status(500).json({ error: 'فشل حفظ الاشتراك' });
  res.json({ ok: true });
});

export { router as pushRoutes };
export async function sendPushToUser(userId, payload) {
  if (!VAPID_PUBLIC || !VAPID_PRIVATE) return;
  const subs = db.getPushSubscriptionsForUser(userId);
  const body = JSON.stringify(payload);
  for (const sub of subs) {
    try {
      await webpush.sendNotification(
        { endpoint: sub.endpoint, keys: sub.keys },
        body,
        { TTL: 60 }
      );
    } catch (e) {
      if (e.statusCode === 410 || e.statusCode === 404) {
        db.removePushSubscription(userId, sub.endpoint);
      }
    }
  }
}
