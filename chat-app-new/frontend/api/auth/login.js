/** Proxy لـ POST /api/auth/login — يتجاوز Failed to fetch مع Render */
const BACKEND = 'https://karas-chat-backend.onrender.com';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'POST فقط' });
  const body = req.body || {};
  try {
    const r = await fetch(`${BACKEND}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(req.headers.authorization ? { Authorization: req.headers.authorization } : {})
      },
      body: JSON.stringify(body)
    });
    const data = await r.json().catch(() => ({}));
    res.status(r.status).json(data);
  } catch (e) {
    res.status(500).json({ error: e?.message || 'فشل الاتصال بالسيرفر' });
  }
}
