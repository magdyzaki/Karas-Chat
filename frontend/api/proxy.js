/**
 * Proxy لجميع طلبات الـ API إلى Render — يتجاوز Failed to fetch
 * POST مع body: { path, method?, body?, headers? }
 */
const BACKEND = 'https://karas-chat-backend.onrender.com';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'POST only' });

  const { path, method = 'GET', body, headers: clientHeaders } = req.body || {};
  if (!path || typeof path !== 'string') return res.status(400).json({ error: 'path required' });

  const url = `${BACKEND}${path.startsWith('/') ? path : '/' + path}`;
  const h = { 'Content-Type': 'application/json' };
  if (clientHeaders?.Authorization) h.Authorization = clientHeaders.Authorization;

  try {
    const r = await fetch(url, {
      method: String(method).toUpperCase(),
      headers: h,
      body: body != null ? JSON.stringify(body) : undefined
    });
    const text = await r.text();
    let data = {};
    try { data = text ? JSON.parse(text) : {}; } catch (_) {}
    res.status(r.status).json(data);
  } catch (e) {
    res.status(500).json({ error: e?.message || 'فشل الاتصال بالسيرفر' });
  }
}
