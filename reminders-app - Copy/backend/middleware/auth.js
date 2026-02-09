const jwt = require('jsonwebtoken');
const JWT_SECRET = process.env.JWT_SECRET || 'reminders-secret-change-in-production';

function auth(req, res, next) {
  const header = req.headers.authorization;
  if (!header || !header.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'يجب تسجيل الدخول' });
  }
  const token = header.slice(7);
  try {
    const payload = jwt.verify(token, JWT_SECRET);
    req.userId = payload.userId;
    next();
  } catch (e) {
    return res.status(401).json({ error: 'انتهت الجلسة، سجّل الدخول مرة أخرى' });
  }
}

module.exports = { auth, JWT_SECRET };
