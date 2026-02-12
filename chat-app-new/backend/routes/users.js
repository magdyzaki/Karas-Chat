import { Router } from 'express';
import { db } from '../db.js';

const router = Router();

router.post('/check-contacts', (req, res) => {
  const { phoneNumbers } = req.body || {};
  const arr = Array.isArray(phoneNumbers) ? phoneNumbers : (typeof phoneNumbers === 'string' ? [phoneNumbers] : []);
  const users = db.findUsersByPhones(arr, req.userId);
  res.json({ users });
});

router.get('/me', (req, res) => {
  const user = db.findUserById(req.userId);
  if (!user) return res.status(404).json({ error: 'المستخدم غير موجود' });
  res.json({ id: user.id, email: user.email, phone: user.phone, name: user.name, avatar_url: user.avatar_url || null });
});

router.patch('/me', (req, res) => {
  const { name, avatar_url } = req.body || {};
  const user = db.updateUserProfile(req.userId, { name, avatar_url });
  if (!user) return res.status(404).json({ error: 'المستخدم غير موجود' });
  res.json({ id: user.id, email: user.email, phone: user.phone, name: user.name, avatar_url: user.avatar_url || null });
});

export default router;
