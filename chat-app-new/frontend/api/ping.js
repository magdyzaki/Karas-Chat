/** للتشخيص فقط — لا يستدعي أي شيء خارجي */
export default async function handler(req, res) {
  res.json({ ok: true, t: Date.now(), msg: 'Vercel API يعمل' });
}
