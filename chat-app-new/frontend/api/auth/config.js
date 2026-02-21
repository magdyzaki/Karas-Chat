/** Proxy لـ GET /api/auth/config — يتجاوز Failed to fetch مع Render */
const BACKEND = 'https://karas-chat-backend.onrender.com';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'GET') return res.status(405).json({ error: 'GET فقط' });
  try {
    const r = await fetch(`${BACKEND}/api/auth/config`, { method: 'GET' });
    const data = await r.json().catch(() => ({}));
    res.status(r.ok ? 200 : 400).json(data);
  } catch (e) {
    res.status(500).json({ error: e?.message || 'فشل الاتصال بالسيرفر' });
  }
}
