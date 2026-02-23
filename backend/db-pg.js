/**
 * تخزين بيانات الشات في PostgreSQL — الرسائل والمستخدمين والمحادثات تدوم بعد إعادة تشغيل Render.
 * يُستخدم عند ضبط DATABASE_URL.
 */
let pool = null;

function getPoolSync() {
  return pool;
}

async function getPool() {
  if (pool) return pool;
  const url = process.env.DATABASE_URL;
  if (!url) return null;
  try {
    const { default: pg } = await import('pg');
    const { Pool } = pg;
    pool = new Pool({ connectionString: url, ssl: url.includes('render.com') ? { rejectUnauthorized: false } : undefined });

    await pool.query(`
      CREATE TABLE IF NOT EXISTS chat_users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255),
        phone VARCHAR(20),
        password_hash VARCHAR(255) NOT NULL,
        name VARCHAR(255) NOT NULL DEFAULT '',
        avatar_url VARCHAR(500),
        verified BOOLEAN DEFAULT false,
        verification_code VARCHAR(20),
        verification_expires TIMESTAMPTZ,
        reset_code VARCHAR(20),
        reset_expires TIMESTAMPTZ,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        last_seen_at TIMESTAMPTZ
      )
    `);
    await pool.query(`CREATE INDEX IF NOT EXISTS idx_users_email ON chat_users(email)`);
    await pool.query(`CREATE INDEX IF NOT EXISTS idx_users_phone ON chat_users(phone)`);

    await pool.query(`
      CREATE TABLE IF NOT EXISTS chat_conversations (
        id SERIAL PRIMARY KEY,
        type VARCHAR(20) NOT NULL DEFAULT 'direct',
        name VARCHAR(255),
        created_at TIMESTAMPTZ DEFAULT NOW(),
        created_by INTEGER REFERENCES chat_users(id)
      )
    `);

    await pool.query(`
      CREATE TABLE IF NOT EXISTS chat_conversation_members (
        conversation_id INTEGER NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,
        user_id INTEGER NOT NULL REFERENCES chat_users(id),
        joined_at TIMESTAMPTZ DEFAULT NOW(),
        PRIMARY KEY (conversation_id, user_id)
      )
    `);

    await pool.query(`
      CREATE TABLE IF NOT EXISTS chat_messages (
        id SERIAL PRIMARY KEY,
        conversation_id INTEGER NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,
        sender_id INTEGER NOT NULL REFERENCES chat_users(id),
        type VARCHAR(20) DEFAULT 'text',
        content TEXT NOT NULL DEFAULT '',
        file_name VARCHAR(255),
        reply_to_id INTEGER,
        reply_to_snippet VARCHAR(100),
        encrypted BOOLEAN DEFAULT false,
        iv TEXT,
        deleted_for_everyone BOOLEAN DEFAULT false,
        deleted_for_me INTEGER[],
        created_at TIMESTAMPTZ DEFAULT NOW()
      )
    `);
    await pool.query(`CREATE INDEX IF NOT EXISTS idx_messages_conv ON chat_messages(conversation_id)`);

    await pool.query(`
      CREATE TABLE IF NOT EXISTS chat_blocked_users (
        user_id INTEGER PRIMARY KEY REFERENCES chat_users(id)
      )
    `);

    await pool.query(`
      CREATE TABLE IF NOT EXISTS chat_user_conversation_prefs (
        user_id INTEGER NOT NULL,
        conversation_id INTEGER NOT NULL,
        muted BOOLEAN DEFAULT false,
        archived BOOLEAN DEFAULT false,
        disappearing_after INTEGER,
        PRIMARY KEY (user_id, conversation_id)
      )
    `);

    await pool.query(`
      CREATE TABLE IF NOT EXISTS chat_conversation_reads (
        conversation_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        last_message_id INTEGER,
        last_read_at TIMESTAMPTZ DEFAULT NOW(),
        PRIMARY KEY (conversation_id, user_id)
      )
    `);

    await pool.query(`
      CREATE TABLE IF NOT EXISTS chat_message_reactions (
        message_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        emoji VARCHAR(20) NOT NULL,
        PRIMARY KEY (message_id, user_id)
      )
    `);

    await pool.query(`
      CREATE TABLE IF NOT EXISTS chat_poll_votes (
        message_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        option_index INTEGER NOT NULL,
        PRIMARY KEY (message_id, user_id)
      )
    `);

    return pool;
  } catch (e) {
    console.error('db-pg init error:', e.message);
    return null;
  }
}

