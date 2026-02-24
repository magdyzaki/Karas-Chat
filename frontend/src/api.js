const API_BASE = import.meta.env.VITE_API_URL || '';

/** عند الويب: استخدم proxy على Vercel لتجاوز Failed to fetch مع Render */
const useApiProxy = () => typeof window !== 'undefined' && window.location?.hostname !== 'localhost';
const useAuthProxy = useApiProxy;
const authBase = () => (useAuthProxy() ? '' : API_BASE);

/** طلب API — عند الويب يمر عبر proxy لتجاوز CORS و Render cold start */
async function apiFetch(path, opts = {}) {
  const url = (API_BASE || '') + (path.startsWith('/') ? path : '/' + path);
  if (useApiProxy()) {
    const pathStr = path.startsWith('/') ? path : '/' + path;
    let body = opts.body;
    if (typeof body === 'string') try { body = JSON.parse(body); } catch (_) {}
    const r = await fetch('/api/proxy', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        path: pathStr,
        method: opts.method || 'GET',
        body,
        headers: opts.headers || {}
      })
    });
    return r;
  }
  return fetch(url, opts);
}

/** يستخدم للطلبات الأولى عند استيقاظ السيرفر (Render cold start) */
async function fetchWithRetry(url, opts = {}, { retries = 3, timeoutMs = 90000 } = {}) {
  for (let i = 0; i < retries; i++) {
    const ctrl = new AbortController();
    const id = setTimeout(() => ctrl.abort(), timeoutMs);
    try {
      const res = await fetch(url, { ...opts, signal: ctrl.signal });
      clearTimeout(id);
      return res;
    } catch (e) {
      clearTimeout(id);
      if (i === retries - 1) throw e;
      await new Promise((r) => setTimeout(r, 2000));
    }
  }
  throw new Error('فشل الاتصال بعد عدة محاولات');
}

/** إيقاظ السيرفر عند فتح صفحة الدعوة — عدة طلبات لتسريع الاستيقاظ */
export function prewakeBackend() {
  const useProxy = typeof window !== 'undefined' && window.location?.hostname !== 'localhost';
  const url = useProxy ? '/api/health' : `${API_BASE}/api/health`;
  [0, 2000, 4000].forEach((d) => setTimeout(() => fetch(url).catch(() => {}), d));
}

export async function searchGifs(q) {
  const res = await apiFetch(`/api/giphy/search?q=${encodeURIComponent(q || '')}`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل بحث GIF');
  return data.gifs || [];
}

export async function getTrendingGifs() {
  const res = await apiFetch(`/api/giphy/trending`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل تحميل GIF');
  return data.gifs || [];
}

function getToken() {
  return localStorage.getItem('chat_token');
}

function headers() {
  const t = getToken();
  return {
    'Content-Type': 'application/json',
    ...(t ? { Authorization: `Bearer ${t}` } : {})
  };
}

export async function getAuthConfig() {
  const base = authBase();
  const res = await fetch(`${base}/api/auth/config`);
  const data = await res.json().catch(() => ({}));
  return data;
}

export async function register(emailOrPhone, password, name = '', inviteToken = '') {
  const base = authBase();
  const res = await fetch(`${base}/api/auth/register`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ emailOrPhone, password, name, inviteToken: inviteToken || undefined })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل التسجيل');
  return data;
}

export async function login(emailOrPhone, password) {
  const base = authBase();
  const res = await fetch(`${base}/api/auth/login`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ emailOrPhone, password })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل تسجيل الدخول');
  return data;
}

export async function verify(emailOrPhone, code) {
  const base = authBase();
  const res = await fetch(`${base}/api/auth/verify`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ emailOrPhone, code })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل التحقق');
  return data;
}

export async function forgotPassword(emailOrPhone) {
  const base = authBase();
  const res = await fetch(`${base}/api/auth/forgot-password`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ emailOrPhone })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل إرسال رمز الاستعادة');
  return data;
}

export async function getDevLastCode(emailOrPhone) {
  const q = encodeURIComponent(String(emailOrPhone || '').trim());
  const res = await apiFetch(`/api/dev/last-code?q=${q}`);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل');
  return data;
}

export async function resetPassword(emailOrPhone, code, newPassword) {
  const base = authBase();
  const res = await fetch(`${base}/api/auth/reset-password`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ emailOrPhone, code, newPassword })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل تغيير كلمة المرور');
  return data;
}

export async function checkContacts(phoneNumbers) {
  const arr = Array.isArray(phoneNumbers) ? phoneNumbers : [phoneNumbers];
  const res = await apiFetch(`/api/users/check-contacts`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ phoneNumbers: arr })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل البحث');
  return data.users || [];
}

