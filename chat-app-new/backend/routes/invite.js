import { Router } from 'express';
import { db } from '../db.js';
import { jwtVerify } from '../middleware/auth.js';

const router = Router();

// إنشاء رابط دعوة (للمستخدم المسجّل فقط)
router.post('/invite-links', jwtVerify, (req, res) => {
  const row = db.createInviteLink(req.userId);
  res.json({ token: row.token });
});

// التحقق واستهلاك الرابط (بدون تسجيل دخول — عند فتح الرابط)
router.get('/validate/:token', (req, res) => {
  const { token } = req.params;
  if (!token) return res.status(400).json({ valid: false, error: 'رابط غير صالح' });
  const link = db.getInviteLink(token);
  if (!link) return res.json({ valid: false, error: 'رابط غير صالح' });
  if (link.used_at) return res.json({ valid: false, error: 'تم استخدام هذا الرابط مسبقاً ولا يمكن استخدامه مرة أخرى' });
  const ok = db.consumeInviteLink(token);
  if (!ok) return res.json({ valid: false, error: 'فشل التحقق' });
  res.json({ valid: true });
});

export default router;
