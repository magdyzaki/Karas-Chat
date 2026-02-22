import { precacheAndRoute } from 'workbox-precaching';

precacheAndRoute(self.__WB_MANIFEST || []);

self.addEventListener('push', (event) => {
  let title = 'تنبيه';
  let body = '';
  let reminderId = null;
  try {
    if (event.data) {
      const d = event.data.json();
      title = d.title || title;
      body = d.body || body;
      reminderId = d.id || null;
    }
  } catch (_) {}
  event.waitUntil(
    self.registration.showNotification(title, {
      body,
      dir: 'rtl',
      lang: 'ar',
      data: { reminderId }
    })
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const reminderId = event.notification.data && event.notification.data.reminderId;
  const url = self.registration.scope.replace(/\/$/, '');
  const openUrl = reminderId ? `${url}?playReminder=${reminderId}` : url;
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      if (clientList.length > 0) {
        clientList[0].navigate(openUrl);
        clientList[0].focus();
      } else {
        clients.openWindow(openUrl);
      }
    })
  );
});
