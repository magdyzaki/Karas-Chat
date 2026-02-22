const API = import.meta.env.VITE_API_URL || '';

function getToken() {
  return localStorage.getItem('chat_token');
}
function headers() {
  const t = getToken();
  return { 'Content-Type': 'application/json', ...(t ? { Authorization: `Bearer ${t}` } : {}) };
}

export async function register(emailOrPhone, password, name) {
  const res = await fetch(API + '/api/auth/register', { method: 'POST', headers: headers(), body: JSON.stringify({ emailOrPhone, password, name }) });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل التسجيل');
  return data;
}

export async function verify(emailOrPhone, code) {
  const res = await fetch(API + '/api/auth/verify', { method: 'POST', headers: headers(), body: JSON.stringify({ emailOrPhone, code }) });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل التحقق');
  return data;
}

export async function login(emailOrPhone, password) {
  const res = await fetch(API + '/api/auth/login', { method: 'POST', headers: headers(), body: JSON.stringify({ emailOrPhone, password }) });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل الدخول');
  return data;
}

export async function getUsers() {
  const res = await fetch(API + '/api/users', { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل');
  return data.users || [];
}

export async function checkContacts(phones) {
  const arr = Array.isArray(phones) ? phones : [phones];
  const res = await fetch(API + '/api/users/check-contacts', { method: 'POST', headers: headers(), body: JSON.stringify({ phoneNumbers: arr }) });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل');
  return data.users || [];
}

export async function getConversations() {
  const res = await fetch(API + '/api/conversations', { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل');
  return data.conversations || [];
}

export async function getConversation(id) {
  const res = await fetch(API + '/api/conversations/' + id, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل');
  return data;
}

export async function getMessages(convId, limit = 100, before = null) {
  let url = API + '/api/conversations/' + convId + '/messages?limit=' + limit;
  if (before) url += '&before=' + before;
  const res = await fetch(url, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل');
  return data.messages || [];
}

export async function createDirectConversation(otherUserId) {
  const res = await fetch(API + '/api/conversations/direct', { method: 'POST', headers: headers(), body: JSON.stringify({ otherUserId }) });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل');
  return data;
}

export async function createGroupConversation(name, memberIds) {
  const res = await fetch(API + '/api/conversations/group', { method: 'POST', headers: headers(), body: JSON.stringify({ name, memberIds }) });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'فشل');
  return data;
}
