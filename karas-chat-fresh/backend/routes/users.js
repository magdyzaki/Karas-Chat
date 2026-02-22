import { Router } from 'express';
import { db } from '../db.js';

const router = Router();

router.get('/', (req, res) => {
  let users = db.listUsersExcept(req.userId);
  users = users.filter((u) => !db.isUserBlocked(u.id));
  res.json({ users });
});

router.post('/check-contacts', (req, res) => {
  const arr = Array.isArray(req.body?.phoneNumbers) ? req.body.phoneNumbers : (typeof req.body?.phoneNumbers === 'string' ? [req.body.phoneNumbers] : []);
  const users = db.findUsersByPhones(arr, req.userId);
  res.json({ users });
});

export default router;
