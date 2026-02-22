import webpush from 'web-push';
const { publicKey, privateKey } = webpush.generateVAPIDKeys();
console.log('\nأضف هذه القيم إلى ملف .env:\n');
console.log('VAPID_PUBLIC_KEY=' + publicKey);
console.log('VAPID_PRIVATE_KEY=' + privateKey);
console.log('\nوأضف VAPID_PUBLIC_KEY في frontend/.env كـ:\nVITE_VAPID_PUBLIC_KEY=' + publicKey + '\n');
