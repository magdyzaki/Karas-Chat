export function getApiBase() {
  try {
    return localStorage.getItem('reminders_api_url') || import.meta.env.VITE_API_URL || '';
  } catch {
    return import.meta.env.VITE_API_URL || '';
  }
}

export function setApiBase(url) {
  const v = (url || '').trim().replace(/\/$/, '');
  if (v) localStorage.setItem('reminders_api_url', v);
  else localStorage.removeItem('reminders_api_url');
}

/** إعادة المحاولة عند Failed to fetch (السيرفر نائم على Render) */
async function fetchWithRetry(url, opts, retries = 2) {
  for (let i = 0; i <= retries; i++) {
    try {
      const signal = typeof AbortSignal?.timeout === 'function' ? AbortSignal.timeout(60000) : undefined;
      const res = await fetch(url, { ...opts, signal });
      return res;
    } catch (e) {
      const isNetworkErr = e?.name === 'TypeError' || e?.message?.includes('fetch') || e?.message === 'Failed to fetch';
      if (isNetworkErr && i < retries) {
        await new Promise((r) => setTimeout(r, 25000)); // انتظار 25 ثانية (السيرفر يستيقظ)
        continue;
      }
      throw e;
    }
  }
  throw new Error('Failed to fetch');
}
}

function getToken() {
  return localStorage.getItem('reminders_token');
}

function headers() {
  const t = getToken();
  return {
    'Content-Type': 'application/json',
    ...(t ? { Authorization: `Bearer ${t}` } : {})
  };
}

export async function login(email, password) {
  const res = await fetchWithRetry(`${getApiBase()}/api/auth/login`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ email, password })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل تسجيل الدخول');
  return data;
}

export async function register(email, password, name = '') {
  const res = await fetchWithRetry(`${getApiBase()}/api/auth/register`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ email, password, name })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل التسجيل');
  return data;
}

export async function getReminders() {
  const res = await fetchWithRetry(`${getApiBase()}/api/reminders`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل جلب التنبيهات');
  return data.reminders || [];
}

export async function addReminder({ title, body, remind_at, repeat, notes }) {
  const res = await fetchWithRetry(`${getApiBase()}/api/reminders`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ title, body: body || '', remind_at, repeat: repeat || null, notes: notes || '' })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل إضافة التنبيه');
  return data;
}

export async function updateReminder(id, { title, body, remind_at, repeat, notes }) {
  const res = await fetchWithRetry(`${getApiBase()}/api/reminders/${id}`, {
    method: 'PUT',
    headers: headers(),
    body: JSON.stringify({ title, body, remind_at, repeat, notes })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل التعديل');
  return data;
}

export async function deleteReminder(id) {
  const res = await fetchWithRetry(`${getApiBase()}/api/reminders/${id}`, {
    method: 'DELETE',
    headers: headers()
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || 'فشل الحذف');
  }
}

export async function getVapidPublic() {
  const res = await fetchWithRetry(`${getApiBase()}/api/push/vapid-public`);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل جلب مفتاح Push');
  return data.publicKey;
}

export async function subscribePush(subscription) {
  const res = await fetchWithRetry(`${getApiBase()}/api/push/subscribe`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify(subscription)
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل تسجيل الاشتراك');
  return data;
}

export async function createInviteLink() {
  const url = `${getApiBase()}/api/invite-links`;
  const res = await fetchWithRetry(url, { method: 'POST', headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = data.error || `خطأ ${res.status}`;
    throw new Error(msg);
  }
  return data;
}

export async function checkInviteLink(token) {
  const res = await fetchWithRetry(`${getApiBase()}/api/check-invite/${encodeURIComponent(token)}`);
  return res.json().catch(() => ({}));
}

export async function consumeInviteLink(token) {
  const res = await fetchWithRetry(`${getApiBase()}/api/consume-invite/${encodeURIComponent(token)}`, { method: 'POST' });
  return res.json().catch(() => ({}));
}

export async function blockUser(targetUserId) {
  const res = await fetchWithRetry(`${getApiBase()}/api/admin/block-user`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ targetUserId })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل إيقاف المستخدم');
  return data;
}

export async function unblockUser(targetUserId) {
  const res = await fetchWithRetry(`${getApiBase()}/api/admin/unblock-user`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ targetUserId })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل إعادة التفعيل');
  return data;
}

export async function getBlockedUsers() {
  const res = await fetchWithRetry(`${getApiBase()}/api/admin/blocked-users`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل جلب القائمة');
  return data.users || [];
}

export async function getAllUsers() {
  const res = await fetchWithRetry(`${getApiBase()}/api/admin/all-users`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل جلب المستخدمين');
  return data.users || [];
}
