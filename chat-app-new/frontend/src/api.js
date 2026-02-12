const API_BASE = import.meta.env.VITE_API_URL || '';

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

export async function register(emailOrPhone, password, name = '') {
  const res = await fetch(`${API_BASE}/api/auth/register`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ emailOrPhone, password, name })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل التسجيل');
  return data;
}

export async function verify(emailOrPhone, code) {
  const res = await fetch(`${API_BASE}/api/auth/verify`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ emailOrPhone, code })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل التحقق');
  return data;
}

export async function login(emailOrPhone, password) {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ emailOrPhone, password })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل تسجيل الدخول');
  return data;
}

export async function checkContacts(phoneNumbers) {
  const arr = Array.isArray(phoneNumbers) ? phoneNumbers : (phoneNumbers ? [String(phoneNumbers)] : []);
  const res = await fetch(`${API_BASE}/api/users/check-contacts`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ phoneNumbers: arr })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل التحقق من جهات الاتصال');
  return data.users || [];
}

export async function getConversations() {
  const res = await fetch(`${API_BASE}/api/conversations`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل جلب المحادثات');
  return data.conversations || [];
}

export async function getConversation(id) {
  const res = await fetch(`${API_BASE}/api/conversations/${id}`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل جلب المحادثة');
  return data;
}

export async function getMessages(conversationId, limit = 100, before = null) {
  let url = `${API_BASE}/api/conversations/${conversationId}/messages?limit=${limit}`;
  if (before) url += `&before=${before}`;
  const res = await fetch(url, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل جلب الرسائل');
  return { messages: data.messages || [], readReceipts: data.readReceipts || [] };
}

export async function deleteMessage(conversationId, messageId, forEveryone) {
  const res = await fetch(`${API_BASE}/api/conversations/${conversationId}/messages/${messageId}/delete`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ forEveryone: !!forEveryone })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل حذف الرسالة');
  return data;
}

export async function createDirectConversation(otherUserId) {
  const res = await fetch(`${API_BASE}/api/conversations/direct`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ otherUserId })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل إنشاء المحادثة');
  return data;
}

export async function createGroupConversation(name, memberIds) {
  const res = await fetch(`${API_BASE}/api/conversations/group`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ name, memberIds })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل إنشاء المجموعة');
  return data;
}

export async function leaveGroup(conversationId) {
  const res = await fetch(`${API_BASE}/api/conversations/${conversationId}/leave`, {
    method: 'POST',
    headers: headers()
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل مغادرة المجموعة');
  return data;
}

export async function deleteGroup(conversationId) {
  const res = await fetch(`${API_BASE}/api/conversations/${conversationId}`, {
    method: 'DELETE',
    headers: headers()
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل حذف المجموعة');
  return data;
}

export async function addMemberToGroup(conversationId, targetUserId) {
  const res = await fetch(`${API_BASE}/api/conversations/${conversationId}/add-member`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ targetUserId })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل إضافة العضو');
  return data;
}

export async function removeMemberFromGroup(conversationId, targetUserId) {
  const res = await fetch(`${API_BASE}/api/conversations/${conversationId}/remove-member`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ targetUserId })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل طرد العضو');
  return data;
}

export async function uploadFile(file) {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${API_BASE}/api/upload`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${getToken()}` },
    body: form
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل رفع الملف');
  return data;
}

export function uploadsUrl(path) {
  if (!path) return '';
  const base = API_BASE || '';
  return path.startsWith('http') ? path : base.replace(/\/$/, '') + path;
}

export async function createInviteLink() {
  const res = await fetch(`${API_BASE}/api/invite-links`, {
    method: 'POST',
    headers: headers()
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || (res.status === 404 ? 'الرابط غير متوفر. تأكد من تحديث السيرفر.' : 'فشل إنشاء الرابط'));
  return data;
}

export async function checkInviteLink(token) {
  const res = await fetch(`${API_BASE}/api/check-invite/${encodeURIComponent(token)}`);
  const data = await res.json().catch(() => ({}));
  return data;
}

export async function consumeInviteLink(token) {
  const res = await fetch(`${API_BASE}/api/consume-invite/${encodeURIComponent(token)}`, { method: 'POST' });
  const data = await res.json().catch(() => ({}));
  return data;
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

export async function getProfile() {
  const res = await fetch(`${API_BASE}/api/users/me`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل جلب البروفايل');
  return data;
}

export async function updateProfile({ name, avatar_url }) {
  const res = await fetch(`${API_BASE}/api/users/me`, {
    method: 'PATCH',
    headers: headers(),
    body: JSON.stringify({ name, avatar_url })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل تحديث البروفايل');
  return data;
}

export async function uploadAvatar(file) {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${API_BASE}/api/upload-avatar`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${getToken()}` },
    body: form
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل رفع الصورة');
  return data;
}