function normalizePhone(input) {
  const digits = (input || '').replace(/\D/g, '');
  return digits.length >= 10 ? digits : '';
}

export async function pgFindUserById(id) {
  const p = await getPool();
  if (!p) return null;
  const r = await p.query('SELECT * FROM chat_users WHERE id = $1', [Number(id)]);
  if (!r.rows.length) return null;
  const row = r.rows[0];
  return {
    id: row.id,
    email: row.email,
    phone: row.phone,
    password_hash: row.password_hash,
    name: row.name || '',
    avatar_url: row.avatar_url,
    verified: !!row.verified,
    verification_code: row.verification_code,
    verification_expires: row.verification_expires,
    reset_code: row.reset_code,
    reset_expires: row.reset_expires,
    created_at: row.created_at,
    last_seen_at: row.last_seen_at
  };
}

export async function pgFindUserByEmail(email) {
  const p = await getPool();
  if (!p) return null;
  const e = (email || '').toLowerCase().trim();
  if (!e) return null;
  const r = await p.query('SELECT * FROM chat_users WHERE email = $1', [e]);
  if (!r.rows.length) return null;
  const row = r.rows[0];
  return { id: row.id, email: row.email, phone: row.phone, password_hash: row.password_hash, name: row.name || '', avatar_url: row.avatar_url, verified: !!row.verified, verification_code: row.verification_code, verification_expires: row.verification_expires, reset_code: row.reset_code, reset_expires: row.reset_expires, created_at: row.created_at, last_seen_at: row.last_seen_at };
}

export async function pgFindUserByPhone(phone) {
  const p = await getPool();
  if (!p) return null;
  const ph = normalizePhone(phone);
  if (!ph) return null;
  const r = await p.query('SELECT * FROM chat_users WHERE phone = $1', [ph]);
  if (!r.rows.length) return null;
  const row = r.rows[0];
  return { id: row.id, email: row.email, phone: row.phone, password_hash: row.password_hash, name: row.name || '', avatar_url: row.avatar_url, verified: !!row.verified, verification_code: row.verification_code, verification_expires: row.verification_expires, reset_code: row.reset_code, reset_expires: row.reset_expires, created_at: row.created_at, last_seen_at: row.last_seen_at };
}

export async function pgAddUser({ email, password_hash, name, phone, verification_code, verification_expires }) {
  const p = await getPool();
  if (!p) return null;
  const r = await p.query(
    `INSERT INTO chat_users (email, phone, password_hash, name, verification_code, verification_expires)
     VALUES ($1, $2, $3, $4, $5, $6) RETURNING *`,
    [(email || '').toLowerCase().trim() || null, phone ? normalizePhone(phone) || null : null, password_hash, (name || '').trim(), verification_code || null, verification_expires || null]
  );
  const row = r.rows[0];
  return { id: row.id, email: row.email, phone: row.phone, password_hash: row.password_hash, name: row.name || '', avatar_url: null, verified: false, verification_code: row.verification_code, verification_expires: row.verification_expires, created_at: row.created_at, last_seen_at: null };
}

export async function pgIsUserBlocked(userId) {
  const p = await getPool();
  if (!p) return false;
  const r = await p.query('SELECT 1 FROM chat_blocked_users WHERE user_id = $1', [Number(userId)]);
  return r.rows.length > 0;
}

export async function pgSetUserVerified(userId, verified) {
  const p = await getPool();
  if (!p) return false;
  await p.query('UPDATE chat_users SET verified = $1, verification_code = NULL, verification_expires = NULL WHERE id = $2', [!!verified, Number(userId)]);
  return true;
}

export async function pgUpdateUserProfile(userId, { name, avatar_url }) {
  const p = await getPool();
  if (!p) return null;
  const updates = [];
  const vals = [];
  let i = 1;
  if (name !== undefined) { updates.push(`name = $${i++}`); vals.push((name || '').trim()); }
  if (avatar_url !== undefined) { updates.push(`avatar_url = $${i++}`); vals.push(avatar_url); }
  if (updates.length === 0) return await pgFindUserById(userId);
  vals.push(Number(userId));
  const r = await p.query(`UPDATE chat_users SET ${updates.join(', ')} WHERE id = $${i} RETURNING *`, vals);
  if (!r.rows.length) return null;
  const row = r.rows[0];
  return { id: row.id, email: row.email, phone: row.phone, name: row.name || '', avatar_url: row.avatar_url };
}

