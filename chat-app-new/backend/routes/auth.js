import { Router } from 'express';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { db } from '../db.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const CODES_FILE = path.join(__dirname, '..', 'last_codes.json');

function writeCodeToFile(key, code, type) {
  try {
    let data = {};
    if (fs.existsSync(CODES_FILE)) {
      data = JSON.parse(fs.readFileSync(CODES_FILE, 'utf8'));
    }
    if (!data[type]) data[type] = {};
    data[type][key] = { code, at: new Date().toISOString() };
    fs.writeFileSync(CODES_FILE, JSON.stringify(data, null, 2));
  } catch (e) { console.error('writeCodeToFile:', e); }
}

const router = Router();
const JWT_SECRET = process.env.JWT_SECRET || 'chat-secret-change-in-production';
const CAN_SEND_EMAIL = !!(process.env.SMTP_HOST || process.env.RESEND_API_KEY);
const CAN_SEND_SMS = !!process.env.TWILIO_ACCOUNT_SID;
const SKIP_VERIFICATION = process.env.SKIP_VERIFICATION === 'true';
const APPROVAL_MODE = process.env.APPROVAL_MODE === 'true';

function genCode() {
  return String(Math.floor(100000 + Math.random() * 900000));
}

function parseEmailOrPhone(input) {
  const s = (input || '').trim();
  if (!s) return { email: null, phone: null };
  if (s.includes('@')) return { email: s.toLowerCase(), phone: null };
  const digits = s.replace(/\D/g, '');
  return { email: null, phone: digits.length >= 10 ? digits : null };
}

const ADMIN_IDS = (process.env.ADMIN_USER_IDS || '1').split(',').map((s) => parseInt(s.trim(), 10)).filter(Boolean);
const isAdmin = (id) => id && ADMIN_IDS.includes(Number(id));

function userToResponse(user) {
  if (!user) return null;
  return { id: user.id, email: user.email || null, phone: user.phone || null, name: user.name, avatar_url: user.avatar_url || null, isAdmin: isAdmin(user.id) };
}

router.post('/register', async (req, res) => {
  const { emailOrPhone, password, name } = req.body || {};
  if (!emailOrPhone || !password) return res.status(400).json({ error: 'البريد أو رقم الموبايل وكلمة المرور مطلوبان' });
  const { email, phone } = parseEmailOrPhone(emailOrPhone);
  if (!email && !phone) return res.status(400).json({ error: 'أدخل بريداً إلكترونياً صحيحاً أو رقم موبايل (10 أرقام على الأقل)' });
  if (email && db.findUserByEmail(email)) return res.status(400).json({ error: 'البريد مستخدم مسبقاً' });
  if (phone && db.findUserByPhone(phone)) return res.status(400).json({ error: 'رقم الموبايل مستخدم مسبقاً' });
  const password_hash = await bcrypt.hash(password, 10);
  const code = genCode();
  const expires = new Date(Date.now() + 10 * 60 * 1000).toISOString();
  const user = db.addUser({
    email: email || undefined,
    phone: phone || undefined,
    password_hash,
    name,
    verification_code: code,
    verification_expires: expires
  });
  if (SKIP_VERIFICATION) {
    db.setUserVerified(user.id, true);
    const verifiedUser = db.findUserById(user.id);
    const token = jwt.sign({ userId: verifiedUser.id }, JWT_SECRET, { expiresIn: '30d' });
    return res.json({ token, user: userToResponse(verifiedUser) });
  }
  if (APPROVAL_MODE) {
    return res.json({ needsApproval: true, msg: 'تم التسجيل. حسابك في انتظار التفعيل من المسؤول.' });
  }
  try {
    if (email && process.env.RESEND_API_KEY) {
      const fromEmail = process.env.RESEND_FROM || 'Karas شات <onboarding@resend.dev>';
      const r = await fetch('https://api.resend.com/emails', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${process.env.RESEND_API_KEY}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          from: fromEmail,
          to: email,
          subject: 'تأكيد الحساب - Karas شات',
          text: `رمز التحقق: ${code}\nصلاحية الرمز: 10 دقائق.`
        })
      });
      if (!r.ok) throw new Error(await r.text());
    } else if (email && process.env.SMTP_HOST) {
      const nodemailer = (await import('nodemailer')).default;
      const transporter = nodemailer.createTransport({
        host: process.env.SMTP_HOST,
        port: parseInt(process.env.SMTP_PORT || '587', 10),
        secure: process.env.SMTP_SECURE === 'true',
        auth: { user: process.env.SMTP_USER, pass: process.env.SMTP_PASS }
      });
      await transporter.sendMail({
        from: process.env.SMTP_FROM || process.env.SMTP_USER,
        to: email,
        subject: 'تأكيد الحساب - Karas شات',
        text: `رمز التحقق: ${code}\nصلاحية الرمز: 10 دقائق.`
      });
    } else if (phone && process.env.TWILIO_ACCOUNT_SID) {
      const twilio = (await import('twilio')).default;
      const client = twilio(process.env.TWILIO_ACCOUNT_SID, process.env.TWILIO_AUTH_TOKEN);
      await client.messages.create({
        body: `رمز التحقق Karas شات: ${code}`,
        from: process.env.TWILIO_PHONE,
        to: '+' + phone.replace(/\D/g, '')
      });
    } else {
      const recipient = email || phone;
      console.log('\n━━━ [وضع التطوير] رمز التحقق ━━━');
      console.log('  المستلم:', recipient);
      console.log('  الرمز:', code);
      console.log('  الصلاحية: 10 دقائق');
      console.log('  (يُحفظ أيضاً في ملف last_codes.json)');
      console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
      writeCodeToFile(recipient, code, 'verification');
    }
  } catch (err) {
    console.error('Send verification:', err);
  }
  res.json({ needsVerification: true, emailOrPhone: email || phone });
});

