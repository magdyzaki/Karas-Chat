import { Router } from 'express';
import { db } from '../db.js';

const router = Router();

router.post('/check-contacts', (req, res) => {
  const { phoneNumbers } = req.body || {};
  const arr = Array.isArray(phoneNumbers) ? phoneNumbers : (typeof phoneNumbers === 'string' ? [phoneNumbers] : []);
  const users = db.findUsersByPhones(arr, req.userId);
  res.json({ users });
});

export default router;
