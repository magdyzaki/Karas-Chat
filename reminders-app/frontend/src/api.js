const API_BASE = import.meta.env.VITE_API_URL || '';

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
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ email, password })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل تسجيل الدخول');
  return data;
}

export async function register(email, password, name = '') {
  const res = await fetch(`${API_BASE}/api/auth/register`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ email, password, name })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل التسجيل');
  return data;
}

export async function getReminders() {
  const res = await fetch(`${API_BASE}/api/reminders`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل جلب التنبيهات');
  return data.reminders || [];
}

export async function addReminder({ title, body, remind_at, repeat, notes }) {
  const res = await fetch(`${API_BASE}/api/reminders`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ title, body: body || '', remind_at, repeat: repeat || null, notes: notes || '' })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل إضافة التنبيه');
  return data;
}

export async function updateReminder(id, { title, body, remind_at, repeat, notes }) {
  const res = await fetch(`${API_BASE}/api/reminders/${id}`, {
    method: 'PUT',
    headers: headers(),
    body: JSON.stringify({ title, body, remind_at, repeat, notes })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل التعديل');
  return data;
}

export async function deleteReminder(id) {
  const res = await fetch(`${API_BASE}/api/reminders/${id}`, {
    method: 'DELETE',
    headers: headers()
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || 'فشل الحذف');
  }
}

export async function getVapidPublic() {
  const res = await fetch(`${API_BASE}/api/push/vapid-public`);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل جلب مفتاح Push');
  return data.publicKey;
}

export async function subscribePush(subscription) {
  const res = await fetch(`${API_BASE}/api/push/subscribe`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify(subscription)
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل تسجيل الاشتراك');
  return data;
}

export async function createInviteLink() {
  const res = await fetch(`${API_BASE}/api/invite-links`, { method: 'POST', headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل إنشاء الرابط');
  return data;
}

export async function checkInviteLink(token) {
  const res = await fetch(`${API_BASE}/api/check-invite/${encodeURIComponent(token)}`);
  return res.json().catch(() => ({}));
}

export async function consumeInviteLink(token) {
  const res = await fetch(`${API_BASE}/api/consume-invite/${encodeURIComponent(token)}`, { method: 'POST' });
  return res.json().catch(() => ({}));
}

export async function blockUser(targetUserId) {
  const res = await fetch(`${API_BASE}/api/admin/block-user`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ targetUserId })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل إيقاف المستخدم');
  return data;
}

export async function unblockUser(targetUserId) {
  const res = await fetch(`${API_BASE}/api/admin/unblock-user`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ targetUserId })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل إعادة التفعيل');
  return data;
}

export async function getBlockedUsers() {
  const res = await fetch(`${API_BASE}/api/admin/blocked-users`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل جلب القائمة');
  return data.users || [];
}

export async function getAllUsers() {
  const res = await fetch(`${API_BASE}/api/admin/all-users`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل جلب المستخدمين');
  return data.users || [];
}
