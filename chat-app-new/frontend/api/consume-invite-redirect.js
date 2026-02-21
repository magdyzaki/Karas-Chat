/**
 * استهلاك الرابط على السيرفر ثم إعادة التوجيه.
 * يُستخدم عند فتح الرابط مباشرة — لا حاجة لـ fetch من المتصفح (يتجاوز "Failed to fetch").
 */
const BACKEND = 'https://karas-chat-backend.onrender.com';

function getBaseUrl(req) {
  const h = req.headers;
  const host = h['x-forwarded-host'] || h.host || 'karas-chat.vercel.app';
  const proto = h['x-forwarded-proto'] || (h['x-forwarded-ssl'] === 'on' ? 'https' : 'http');
  return `${proto}://${host}`;
}

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.redirect(302, getBaseUrl(req) + '/');
  }
  const token = req.query?.token;
  if (!token) {
    return res.redirect(302, getBaseUrl(req) + '/?invite_error=رابط+غير+صالح');
  }
  try {
    const r = await fetch(`${BACKEND}/api/consume-invite/${encodeURIComponent(token)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const data = await r.json().catch(() => ({}));
    const base = getBaseUrl(req);
    if (data.ok) {
      return res.redirect(302, `${base}/?invite=${encodeURIComponent(token)}&consumed=1`);
    }
    const err = encodeURIComponent(data.error || 'الرابط مُستهلَك أو غير صالح');
    return res.redirect(302, `${base}/?invite_error=${err}`);
  } catch (e) {
    const err = encodeURIComponent(e?.message || 'فشل الاتصال');
    return res.redirect(302, getBaseUrl(req) + `/?invite_error=${err}`);
  }
}