export async function pgSetUserLastSeen(userId) {
  const p = await getPool();
  if (!p) return;
  await p.query('UPDATE chat_users SET last_seen_at = NOW() WHERE id = $1', [Number(userId)]);
}

export async function pgGetConversationPref(userId, conversationId) {
  const p = await getPool();
  if (!p) return { muted: false, archived: false, disappearing_after: null };
  const r = await p.query('SELECT * FROM chat_user_conversation_prefs WHERE user_id = $1 AND conversation_id = $2', [Number(userId), Number(conversationId)]);
  if (!r.rows.length) return { muted: false, archived: false, disappearing_after: null };
  const row = r.rows[0];
  return { muted: !!row.muted, archived: !!row.archived, disappearing_after: row.disappearing_after };
}

export async function pgGetMemberIds(conversationId) {
  const p = await getPool();
  if (!p) return [];
  const r = await p.query('SELECT user_id FROM chat_conversation_members WHERE conversation_id = $1', [Number(conversationId)]);
  return r.rows.map((x) => x.user_id);
}

export async function pgGetOrCreateDirectConversation(userId1, userId2) {
  const p = await getPool();
  if (!p) return null;
  const id1 = Number(userId1);
  const id2 = Number(userId2);
  const r = await p.query(`
    SELECT c.* FROM chat_conversations c
    JOIN chat_conversation_members m1 ON m1.conversation_id = c.id AND m1.user_id = $1
    JOIN chat_conversation_members m2 ON m2.conversation_id = c.id AND m2.user_id = $2
    WHERE c.type = 'direct'
  `, [id1, id2]);
  if (r.rows.length) return { conversation: r.rows[0], created: false };
  const ins = await p.query('INSERT INTO chat_conversations (type, created_by) VALUES ($1, $2) RETURNING *', ['direct', id1]);
  const conv = ins.rows[0];
  await p.query('INSERT INTO chat_conversation_members (conversation_id, user_id) VALUES ($1, $2), ($1, $3)', [conv.id, id1, id2]);
  return { conversation: conv, created: true };
}

export async function pgCreateGroupConversation(creatorId, name, memberIds) {
  const p = await getPool();
  if (!p) return null;
  const allIds = [Number(creatorId), ...(memberIds || []).map(Number).filter(Boolean)];
  const unique = [...new Set(allIds)];
  const ins = await p.query('INSERT INTO chat_conversations (type, name, created_by) VALUES ($1, $2, $3) RETURNING *', ['group', name || '', Number(creatorId)]);
  const conv = ins.rows[0];
  for (const uid of unique) {
    await p.query('INSERT INTO chat_conversation_members (conversation_id, user_id) VALUES ($1, $2)', [conv.id, uid]);
  }
  return conv;
}

export async function pgGetConversationByIdAndUser(conversationId, userId) {
  const p = await getPool();
  if (!p) return null;
  const r = await p.query(`
    SELECT c.* FROM chat_conversations c
    JOIN chat_conversation_members m ON m.conversation_id = c.id AND m.user_id = $2
    WHERE c.id = $1
  `, [Number(conversationId), Number(userId)]);
  if (!r.rows.length) return null;
  const conv = r.rows[0];
  const members = await pgGetMemberIds(conv.id);
  return { ...conv, members };
}

export async function pgGetConversationsForUser(userId) {
  const p = await getPool();
  if (!p) return [];
  const r = await p.query(`
    SELECT c.* FROM chat_conversations c
    JOIN chat_conversation_members m ON m.conversation_id = c.id AND m.user_id = $1
    ORDER BY c.id DESC
  `, [Number(userId)]);
  const result = [];
  for (const c of r.rows) {
    const members = await pgGetMemberIds(c.id);
    result.push({ ...c, members });
  }
  return result;
}

