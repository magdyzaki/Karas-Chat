const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const db = require('../db');
const { JWT_SECRET } = require('../middleware/auth');

const router = express.Router();

router.post('/register', async (req, res) => {
  try {
    const { email, password, name } = req.body || {};
    if (!email || !password) {
      return res.status(400).json({ error: 'البريد الإلكتروني وكلمة المرور مطلوبان' });
    }
    const emailNorm = email.trim().toLowerCase();
    const existing = await db.findUserByEmail(emailNorm);
    if (existing) {
      return res.status(400).json({ error: 'البريد الإلكتروني مستخدم بالفعل' });
    }
    const hash = bcrypt.hashSync(password.trim(), 10);
    const row = await db.addUser({
      email: emailNorm,
      password_hash: hash,
      name: (name || '').trim()
    });
    const token = jwt.sign({ userId: row.id }, JWT_SECRET, { expiresIn: '30d' });
    return res.json({
      user: { id: row.id, email: row.email, name: row.name },
      token
    });
  } catch (e) {
    const msg = e.message || '';
    const isDbError = /SSL|TLS|0A000438|openssl|tlsv1/i.test(msg);
    return res.status(500).json({
      error: isDbError ? 'خطأ في الاتصال بقاعدة البيانات. جرّب بعد دقائق أو راجع إعدادات السيرفر (Node 18 و MONGODB_URI).' : (msg || 'خطأ في التسجيل')
    });
  }
});

router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body || {};
    if (!email || !password) {
      return res.status(400).json({ error: 'البريد الإلكتروني وكلمة المرور مطلوبان' });
    }
    const row = await db.findUserByEmail(email.trim().toLowerCase());
    if (!row || !bcrypt.compareSync(password.trim(), row.password_hash)) {
      return res.status(401).json({ error: 'البريد أو كلمة المرور غير صحيحة' });
    }
    if (await db.isUserBlocked(row.id)) {
      return res.status(403).json({ error: 'تم إيقاف وصولك من قبل المسؤول' });
    }
    const token = jwt.sign({ userId: row.id }, JWT_SECRET, { expiresIn: '30d' });
    res.json({ user: { id: row.id, email: row.email, name: row.name }, token });
  } catch (e) {
    const msg = e.message || '';
    const isDbError = /SSL|TLS|0A000438|openssl|tlsv1/i.test(msg);
    return res.status(500).json({
      error: isDbError ? 'خطأ في الاتصال بقاعدة البيانات. جرّب بعد دقائق أو راجع إعدادات السيرفر (Node 18 و MONGODB_URI).' : (msg || 'خطأ في الدخول')
    });
  }
});

module.exports = router;
