import { Router } from 'express';
import { db } from '../db.js';
import { jwtVerify } from '../middleware/auth.js';

const router = Router();
const ADMIN_IDS = (process.env.ADMIN_USER_IDS || '1').split(',').map((s) => parseInt(s.trim(), 10)).filter(Boolean);
const isAdmin = (id) => id && ADMIN_IDS.includes(Number(id));

// إنشاء رابط دعوة (للأدمن فقط)
router.post('/invite-links', jwtVerify, (req, res) => {
  if (!isAdmin(req.userId)) return res.status(403).json({ error: 'غير مصرح - إنشاء الروابط مقتصر على الأدمن' });
  const row = db.createInviteLink(req.userId);
  res.json({ token: row.token });
});

// التحقق فقط — لا يُستهلك (لتفادي استهلاك الرابط عند معاينة واتساب)
router.get('/check-invite/:token', (req, res) => {
  const { token } = req.params;
  if (!token) return res.status(400).json({ valid: false, error: 'رابط غير صالح' });
  const link = db.getInviteLink(token);
  if (!link) return res.json({ valid: false, used: false, error: 'رابط غير صالح' });
  if (link.used_at) return res.json({ valid: false, used: true, error: 'تم استخدام هذا الرابط مسبقاً' });
  res.json({ valid: true, used: false });
});

// استهلاك الرابط — يُستدعى فقط عند الضغط على «انتقل إلى التطبيق»
router.post('/consume-invite/:token', (req, res) => {
  const { token } = req.params;
  if (!token) return res.status(400).json({ ok: false, error: 'رابط غير صالح' });
  const link = db.getInviteLink(token);
  if (!link) return res.json({ ok: false, error: 'رابط غير صالح' });
  if (link.used_at) return res.json({ ok: false, error: 'الرابط مُستهلَك مسبقاً' });
  const ok = db.consumeInviteLink(token);
  if (!ok) return res.json({ ok: false, error: 'فشل' });
  res.json({ ok: true });
});

export default router;