export async function pgAddMessage({ conversation_id, sender_id, type, content, file_name, reply_to_id, reply_to_snippet, encrypted, iv }) {
  const p = await getPool();
  if (!p) return null;
  const r = await p.query(
    `INSERT INTO chat_messages (conversation_id, sender_id, type, content, file_name, reply_to_id, reply_to_snippet, encrypted, iv)
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) RETURNING *`,
    [Number(conversation_id), Number(sender_id), type || 'text', content || '', file_name || null, reply_to_id ? Number(reply_to_id) : null, (reply_to_snippet && String(reply_to_snippet).slice(0, 100)) || null, !!encrypted, iv || null]
  );
  const row = r.rows[0];
  return {
    id: row.id,
    conversation_id: row.conversation_id,
    sender_id: row.sender_id,
    type: row.type,
    content: row.content,
    file_name: row.file_name,
    reply_to_id: row.reply_to_id,
    reply_to_snippet: row.reply_to_snippet,
    encrypted: !!row.encrypted,
    iv: row.iv,
    created_at: row.created_at,
    deleted_for_everyone: !!row.deleted_for_everyone,
    deleted_for_me: row.deleted_for_me || []
  };
}

export async function pgGetMessagesForConversation(conversationId, limit = 100, beforeId = null, currentUserId = null) {
  const p = await getPool();
  if (!p) return [];
  const prefs = await pgGetConversationPref(currentUserId, conversationId);
  const disappearingSec = prefs.disappearing_after;
  let sql = 'SELECT * FROM chat_messages WHERE conversation_id = $1';
  const params = [Number(conversationId)];
  if (disappearingSec) {
    sql += ` AND created_at >= NOW() - INTERVAL '1 second' * $${params.length + 1}`;
    params.push(disappearingSec);
  }
  if (beforeId) {
    sql += ` AND id < $${params.length + 1}`;
    params.push(Number(beforeId));
  }
  sql += ` ORDER BY created_at DESC LIMIT $${params.length + 1}`;
  params.push(Math.min(limit, 200));
  const r = await p.query(sql, params);
  let list = r.rows.reverse().map((m) => ({
    id: m.id,
    conversation_id: m.conversation_id,
    sender_id: m.sender_id,
    type: m.type,
    content: m.content,
    file_name: m.file_name,
    reply_to_id: m.reply_to_id,
    reply_to_snippet: m.reply_to_snippet,
    encrypted: !!m.encrypted,
    iv: m.iv,
    created_at: m.created_at,
    deleted_for_everyone: !!m.deleted_for_everyone,
    deleted_for_me: m.deleted_for_me || []
  }));
  const uid = currentUserId != null ? Number(currentUserId) : null;
  return list.map((m) => {
    const deletedForMe = Array.isArray(m.deleted_for_me) && uid != null && m.deleted_for_me.includes(uid);
    if (m.deleted_for_everyone || deletedForMe) {
      return { ...m, content: '', file_name: null, type: 'text', deleted: true };
    }
    return m;
  });
}

export async function pgSetConversationRead(conversationId, userId, lastMessageId) {
  const p = await getPool();
  if (!p) return null;
  await p.query(
    `INSERT INTO chat_conversation_reads (conversation_id, user_id, last_message_id, last_read_at)
     VALUES ($1, $2, $3, NOW())
     ON CONFLICT (conversation_id, user_id) DO UPDATE SET last_message_id = $3, last_read_at = NOW()`,
    [Number(conversationId), Number(userId), lastMessageId != null ? Number(lastMessageId) : null]
  );
  return { conversation_id: Number(conversationId), user_id: Number(userId), last_message_id: lastMessageId != null ? Number(lastMessageId) : null };
}

export async function pgGetConversationReads(conversationId) {
  const p = await getPool();
  if (!p) return [];
  const r = await p.query('SELECT * FROM chat_conversation_reads WHERE conversation_id = $1', [Number(conversationId)]);
  return r.rows.map((x) => ({ user_id: x.user_id, last_message_id: x.last_message_id }));
}

export async function pgGetUserPublicKey(userId) {
  const p = await getPool();
  if (!p) return null;
  return null;
}

export async function pgDeleteMessageForMe(messageId, conversationId, userId) {
  const p = await getPool();
  if (!p) return false;
  const r = await p.query('UPDATE chat_messages SET deleted_for_me = array_append(COALESCE(deleted_for_me, ARRAY[]::integer[]), $3) WHERE id = $1 AND conversation_id = $2 AND NOT (COALESCE(deleted_for_me, ARRAY[]::integer[]) @> ARRAY[$3]) RETURNING id', [Number(messageId), Number(conversationId), Number(userId)]);
  return r.rowCount > 0;
}

export async function pgDeleteMessageForEveryone(messageId, conversationId, userId) {
  const p = await getPool();
  if (!p) return false;
  const r = await p.query(`UPDATE chat_messages SET deleted_for_everyone = true, content = '', file_name = NULL WHERE id = $1 AND conversation_id = $2 AND sender_id = $3 RETURNING id`, [Number(messageId), Number(conversationId), Number(userId)]);
  return r.rowCount > 0;
}

