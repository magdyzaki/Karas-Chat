const API_BASE = import.meta.env.VITE_API_URL || '';

export async function searchGifs(q) {
  const res = await fetch(`${API_BASE}/api/giphy/search?q=${encodeURIComponent(q || '')}`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل بحث GIF');
  return data.gifs || [];
}

export async function getTrendingGifs() {
  const res = await fetch(`${API_BASE}/api/giphy/trending`, { headers: headers() });
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

export async function forgotPassword(emailOrPhone) {
  const res = await fetch(`${API_BASE}/api/auth/forgot-password`, {
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
  const res = await fetch(`${API_BASE}/api/dev/last-code?q=${q}`);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل');
  return data;
}

export async function resetPassword(emailOrPhone, code, newPassword) {
  const res = await fetch(`${API_BASE}/api/auth/reset-password`, {
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
  const res = await fetch(`${API_BASE}/api/users/check-contacts`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ phoneNumbers: arr })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل البحث');
  return data.users || [];
}

export async function getUsers() {
  const res = await fetch(`${API_BASE}/api/users`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل جلب المستخدمين');
  return data.users || [];
}

export async function getAdminUsers() {
  const res = await fetch(`${API_BASE}/api/admin/users`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل جلب المستخدمين');
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
  return { messages: data.messages || [], readReceipts: data.readReceipts || [], reactions: data.reactions || [] };
}

export async function muteConversation(conversationId) {
  const res = await fetch(`${API_BASE}/api/conversations/${conversationId}/mute`, { method: 'PATCH', headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل كتم المحادثة');
  return data;
}

export async function unmuteConversation(conversationId) {
  const res = await fetch(`${API_BASE}/api/conversations/${conversationId}/unmute`, { method: 'PATCH', headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل إلغاء كتم المحادثة');
  return data;
}

export async function archiveConversation(conversationId) {
  const res = await fetch(`${API_BASE}/api/conversations/${conversationId}/archive`, { method: 'PATCH', headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل أرشفة المحادثة');
  return data;
}

export async function unarchiveConversation(conversationId) {
  const res = await fetch(`${API_BASE}/api/conversations/${conversationId}/unarchive`, { method: 'PATCH', headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل إلغاء أرشفة المحادثة');
  return data;
}

export async function getStories() {
  const res = await fetch(`${API_BASE}/api/stories`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل جلب القصص');
  return data.feed || [];
}

export async function createStory(type, content, file_name = null) {
  const res = await fetch(`${API_BASE}/api/stories`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ type, content, file_name })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل نشر القصة');
  return data;
}

export async function setDisappearing(conversationId, seconds) {
  const res = await fetch(`${API_BASE}/api/conversations/${conversationId}/disappearing`, {
    method: 'PATCH',
    headers: headers(),
    body: JSON.stringify({ seconds })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل تحديد الرسائل المؤقتة');
  return data;
}

export async function votePoll(conversationId, messageId, optionIndex) {
  const res = await fetch(`${API_BASE}/api/conversations/${conversationId}/messages/${messageId}/vote`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ optionIndex })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل التصويت');
  return data;
}

export async function exportBackup() {
  const res = await fetch(`${API_BASE}/api/backup/export`, { headers: headers() });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || 'فشل تصدير النسخة الاحتياطية');
  }
  const blob = await res.blob();
  return blob;
}

export async function forwardMessage(targetConversationId, fromConversationId, messageId) {
  const res = await fetch(`${API_BASE}/api/conversations/${targetConversationId}/forward`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ fromConversationId, messageId })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل إعادة التوجيه');
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

export async function getBroadcastLists() {
  const res = await fetch(`${API_BASE}/api/broadcast`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل جلب القوائم');
  return data.lists || [];
}

export async function createBroadcastList(name, recipientIds) {
  const res = await fetch(`${API_BASE}/api/broadcast`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ name, recipientIds })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل إنشاء القائمة');
  return data;
}

export async function updateBroadcastList(id, { name, recipientIds }) {
  const res = await fetch(`${API_BASE}/api/broadcast/${id}`, {
    method: 'PATCH',
    headers: headers(),
    body: JSON.stringify({ name, recipientIds })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل التحديث');
  return data;
}

export async function deleteBroadcastList(id) {
  const res = await fetch(`${API_BASE}/api/broadcast/${id}`, { method: 'DELETE', headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل الحذف');
  return data;
}

export async function sendBroadcastMessage(listId, { type = 'text', content, file_name }) {
  const res = await fetch(`${API_BASE}/api/broadcast/${listId}/send`, {
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
  const res = await fetch(`${API_BASE}/api/upload`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${getToken()}` },
    body: form
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل رفع الملف');
  return data;
}

export async function consumeInviteLink(token) {
  const res = await fetch(`${API_BASE}/api/consume-invite/${token}`, { method: 'POST' });
  return res.json().catch(() => ({}));
}

export async function createInviteLink() {
  const res = await fetch(`${API_BASE}/api/invite-links`, { method: 'POST', headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل إنشاء الرابط');
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
  if (!res.ok) throw new Error(data.error || 'فشل إلغاء الإيقاف');
  return data;
}

export async function getPendingUsers() {
  const res = await fetch(`${API_BASE}/api/admin/pending-users`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل');
  return data;
}

export async function approveUser(targetUserId) {
  const res = await fetch(`${API_BASE}/api/admin/approve-user`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ targetUserId })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل التفعيل');
  return data;
}

export async function getPendingCodes() {
  const res = await fetch(`${API_BASE}/api/admin/pending-codes`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل');
  return data;
}

export async function getBlockedUsers() {
  const res = await fetch(`${API_BASE}/api/admin/blocked-users`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل جلب القائمة');
  return data.users || [];
}

export async function resetDatabase() {
  const res = await fetch(`${API_BASE}/api/admin/reset-database`, { method: 'POST' });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل إعادة التعيين');
  return data;
}

export async function setMyE2EPublicKey(publicKey) {
  const res = await fetch(`${API_BASE}/api/users/me/e2e-key`, {
    method: 'PUT',
    headers: headers(),
    body: JSON.stringify({ publicKey })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل حفظ المفتاح');
  return data;
}

export async function getUserE2EPublicKey(userId) {
  const res = await fetch(`${API_BASE}/api/users/${userId}/e2e-key`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) return null;
  return data.publicKey || null;
}

export async function getMe() {
  const res = await fetch(`${API_BASE}/api/users/me`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل');
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

export function uploadsUrl(path) {
  if (!path) return '';
  const base = API_BASE || '';
  return path.startsWith('http') ? path : base.replace(/\/$/, '') + path;
}

export async function subscribePush(subscription) {
  const res = await fetch(`${API_BASE}/api/push/subscribe`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ subscription })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل تفعيل التنبيهات');
  return data;
}
