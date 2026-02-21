/** Proxy لطلب استهلاك رابط الدعوة — يتجاوز أي حظر لشبكة Render */
const BACKEND = 'https://karas-chat-backend.onrender.com';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (!['POST', 'GET'].includes(req.method)) return res.status(405).json({ ok: false, error: 'POST أو GET فقط' });
  const token = req.body?.token ?? req.query?.token;
  if (!token) return res.status(400).json({ ok: false, error: 'رابط غير صالح' });
  try {
    const r = await fetch(`${BACKEND}/api/consume-invite/${encodeURIComponent(token)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const data = await r.json().catch(() => ({}));
    res.status(r.ok ? 200 : 400).json(data);
  } catch (e) {
    res.status(500).json({ ok: false, error: e?.message || 'فشل الاتصال بالسيرفر' });
  }
}
