const express = require('express');
const db = require('../db');
const { auth } = require('../middleware/auth');

const router = express.Router();
const ADMIN_IDS = (process.env.ADMIN_USER_IDS || '1').split(',').map((s) => parseInt(s.trim(), 10)).filter(Boolean);
const isAdmin = (id) => id && ADMIN_IDS.includes(Number(id));

router.post('/invite-links', auth, async (req, res) => {
  if (!isAdmin(req.userId)) return res.status(403).json({ error: 'غير مصرح' });
  try {
    const row = await db.createInviteLink(req.userId);
    res.json({ token: row.token });
  } catch (e) {
    res.status(500).json({ error: e.message || 'فشل' });
  }
});

router.get('/check-invite/:token', async (req, res) => {
  try {
    const token = req.params.token;
    if (!token) return res.status(400).json({ valid: false, error: 'رابط غير صالح' });
    const link = await db.getInviteLink(token);
    if (!link) return res.json({ valid: false, used: false, error: 'رابط غير صالح' });
    if (link.used_at) return res.json({ valid: false, used: true, error: 'تم استخدام هذا الرابط مسبقاً' });
    res.json({ valid: true, used: false });
  } catch (e) {
    res.status(500).json({ valid: false, error: e.message });
  }
});

router.post('/consume-invite/:token', async (req, res) => {
  try {
    const token = req.params.token;
    if (!token) return res.status(400).json({ ok: false, error: 'رابط غير صالح' });
    const link = await db.getInviteLink(token);
    if (!link) return res.json({ ok: false, error: 'رابط غير صالح' });
    if (link.used_at) return res.json({ ok: false, error: 'الرابط مُستهلَك مسبقاً' });
    const ok = await db.consumeInviteLink(token);
    if (!ok) return res.json({ ok: false, error: 'فشل' });
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

module.exports = router;