router.post('/verify', async (req, res) => {
  const { emailOrPhone, code } = req.body || {};
  if (!emailOrPhone || !code) return res.status(400).json({ error: 'أدخل البريد/الهاتف ورمز التحقق' });
  const user = db.findUserByEmailOrPhone(emailOrPhone);
  if (!user) return res.status(401).json({ error: 'الحساب غير موجود' });
  if (user.verified) {
    const token = jwt.sign({ userId: user.id }, JWT_SECRET, { expiresIn: '30d' });
    return res.json({ token, user: userToResponse(user) });
  }
  const codeNorm = String(code || '').replace(/\D/g, '');
  const savedNorm = String(user.verification_code || '').replace(/\D/g, '');
  if (codeNorm !== savedNorm || !codeNorm) return res.status(401).json({ error: 'رمز التحقق غير صحيح' });
  if (user.verification_expires && new Date(user.verification_expires) < new Date()) {
    return res.status(401).json({ error: 'انتهت صلاحية الرمز. اطلب رمزاً جديداً.' });
  }
  db.setUserVerified(user.id, true);
  const updated = db.findUserById(user.id);
  const token = jwt.sign({ userId: updated.id }, JWT_SECRET, { expiresIn: '30d' });
  res.json({ token, user: userToResponse(updated) });
});

