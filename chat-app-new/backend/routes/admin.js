import { Router } from 'express';
import { db } from '../db.js';
import { jwtVerify } from '../middleware/auth.js';

const router = Router();
const ADMIN_IDS = (process.env.ADMIN_USER_IDS || '1').split(',').map((s) => parseInt(s.trim(), 10)).filter(Boolean);
const isAdmin = (id) => id && ADMIN_IDS.includes(Number(id));

router.use(jwtVerify);

router.post('/block-user', (req, res) => {
  if (!isAdmin(req.userId)) return res.status(403).json({ error: 'غير مصرح' });
  const { targetUserId } = req.body || {};
  if (!targetUserId) return res.status(400).json({ error: 'معرف المستخدم مطلوب' });
  if (Number(targetUserId) === Number(req.userId)) return res.status(400).json({ error: 'لا يمكنك إيقاف نفسك' });
  const ok = db.blockUser(targetUserId);
  if (!ok) return res.status(400).json({ error: 'مُوقَف مسبقاً أو غير صالح' });
  res.json({ ok: true });
});

router.post('/unblock-user', (req, res) => {
  if (!isAdmin(req.userId)) return res.status(403).json({ error: 'غير مصرح' });
  const { targetUserId } = req.body || {};
  if (!targetUserId) return res.status(400).json({ error: 'معرف المستخدم مطلوب' });
  db.unblockUser(targetUserId);
  res.json({ ok: true });
});

router.get('/blocked-users', (req, res) => {
  if (!isAdmin(req.userId)) return res.status(403).json({ error: 'غير مصرح' });
  const list = db.getBlockedUsers().map((u) => ({ id: u.id, name: u.name, email: u.email, phone: u.phone }));
  res.json({ users: list });
});

export default router;
