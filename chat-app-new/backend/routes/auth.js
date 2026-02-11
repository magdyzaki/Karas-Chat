import { Router } from 'express';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { db } from '../db.js';

const router = Router();
const JWT_SECRET = process.env.JWT_SECRET || 'chat-secret-change-in-production';

function parseEmailOrPhone(input) {
  const s = (input || '').trim();
  if (!s) return { email: null, phone: null };
  if (s.includes('@')) return { email: s.toLowerCase(), phone: null };
  const digits = s.replace(/\D/g, '');
  return { email: null, phone: digits.length >= 10 ? digits : null };
}

function userToResponse(user) {
  if (!user) return null;
  return { id: user.id, email: user.email || null, phone: user.phone || null, name: user.name };
}

router.post('/register', async (req, res) => {
  const { emailOrPhone, password, name } = req.body || {};
  if (!emailOrPhone || !password) return res.status(400).json({ error: 'البريد أو رقم الموبايل وكلمة المرور مطلوبان' });
  const { email, phone } = parseEmailOrPhone(emailOrPhone);
  if (!email && !phone) return res.status(400).json({ error: 'أدخل بريداً إلكترونياً صحيحاً أو رقم موبايل (10 أرقام على الأقل)' });
  if (email && db.findUserByEmail(email)) return res.status(400).json({ error: 'البريد مستخدم مسبقاً' });
  if (phone && db.findUserByPhone(phone)) return res.status(400).json({ error: 'رقم الموبايل مستخدم مسبقاً' });
  const password_hash = await bcrypt.hash(password, 10);
  const user = db.addUser({ email: email || undefined, phone: phone || undefined, password_hash, name });
  const token = jwt.sign({ userId: user.id }, JWT_SECRET, { expiresIn: '30d' });
  res.json({ token, user: userToResponse(user) });
});

router.post('/login', async (req, res) => {
  const { emailOrPhone, password } = req.body || {};
  if (!emailOrPhone || !password) return res.status(400).json({ error: 'البريد أو رقم الموبايل وكلمة المرور مطلوبان' });
  const user = db.findUserByEmailOrPhone(emailOrPhone);
  if (!user) return res.status(401).json({ error: 'بيانات الدخول غير صحيحة' });
  if (db.isUserBlocked(user.id)) return res.status(403).json({ error: 'تم إيقاف وصولك من قبل المسؤول' });
  const ok = await bcrypt.compare(password, user.password_hash);
  if (!ok) return res.status(401).json({ error: 'بيانات الدخول غير صحيحة' });
  const token = jwt.sign({ userId: user.id }, JWT_SECRET, { expiresIn: '30d' });
  res.json({ token, user: userToResponse(user) });
});

export default router;
