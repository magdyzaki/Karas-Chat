import { Router } from 'express';
import { db } from '../db.js';

const router = Router();

router.get('/', (req, res) => {
  const list = db.listUsersExcept(req.userId);
  res.json({ users: list });
});

export default router;
