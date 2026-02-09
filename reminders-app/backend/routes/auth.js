const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const db = require('../db');
const { JWT_SECRET } = require('../middleware/auth');

const router = express.Router();

// تسجيل مستخدم جديد
router.post('/register', (req, res) => {
  const { email, password, name } = req.body || {};
  if (!email || !password) {
    return res.status(400).json({ error: 'البريد الإلكتروني وكلمة المرور مطلوبان' });
  }
  const emailNorm = email.trim().toLowerCase();
  if (db.findUserByEmail(emailNorm)) {
    return res.status(400).json({ error: 'البريد الإلكتروني مستخدم بالفعل' });
  }
  const hash = bcrypt.hashSync(password.trim(), 10);
  const row = db.addUser({
    email: emailNorm,
    password_hash: hash,
    name: (name || '').trim()
  });
  const token = jwt.sign({ userId: row.id }, JWT_SECRET, { expiresIn: '30d' });
  return res.json({
    user: { id: row.id, email: row.email, name: row.name },
    token
  });
});

// تسجيل الدخول
router.post('/login', (req, res) => {
  const { email, password } = req.body || {};
  if (!email || !password) {
    return res.status(400).json({ error: 'البريد الإلكتروني وكلمة المرور مطلوبان' });
  }
  const row = db.findUserByEmail(email.trim().toLowerCase());
  if (!row || !bcrypt.compareSync(password.trim(), row.password_hash)) {
    return res.status(401).json({ error: 'البريد أو كلمة المرور غير صحيحة' });
  }
  const token = jwt.sign({ userId: row.id }, JWT_SECRET, { expiresIn: '30d' });
  res.json({ user: { id: row.id, email: row.email, name: row.name }, token });
});

module.exports = router;
