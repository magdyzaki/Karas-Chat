/**
 * تخزين روابط الدعوة في PostgreSQL — يدوم بعد إعادة تشغيل Render.
 * يُستخدم عند ضبط DATABASE_URL (مثل Postgres المجاني من Render).
 */
let pool = null;

async function getPool() {
  if (pool) return pool;
  const url = process.env.DATABASE_URL;
  if (!url) return null;
  try {
    const { default: pg } = await import('pg');
    const { Pool } = pg;
    pool = new Pool({ connectionString: url, ssl: url.includes('render.com') ? { rejectUnauthorized: false } : undefined });
    await pool.query(`
      CREATE TABLE IF NOT EXISTS invite_links (
        token VARCHAR(64) PRIMARY KEY,
        created_by INTEGER NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        used_at TIMESTAMPTZ
      )
    `);
    return pool;
  } catch (e) {
    console.error('invite-pg init:', e.message);
    return null;
  }
}

export async function pgCreateInviteLink(userId) {
  const p = await getPool();
  if (!p) return null;
  const token = 'i_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 10);
  await p.query(
    'INSERT INTO invite_links (token, created_by) VALUES ($1, $2)',
    [token, Number(userId)]
  );
  return { token, created_by: Number(userId), created_at: new Date().toISOString(), used_at: null };
}

export async function pgGetInviteLink(token) {
  const p = await getPool();
  if (!p) return null;
  const r = await p.query('SELECT * FROM invite_links WHERE token = $1', [String(token).trim()]);
  if (!r.rows.length) return null;
  const row = r.rows[0];
  return { token: row.token, created_by: row.created_by, created_at: row.created_at, used_at: row.used_at };
}

export async function pgConsumeInviteLink(token) {
  const p = await getPool();
  if (!p) return false;
  const r = await p.query(
    "UPDATE invite_links SET used_at = NOW() WHERE token = $1 AND used_at IS NULL RETURNING token",
    [String(token).trim()]
  );
  return r.rowCount > 0;
}
