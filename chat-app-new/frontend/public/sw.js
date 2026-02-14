/* Service Worker - تنبيهات الدفع عند إغلاق التطبيق */
self.addEventListener('push', (e) => {
  let data = { title: 'رسالة جديدة', body: 'لديك رسالة في Karas شات', tag: 'chat-msg' };
  try {
    if (e.data) data = { ...data, ...e.data.json() };
  } catch (_) {}
  const opts = {
    body: data.body || 'لديك رسالة جديدة',
    icon: '/icon-192.png',
    badge: '/icon-192.png',
    tag: data.tag || 'chat-msg',
    requireInteraction: true,
    silent: false,
    vibrate: [200, 100, 200, 100, 400],
    data: data.data || {}
  };
  e.waitUntil(self.registration.showNotification(data.title || 'Karas شات', opts));
});

self.addEventListener('notificationclick', (e) => {
  e.notification.close();
  const url = e.notification.data?.url || '/';
  e.waitUntil(clients.matchAll({ type: 'window', includeUncontrolled: true }).then((list) => {
    if (list.length) list[0].focus(); else clients.openWindow(url);
  }));
});