export async function pgAddMessageReaction(messageId, userId, emoji) {
  const p = await getPool();
  if (!p) return false;
  await p.query('INSERT INTO chat_message_reactions (message_id, user_id, emoji) VALUES ($1, $2, $3) ON CONFLICT (message_id, user_id) DO UPDATE SET emoji = $3', [Number(messageId), Number(userId), String(emoji).slice(0, 10)]);
  return true;
}

export async function pgRemoveMessageReaction(messageId, userId) {
  const p = await getPool();
  if (!p) return false;
  await p.query('DELETE FROM chat_message_reactions WHERE message_id = $1 AND user_id = $2', [Number(messageId), Number(userId)]);
  return true;
}

export async function pgGetMessageReactions(conversationId) {
  const p = await getPool();
  if (!p) return [];
  const r = await p.query(`
    SELECT mr.* FROM chat_message_reactions mr
    JOIN chat_messages m ON m.id = mr.message_id
    WHERE m.conversation_id = $1
  `, [Number(conversationId)]);
  return r.rows.map((x) => ({ message_id: x.message_id, user_id: x.user_id, emoji: x.emoji }));
}

export async function pgGetPollVotes(conversationId) {
  const p = await getPool();
  if (!p) return [];
  const r = await p.query(`
    SELECT pv.message_id, pv.user_id, pv.option_index FROM chat_poll_votes pv
    JOIN chat_messages m ON m.id = pv.message_id
    WHERE m.conversation_id = $1
  `, [Number(conversationId)]);
  return r.rows.map((x) => ({ message_id: x.message_id, user_id: x.user_id, option_index: x.option_index }));
}

export async function pgIsMessageInConversation(messageId, conversationId) {
  const p = await getPool();
  if (!p) return false;
  const r = await p.query('SELECT 1 FROM chat_messages WHERE id = $1 AND conversation_id = $2', [Number(messageId), Number(conversationId)]);
  return r.rows.length > 0;
}

export async function pgAddPollVote(messageId, conversationId, userId, optionIndex) {
  const p = await getPool();
  if (!p) return false;
  try {
    await p.query('INSERT INTO chat_poll_votes (message_id, user_id, option_index) VALUES ($1, $2, $3) ON CONFLICT (message_id, user_id) DO UPDATE SET option_index = $3', [Number(messageId), Number(userId), Number(optionIndex)]);
    return true;
  } catch (_) {
    return false;
  }
}

export async function pgGetUnverifiedUsers() {
  const p = await getPool();
  if (!p) return [];
  const r = await p.query('SELECT id, email, phone, name, created_at FROM chat_users WHERE verified = false');
  return r.rows.map((x) => ({ id: x.id, email: x.email, phone: x.phone, name: x.name, created_at: x.created_at }));
}

export async function pgFindUsersByPhones(phoneNumbers, excludeUserId = null) {
  const p = await getPool();
  if (!p) return [];
  const normalizedSet = new Set();
  for (const raw of phoneNumbers || []) {
    const ph = normalizePhone(raw);
    if (ph) normalizedSet.add(ph);
  }
  if (!normalizedSet.size) return [];
  const exclude = excludeUserId != null ? Number(excludeUserId) : null;
  const r = await p.query('SELECT id, email, phone, name, avatar_url FROM chat_users WHERE phone IS NOT NULL');
  return r.rows
    .filter((u) => normalizedSet.has(normalizePhone(u.phone)) && (!exclude || u.id !== exclude))
    .map((u) => ({ id: u.id, email: u.email, phone: u.phone, name: u.name, avatar_url: u.avatar_url || null }));
}

export async function pgListUsersExcept(userId) {
  const p = await getPool();
  if (!p) return [];
  const r = await p.query('SELECT id, email, phone, name, avatar_url FROM chat_users WHERE id != $1', [Number(userId)]);
  return r.rows.map((u) => ({ id: u.id, email: u.email, phone: u.phone, name: u.name, avatar_url: u.avatar_url }));
}

export async function pgGetArchivedConversationIds(userId) {
  const p = await getPool();
  if (!p) return [];
  const r = await p.query('SELECT conversation_id FROM chat_user_conversation_prefs WHERE user_id = $1 AND archived = true', [Number(userId)]);
  return r.rows.map((x) => x.conversation_id);
}
