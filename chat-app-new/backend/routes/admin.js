import { Router } from 'express';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { db } from '../db.js';
import { jwtVerify } from '../middleware/auth.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const router = Router();
const ADMIN_IDS = (process.env.ADMIN_USER_IDS || '1').split(',').map((s) => parseInt(s.trim(), 10)).filter(Boolean);
const isAdmin = (id) => id && ADMIN_IDS.includes(Number(id));
const ALLOW_RESET = process.env.ALLOW_DB_RESET === 'true';

router.post('/reset-database', (req, res) => {
  if (!ALLOW_RESET) return res.status(403).json({ error: 'غير مفعّل. أضف ALLOW_DB_RESET=true في .env للسماح' });
  db.resetAll();
  res.json({ ok: true, msg: 'تم مسح جميع البيانات. سجّل من جديد لتصبح المعرف 1' });
});

router.use(jwtVerify);

router.get('/pending-codes', (req, res) => {
  if (!isAdmin(req.userId)) return res.status(403).json({ error: 'غير مصرح' });
  try {
    const fp = path.join(__dirname, '..', 'last_codes.json');
    if (!fs.existsSync(fp)) return res.json({ verification: {}, reset: {} });
    const data = JSON.parse(fs.readFileSync(fp, 'utf8'));
    res.json({ verification: data.verification || {}, reset: data.reset || {} });
  } catch (e) {
    res.json({ verification: {}, reset: {} });
  }
});

router.get('/users', (req, res) => {
  if (!isAdmin(req.userId)) return res.status(403).json({ error: 'غير مصرح' });
  const list = db.listUsersExcept(null).map((u) => ({ id: u.id, name: u.name, email: u.email, phone: u.phone, avatar_url: u.avatar_url || null }));
  res.json({ users: list });
});

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

router.get('/pending-users', (req, res) => {
  if (!isAdmin(req.userId)) return res.status(403).json({ error: 'غير مصرح' });
  const list = db.getUnverifiedUsers();
  res.json({ users: list });
});

router.post('/approve-user', (req, res) => {
  if (!isAdmin(req.userId)) return res.status(403).json({ error: 'غير مصرح' });
  const { targetUserId } = req.body || {};
  if (!targetUserId) return res.status(400).json({ error: 'معرف المستخدم مطلوب' });
  const ok = db.setUserVerified(Number(targetUserId), true);
  if (!ok) return res.status(400).json({ error: 'المستخدم غير موجود أو مُفعّل مسبقاً' });
  res.json({ ok: true, msg: 'تم تفعيل الحساب' });
});

router.get('/blocked-users', (req, res) => {
  if (!isAdmin(req.userId)) return res.status(403).json({ error: 'غير مصرح' });
  const list = db.getBlockedUsers().map((u) => ({ id: u.id, name: u.name, email: u.email, phone: u.phone }));
  res.json({ users: list });
});

export default router;