router.post('/forgot-password', async (req, res) => {
  const { emailOrPhone } = req.body || {};
  if (!emailOrPhone || !String(emailOrPhone).trim()) return res.status(400).json({ error: 'أدخل البريد أو رقم الموبايل' });
  const user = db.findUserByEmailOrPhone(emailOrPhone.trim());
  if (!user) return res.status(401).json({ error: 'لا يوجد حساب بهذا البريد أو رقم الموبايل' });
  const { email, phone } = parseEmailOrPhone(emailOrPhone.trim());
  const code = genCode();
  const expires = new Date(Date.now() + 15 * 60 * 1000).toISOString();
  db.setResetCode(user.id, code, expires);
  try {
    if (email && process.env.RESEND_API_KEY) {
      const fromEmail = process.env.RESEND_FROM || 'Karas شات <onboarding@resend.dev>';
      const r = await fetch('https://api.resend.com/emails', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${process.env.RESEND_API_KEY}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ from: fromEmail, to: email, subject: 'استعادة كلمة المرور - Karas شات', text: `رمز الاستعادة: ${code}\nصلاحية الرمز: 15 دقيقة.` })
      });
      if (!r.ok) throw new Error(await r.text());
    } else if (email && process.env.SMTP_HOST) {
      const nodemailer = (await import('nodemailer')).default;
      const transporter = nodemailer.createTransport({
        host: process.env.SMTP_HOST,
        port: parseInt(process.env.SMTP_PORT || '587', 10),
        secure: process.env.SMTP_SECURE === 'true',
        auth: { user: process.env.SMTP_USER, pass: process.env.SMTP_PASS }
      });
      await transporter.sendMail({
        from: process.env.SMTP_FROM || process.env.SMTP_USER,
        to: email,
        subject: 'استعادة كلمة المرور - Karas شات',
        text: `رمز الاستعادة: ${code}\nصلاحية الرمز: 15 دقيقة.`
      });
    } else if (phone && process.env.TWILIO_ACCOUNT_SID) {
      const twilio = (await import('twilio')).default;
      const client = twilio(process.env.TWILIO_ACCOUNT_SID, process.env.TWILIO_AUTH_TOKEN);
      await client.messages.create({
        body: `رمز استعادة كلمة المرور Karas شات: ${code}`,
        from: process.env.TWILIO_PHONE,
        to: '+' + phone.replace(/\D/g, '')
      });
    } else {
      const recipient = email || phone;
      console.log('\n━━━ [وضع التطوير] رمز استعادة كلمة المرور ━━━');
      console.log('  المستلم:', recipient);
      console.log('  الرمز:', code);
      console.log('  الصلاحية: 15 دقيقة');
      console.log('  (يُحفظ أيضاً في ملف last_codes.json)');
      console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
      writeCodeToFile(recipient, code, 'reset');
    }
  } catch (err) {
    console.error('Send reset code:', err);
  }
  res.json({ ok: true, msg: 'تم إرسال رمز الاستعادة' });
});

router.post('/reset-password', async (req, res) => {
  const { emailOrPhone, code, newPassword } = req.body || {};
  if (!emailOrPhone || !code || !newPassword || newPassword.length < 6) {
    return res.status(400).json({ error: 'أدخل البريد/الهاتف ورمز الاستعادة وكلمة مرور جديدة (6 أحرف على الأقل)' });
  }
  const user = db.findUserByEmailOrPhone(emailOrPhone.trim());
  if (!user) return res.status(401).json({ error: 'الحساب غير موجود' });
  const codeNorm = String(code || '').replace(/\D/g, '');
  const savedNorm = String(user.reset_code || '').replace(/\D/g, '');
  if (codeNorm !== savedNorm || !codeNorm) return res.status(401).json({ error: 'رمز الاستعادة غير صحيح' });
  if (user.reset_expires && new Date(user.reset_expires) < new Date()) return res.status(401).json({ error: 'انتهت صلاحية الرمز. اطلب رمزاً جديداً.' });
  const password_hash = await bcrypt.hash(newPassword, 10);
  db.updateUserPassword(user.id, password_hash);
  const token = jwt.sign({ userId: user.id }, JWT_SECRET, { expiresIn: '30d' });
  res.json({ token, user: userToResponse(db.findUserById(user.id)) });
});

router.post('/login', async (req, res) => {
  const { emailOrPhone, password } = req.body || {};
  if (!emailOrPhone || !password) return res.status(400).json({ error: 'البريد أو رقم الموبايل وكلمة المرور مطلوبان' });
  const user = db.findUserByEmailOrPhone(emailOrPhone);
  if (!user) return res.status(401).json({ error: 'بيانات الدخول غير صحيحة' });
  if (db.isUserBlocked(user.id)) return res.status(403).json({ error: 'تم إيقاف وصولك من قبل المسؤول' });
  if (user.verified === false && !SKIP_VERIFICATION) return res.status(403).json({ error: 'يجب تأكيد الحساب أولاً. أدخل رمز التحقق المرسل إليك.' });
  const ok = await bcrypt.compare(password, user.password_hash);
  if (!ok) return res.status(401).json({ error: 'بيانات الدخول غير صحيحة' });
  const token = jwt.sign({ userId: user.id }, JWT_SECRET, { expiresIn: '30d' });
  res.json({ token, user: userToResponse(user) });
});

export default router;
