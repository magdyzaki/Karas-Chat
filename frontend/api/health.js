/** Proxy لإيقاظ سيرفر Render عبر Vercel */
const BACKEND = 'https://karas-chat-backend.onrender.com';

export default async function handler(req, res) {
  try {
    await fetch(`${BACKEND}/api/health`);
  } catch (_) {}
  res.json({ ok: true });
}
