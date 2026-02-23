import jwt from 'jsonwebtoken';
import { db } from '../db-api.js';

const JWT_SECRET = process.env.JWT_SECRET || 'chat-secret-change-in-production';

export async function jwtVerify(req, res, next) {
  const auth = req.headers.authorization;
  const token = auth && auth.startsWith('Bearer ') ? auth.slice(7) : null;
  if (!token) return res.status(401).json({ error: 'انتهت الجلسة أو غير مصرح' });
  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    const user = await db.findUserById(decoded.userId);
    if (!user) return res.status(401).json({ error: 'المستخدم غير موجود' });
    if (await db.isUserBlocked(user.id)) return res.status(403).json({ error: 'تم إيقاف وصولك من قبل المسؤول' });
    req.userId = user.id;
    next();
  } catch (_) {
    res.status(401).json({ error: 'انتهت الجلسة أو غير مصرح' });
  }
}
