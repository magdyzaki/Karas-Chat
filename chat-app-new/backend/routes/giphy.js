import { Router } from 'express';
const router = Router();

const GIPHY_KEY = process.env.GIPHY_API_KEY || '';

router.get('/search', async (req, res) => {
  if (!GIPHY_KEY) return res.status(503).json({ error: 'GIF غير مفعّل. أضف GIPHY_API_KEY في .env' });
  const q = (req.query.q || '').trim().slice(0, 50);
  if (!q) return res.status(400).json({ error: 'أدخل كلمة بحث' });
  try {
    const url = `https://api.giphy.com/v1/gifs/search?api_key=${GIPHY_KEY}&q=${encodeURIComponent(q)}&limit=20&rating=g`;
    const r = await fetch(url);
    const data = await r.json();
    const list = (data.data || []).map((g) => ({
      id: g.id,
      url: g.images?.fixed_width?.url || g.images?.downsized?.url || g.images?.original?.url,
      title: g.title || ''
    })).filter((x) => x.url);
    res.json({ gifs: list });
  } catch (e) {
    res.status(502).json({ error: e.message || 'فشل البحث' });
  }
});

router.get('/trending', async (req, res) => {
  if (!GIPHY_KEY) return res.status(503).json({ error: 'GIF غير مفعّل' });
  try {
    const url = `https://api.giphy.com/v1/gifs/trending?api_key=${GIPHY_KEY}&limit=20&rating=g`;
    const r = await fetch(url);
    const data = await r.json();
    const list = (data.data || []).map((g) => ({
      id: g.id,
      url: g.images?.fixed_width?.url || g.images?.downsized?.url || g.images?.original?.url,
      title: g.title || ''
    })).filter((x) => x.url);
    res.json({ gifs: list });
  } catch (e) {
    res.status(502).json({ error: e.message || 'فشل التحميل' });
  }
});

export default router;
