import { Router } from 'express';
import { db } from '../db.js';

const router = Router();
const STORY_MAX_AGE_MS = 24 * 60 * 60 * 1000;

router.get('/', (req, res) => {
  const feed = db.getStoriesForFeed(req.userId);
  const usersById = {};
  const userIds = [...new Set(Object.keys(feed).map(Number))];
  userIds.forEach((id) => {
    const u = db.findUserById(id);
    if (u) usersById[id] = { id: u.id, name: u.name, email: u.email, phone: u.phone, avatar_url: u.avatar_url };
  });
  res.json({
    feed: Object.entries(feed).map(([uid, stories]) => ({
      userId: Number(uid),
      user: usersById[uid] || { id: Number(uid), name: '' },
      stories: stories.map((s) => ({ id: s.id, type: s.type, content: s.content, file_name: s.file_name, created_at: s.created_at }))
    }))
  });
});

router.post('/', (req, res) => {
  const { type, content, file_name } = req.body || {};
  if (!type || (!content && type === 'text')) return res.status(400).json({ error: 'النوع والمحتوى مطلوبان' });
  if (!['text', 'image', 'video'].includes(type)) return res.status(400).json({ error: 'نوع غير مدعوم' });
  const story = db.addStory({ user_id: req.userId, type, content: content || '', file_name: file_name || null });
  const io = req.app.get('io');
  if (io) io.emit('new_story', { userId: req.userId, story });
  res.json(story);
});

export default router;
