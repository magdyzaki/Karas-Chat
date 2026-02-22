import jwt from 'jsonwebtoken';
import { db } from '../db.js';

const JWT_SECRET = process.env.JWT_SECRET || 'karas-secret-change-me';

export function jwtVerify(req, res, next) {
  const auth = req.headers.authorization;
  const token = auth?.startsWith('Bearer ') ? auth.slice(7) : null;
  if (!token) return res.status(401).json({ error: 'غير مصرح' });
  jwt.verify(token, JWT_SECRET, (err, d) => {
    if (err) return res.status(401).json({ error: 'رمز غير صالح' });
    if (db.isUserBlocked(d.userId)) return res.status(403).json({ error: 'تم إيقافك' });
    req.userId = d.userId;
    next();
  });
}
