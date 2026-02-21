import { Router } from 'express';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { db } from '../db.js';

const router = Router();
const JWT_SECRET = process.env.JWT_SECRET || 'karas-secret-change-me';
const SKIP_VERIFICATION = process.env.SKIP_VERIFICATION === 'true';
const TRUSTED_PHONES = (process.env.TRUSTED_PHONES || '').split(',').map((s) => s.replace(/\D/g, '')).filter(Boolean);

function toCanonicalPhone(phone) {
  const d = String(phone || '').replace(/\D/g, '');
  if (d.length < 10) return '';
  if (d.startsWith('01') && d.length === 11) return '2' + d;
  if (d.startsWith('20') && d.length >= 11) return d.slice(0, 12);
  return d;
}
function isTrusted(phone) {
  if (!phone || !TRUSTED_PHONES.length) return false;
  const p = toCanonicalPhone(phone);
  return TRUSTED_PHONES.some((t) => toCanonicalPhone(t) === p || p.endsWith(toCanonicalPhone(t)) || toCanonicalPhone(t).endsWith(p));
}

function parseInput(input) {
  const s = (input || '').trim();
  if (!s) return { email: null, phone: null };
  if (s.includes('@')) return { email: s.toLowerCase(), phone: null };
  const d = s.replace(/\D/g, '');
  return { email: null, phone: d.length >= 10 ? d : null };
}

router.post('/register', async (req, res) => {
  const { emailOrPhone, password, name } = req.body || {};
  if (!emailOrPhone || !password) return res.status(400).json({ error: 'البريد/الهاتف وكلمة المرور مطلوبان' });
  const { email, phone } = parseInput(emailOrPhone);
  if (!email && !phone) return res.status(400).json({ error: 'أدخل بريداً أو رقم موبايل صحيح' });
  if (email && db.findUserByEmail(email)) return res.status(400).json({ error: 'البريد مستخدم' });
  if (phone && db.findUserByPhone(phone)) return res.status(400).json({ error: 'رقم الموبايل مستخدم' });
  const hash = await bcrypt.hash(password, 10);
  const code = String(Math.floor(100000 + Math.random() * 900000));
  const expires = new Date(Date.now() + 10 * 60 * 1000).toISOString();
  const user = db.addUser({ email: email || undefined, phone: phone || undefined, password_hash: hash, name: name || '', verification_code: code, verification_expires: expires });
  if (SKIP_VERIFICATION || (phone && isTrusted(phone))) {
    db.setUserVerified(user.id, true);
    const u = db.findUserById(user.id);
    const token = jwt.sign({ userId: u.id }, JWT_SECRET, { expiresIn: '30d' });
    return res.json({ token, user: { id: u.id, email: u.email, phone: u.phone, name: u.name } });
  }
  console.log('[تطوير] رمز التحقق:', email || phone, '=', code);
  res.json({ needsVerification: true, emailOrPhone: email || phone });
});

router.post('/verify', async (req, res) => {
  const { emailOrPhone, code } = req.body || {};
  if (!emailOrPhone || !code) return res.status(400).json({ error: 'أدخل البريد/الهاتف ورمز التحقق' });
  const user = db.findUserByEmailOrPhone(emailOrPhone);
  if (!user) return res.status(401).json({ error: 'الحساب غير موجود' });
  if (user.verified) {
    const token = jwt.sign({ userId: user.id }, JWT_SECRET, { expiresIn: '30d' });
    return res.json({ token, user: { id: user.id, email: user.email, phone: user.phone, name: user.name } });
  }
  if (String(code).replace(/\D/g, '') !== String(user.verification_code || '').replace(/\D/g, '')) return res.status(401).json({ error: 'رمز خاطئ' });
  if (user.verification_expires && new Date(user.verification_expires) < new Date()) return res.status(401).json({ error: 'انتهت صلاحية الرمز' });
  db.setUserVerified(user.id, true);
  const u = db.findUserById(user.id);
  const token = jwt.sign({ userId: u.id }, JWT_SECRET, { expiresIn: '30d' });
  res.json({ token, user: { id: u.id, email: u.email, phone: u.phone, name: u.name } });
});

router.post('/login', async (req, res) => {
  const { emailOrPhone, password } = req.body || {};
  if (!emailOrPhone || !password) return res.status(400).json({ error: 'أدخل البريد/الهاتف وكلمة المرور' });
  const user = db.findUserByEmailOrPhone(emailOrPhone);
  if (!user) return res.status(401).json({ error: 'بيانات غير صحيحة' });
  if (db.isUserBlocked(user.id)) return res.status(403).json({ error: 'تم إيقافك' });
  if (!user.verified && !SKIP_VERIFICATION && !(user.phone && isTrusted(user.phone))) return res.status(403).json({ error: 'يجب تأكيد الحساب أولاً' });
  if (!user.verified && user.phone && isTrusted(user.phone)) db.setUserVerified(user.id, true);
  const ok = await bcrypt.compare(password, user.password_hash);
  if (!ok) return res.status(401).json({ error: 'بيانات غير صحيحة' });
  const token = jwt.sign({ userId: user.id }, JWT_SECRET, { expiresIn: '30d' });
  res.json({ token, user: { id: user.id, email: user.email, phone: user.phone, name: user.name } });
});

export default router;
