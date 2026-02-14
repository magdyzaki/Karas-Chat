import { Router } from 'express';
import { db } from '../db.js';

const router = Router();
const ADMIN_IDS = (process.env.ADMIN_USER_IDS || '1').split(',').map((s) => parseInt(s.trim(), 10)).filter(Boolean);
const isAdmin = (id) => id && ADMIN_IDS.includes(Number(id));

router.get('/', (req, res) => {
  let users = db.listUsersExcept(req.userId);
  users = users.filter((u) => !db.isUserBlocked(u.id));
  res.json({ users });
});

router.post('/check-contacts', (req, res) => {
  const { phoneNumbers } = req.body || {};
  const arr = Array.isArray(phoneNumbers) ? phoneNumbers : (typeof phoneNumbers === 'string' ? [phoneNumbers] : []);
  const users = db.findUsersByPhones(arr, req.userId);
  res.json({ users });
});

router.get('/me', (req, res) => {
  const user = db.findUserById(req.userId);
  if (!user) return res.status(404).json({ error: 'المستخدم غير موجود' });
  res.json({ id: user.id, email: user.email, phone: user.phone, name: user.name, avatar_url: user.avatar_url || null, isAdmin: isAdmin(user.id) });
});

router.patch('/me', (req, res) => {
  const { name, avatar_url } = req.body || {};
  const user = db.updateUserProfile(req.userId, { name, avatar_url });
  if (!user) return res.status(404).json({ error: 'المستخدم غير موجود' });
  res.json({ id: user.id, email: user.email, phone: user.phone, name: user.name, avatar_url: user.avatar_url || null });
});

router.put('/me/e2e-key', (req, res) => {
  const { publicKey } = req.body || {};
  if (!publicKey || typeof publicKey !== 'string') return res.status(400).json({ error: 'المفتاح العام مطلوب' });
  db.setUserPublicKey(req.userId, publicKey);
  res.json({ ok: true });
});

router.get('/:id/e2e-key', (req, res) => {
  const key = db.getUserPublicKey(req.params.id);
  res.json({ publicKey: key });
});

export default router;
