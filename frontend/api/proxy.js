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

  const doFetch = () => {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), 30000);
    return fetch(url, {
      method: String(method).toUpperCase(),
      headers: h,
      body: body != null ? JSON.stringify(body) : undefined,
      signal: ctrl.signal
    }).finally(() => clearTimeout(t));
  };
  let lastErr;
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const r = await doFetch();
      const text = await r.text();
      let data = {};
      try { data = text ? JSON.parse(text) : {}; } catch (_) {}
      return res.status(r.status).json(data);
    } catch (e) {
      lastErr = e;
      if (attempt < 2) await new Promise((r) => setTimeout(r, 2000));
    }
  }
  res.status(500).json({ error: lastErr?.message || 'فشل الاتصال بالسيرفر. جرّب مرة أخرى.' });
}
