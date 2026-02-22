const express = require('express');
const db = require('../db');
const { auth } = require('../middleware/auth');

const router = express.Router();
const ADMIN_IDS = (process.env.ADMIN_USER_IDS || '1').split(',').map((s) => parseInt(s.trim(), 10)).filter(Boolean);
const isAdmin = (id) => id && ADMIN_IDS.includes(Number(id));

router.use(auth);

router.post('/block-user', async (req, res) => {
  if (!isAdmin(req.userId)) return res.status(403).json({ error: 'غير مصرح' });
  const { targetUserId } = req.body || {};
  if (!targetUserId) return res.status(400).json({ error: 'معرف المستخدم مطلوب' });
  if (Number(targetUserId) === Number(req.userId)) return res.status(400).json({ error: 'لا يمكنك إيقاف نفسك' });
  try {
    const ok = await db.blockUser(targetUserId);
    if (!ok) return res.status(400).json({ error: 'مُوقَف مسبقاً أو غير صالح' });
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ error: e.message || 'فشل' });
  }
});

router.post('/unblock-user', async (req, res) => {
  if (!isAdmin(req.userId)) return res.status(403).json({ error: 'غير مصرح' });
  const { targetUserId } = req.body || {};
  if (!targetUserId) return res.status(400).json({ error: 'معرف المستخدم مطلوب' });
  try {
    await db.unblockUser(targetUserId);
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ error: e.message || 'فشل' });
  }
});

router.get('/blocked-users', async (req, res) => {
  if (!isAdmin(req.userId)) return res.status(403).json({ error: 'غير مصرح' });
  try {
    const list = await db.getBlockedUsers();
    res.json({ users: list });
  } catch (e) {
    res.status(500).json({ error: e.message || 'فشل' });
  }
});

router.get('/all-users', async (req, res) => {
  if (!isAdmin(req.userId)) return res.status(403).json({ error: 'غير مصرح' });
  try {
    const list = await db.getAllUsers();
    res.json({ users: list });
  } catch (e) {
    res.status(500).json({ error: e.message || 'فشل' });
  }
});

module.exports = router;