export async function getUsers() {
  const res = await apiFetch(`/api/users`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل جلب المستخدمين');
  return data.users || [];
}

export async function getAdminUsers() {
  const res = await apiFetch(`/api/admin/users`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل جلب المستخدمين');
  return data.users || [];
}

export async function getConversations() {
  const res = await apiFetch(`/api/conversations`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل جلب المحادثات');
  return data.conversations || [];
}

export async function getConversation(id) {
  const res = await apiFetch(`/api/conversations/${id}`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل جلب المحادثة');
  return data;
}

export async function sendMessage(conversationId, { type = 'text', content, file_name, reply_to_id, reply_to_snippet, encrypted, iv }) {
  const opts = { method: 'POST', headers: headers(), body: JSON.stringify({ type, content, file_name, reply_to_id, reply_to_snippet, encrypted, iv }) };
  let lastErr;
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const res = await apiFetch(`/api/conversations/${conversationId}/messages`, opts);
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || 'فشل إرسال الرسالة');
      return data.message;
    } catch (e) {
      lastErr = e;
      if (attempt < 2) await new Promise((r) => setTimeout(r, 1500));
    }
  }
  throw lastErr;
}

export async function getMessages(conversationId, limit = 100, before = null) {
  let path = `/api/conversations/${conversationId}/messages?limit=${limit}`;
  if (before) path += `&before=${before}`;
  const res = await apiFetch(path, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل جلب الرسائل');
  return { messages: data.messages || [], readReceipts: data.readReceipts || [], reactions: data.reactions || [], pollVotes: data.pollVotes || [] };
}

export async function muteConversation(conversationId) {
  const res = await apiFetch(`/api/conversations/${conversationId}/mute`, { method: 'PATCH', headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل كتم المحادثة');
  return data;
}

export async function unmuteConversation(conversationId) {
  const res = await apiFetch(`/api/conversations/${conversationId}/unmute`, { method: 'PATCH', headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل إلغاء كتم المحادثة');
  return data;
}

export async function archiveConversation(conversationId) {
  const res = await apiFetch(`/api/conversations/${conversationId}/archive`, { method: 'PATCH', headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل أرشفة المحادثة');
  return data;
}

export async function unarchiveConversation(conversationId) {
  const res = await apiFetch(`/api/conversations/${conversationId}/unarchive`, { method: 'PATCH', headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل إلغاء أرشفة المحادثة');
  return data;
}

export async function getStories() {
  const res = await apiFetch(`/api/stories`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل جلب القصص');
  return data.feed || [];
}

export async function createStory(type, content, file_name = null) {
  const res = await apiFetch(`/api/stories`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ type, content, file_name })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل نشر القصة');
  return data;
}

export async function setDisappearing(conversationId, seconds) {
  const res = await apiFetch(`/api/conversations/${conversationId}/disappearing`, {
    method: 'PATCH',
    headers: headers(),
    body: JSON.stringify({ seconds })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل تحديد الرسائل المؤقتة');
  return data;
}

export async function votePoll(conversationId, messageId, optionIndex) {
  const res = await apiFetch(`/api/conversations/${conversationId}/messages/${messageId}/vote`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ optionIndex })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل التصويت');
  return data;
}

export async function exportBackup() {
  const res = await apiFetch(`/api/backup/export`, { headers: headers() });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || 'فشل تصدير النسخة الاحتياطية');
  }
  const blob = await res.blob();
  return blob;
}

export async function forwardMessage(targetConversationId, fromConversationId, messageId) {
  const res = await apiFetch(`/api/conversations/${targetConversationId}/forward`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ fromConversationId, messageId })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل إعادة التوجيه');
  return data;
}

export async function createDirectConversation(otherUserId) {
  const res = await apiFetch(`/api/conversations/direct`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ otherUserId })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل إنشاء المحادثة');
  return data;
}

export async function createGroupConversation(name, memberIds) {
  const res = await apiFetch(`/api/conversations/group`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ name, memberIds })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل إنشاء المجموعة');
  return data;
}

export async function addMemberToGroup(conversationId, targetUserId) {
  const res = await apiFetch(`/api/conversations/${conversationId}/add-member`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ targetUserId })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل إضافة العضو');
  return data;
}

export async function removeMemberFromGroup(conversationId, targetUserId) {
  const res = await apiFetch(`/api/conversations/${conversationId}/remove-member`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ targetUserId })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل طرد العضو');
  return data;
}

export async function getBroadcastLists() {
  const res = await apiFetch(`/api/broadcast`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل جلب القوائم');
  return data.lists || [];
}

export async function createBroadcastList(name, recipientIds) {
  const res = await apiFetch(`/api/broadcast`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ name, recipientIds })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل إنشاء القائمة');
  return data;
}

export async function updateBroadcastList(id, { name, recipientIds }) {
  const res = await apiFetch(`/api/broadcast/${id}`, {
    method: 'PATCH',
    headers: headers(),
    body: JSON.stringify({ name, recipientIds })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل التحديث');
  return data;
}

export async function deleteBroadcastList(id) {
  const res = await apiFetch(`/api/broadcast/${id}`, { method: 'DELETE', headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل الحذف');
  return data;
}

export async function sendBroadcastMessage(listId, { type = 'text', content, file_name }) {
  const res = await apiFetch(`/api/broadcast/${listId}/send`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ type, content, file_name })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل الإرسال');
  return data;
}

export async function uploadFile(file) {
  const form = new FormData();
  form.append('file', file);
  const res = await apiFetch(`/api/upload`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${getToken()}` },
    body: form
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل رفع الملف');
  return data;
}

export async function consumeInviteLink(token) {
  const useProxy = typeof window !== 'undefined' && window.location?.hostname !== 'localhost';
  const tryRequest = async (url, opts) => {
    const res = await fetchWithRetry(url, opts);
    const data = await res.json().catch(() => ({}));
    return { res, data };
  };
  const tryOnce = async (url, opts) => {
    try {
      const { res, data } = await tryRequest(url, opts);
      if (res.ok || data.ok !== undefined) return data;
    } catch (_) {}
    return null;
  };
  if (useProxy) {
    const encoded = encodeURIComponent(token);
    for (let i = 0; i < 3; i++) {
      const data = await tryOnce(`/api/consume-invite?token=${encoded}`, { method: 'GET' }) ||
        await tryOnce('/api/consume-invite', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ token }) });
      if (data) return data;
      if (i < 2) await new Promise((r) => setTimeout(r, 5000));
    }
  }
  if (API_BASE) {
    const data = await tryOnce(`${API_BASE}/api/consume-invite/${encodeURIComponent(token)}`, directOpts);
    if (data) return data;
  }
  throw new Error('فشل الاتصال. تحقق من الإنترنت وحاول مرة أخرى.');
}

export async function createInviteLink() {
  const res = await apiFetch(`/api/invite-links`, { method: 'POST', headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل إنشاء الرابط');
  return data;
}

export async function blockUser(targetUserId) {
  const res = await apiFetch(`/api/admin/block-user`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ targetUserId })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل إيقاف المستخدم');
  return data;
}

export async function unblockUser(targetUserId) {
  const res = await apiFetch(`/api/admin/unblock-user`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ targetUserId })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل إلغاء الإيقاف');
  return data;
}

export async function getPendingUsers() {
  const res = await apiFetch(`/api/admin/pending-users`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل');
  return data;
}

export async function approveUser(targetUserId) {
  const res = await apiFetch(`/api/admin/approve-user`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ targetUserId })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل التفعيل');
  return data;
}

export async function getPendingCodes() {
  const res = await apiFetch(`/api/admin/pending-codes`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل');
  return data;
}

export async function getBlockedUsers() {
  const res = await apiFetch(`/api/admin/blocked-users`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل جلب القائمة');
  return data.users || [];
}

export async function resetDatabase() {
  const res = await apiFetch(`/api/admin/reset-database`, { method: 'POST' });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل إعادة التعيين');
  return data;
}

export async function setMyE2EPublicKey(publicKey) {
  const res = await apiFetch(`/api/users/me/e2e-key`, {
    method: 'PUT',
    headers: headers(),
    body: JSON.stringify({ publicKey })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل حفظ المفتاح');
  return data;
}

export async function getUserE2EPublicKey(userId) {
  const res = await apiFetch(`/api/users/${userId}/e2e-key`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) return null;
  return data.publicKey || null;
}

export async function getMe() {
  const res = await apiFetch(`/api/users/me`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل');
  return data;
}

export async function uploadAvatar(file) {
  const form = new FormData();
  form.append('file', file);
  const res = await apiFetch(`/api/upload-avatar`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${getToken()}` },
    body: form
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل رفع الصورة');
  return data;
}

export function uploadsUrl(path) {
  if (!path) return '';
  const base = API_BASE || '';
  return path.startsWith('http') ? path : base.replace(/\/$/, '') + path;
}

export async function subscribePush(subscription) {
  const res = await apiFetch(`/api/push/subscribe`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ subscription })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل تفعيل التنبيهات');
  return data;
}
