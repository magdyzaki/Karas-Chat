/**
 * طلب صلاحية الإشعارات ثم إظهار إشعار مكتوب + قراءة النص بصوت افتراضي (TTS)
 */
export function requestNotificationPermission() {
  if (!('Notification' in window)) return Promise.resolve(false);
  if (Notification.permission === 'granted') return Promise.resolve(true);
  if (Notification.permission === 'denied') return Promise.resolve(false);
  return Notification.requestPermission().then(p => p === 'granted');
}

/**
 * إظهار تنبيه: إشعار مكتوب + TTS
 * @param {string} title - عنوان التنبيه
 * @param {string} body - نص التنبيه (يُقرأ بالصوت)
 */
export function showReminderNotification(title, body) {
  const textToSpeak = body && body.trim() ? `${title}. ${body}` : title;

  // إشعار المتصفح (مكتوب)
  if ('Notification' in window && Notification.permission === 'granted') {
    try {
      new Notification(title, {
        body: body || title,
        dir: 'rtl',
        lang: 'ar'
      });
    } catch (_) {}
  }

  // الصوت الافتراضي (TTS)
  if ('speechSynthesis' in window) {
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(textToSpeak);
    u.lang = 'ar-SA';
    u.rate = 0.9;
    const voices = speechSynthesis.getVoices();
    const arVoice = voices.find(v => v.lang.startsWith('ar'));
    if (arVoice) u.voice = arVoice;
    speechSynthesis.speak(u);
  }
}

/**
 * تحويل مفتاح VAPID من Base64 إلى Uint8Array للاشتراك في Push
 */
function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = atob(base64);
  const output = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) output[i] = rawData.charCodeAt(i);
  return output;
}

/**
 * الاشتراك في إشعارات الدفع (حتى تعمل مع الشاشة مطفية)
 * @returns {Promise<{ok: boolean, reason?: string}>}
 */
export async function subscribeToPush(getVapidPublic, subscribePush) {
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    return { ok: false, reason: 'المتصفح لا يدعم إشعارات الدفع' };
  }
  const permission = await requestNotificationPermission();
  if (!permission) {
    return { ok: false, reason: 'سماح بالإشعارات من إعدادات الموقع أولاً' };
  }
  try {
    const reg = await navigator.serviceWorker.ready;
    let publicKey = await getVapidPublic();
    if (typeof publicKey === 'string') publicKey = publicKey.trim().replace(/\s/g, '');
    const sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(publicKey)
    });
    await subscribePush(sub.toJSON ? sub.toJSON() : { endpoint: sub.endpoint, keys: sub.getKey('p256dh') && sub.getKey('auth') ? { p256dh: btoa(String.fromCharCode.apply(null, new Uint8Array(sub.getKey('p256dh')))), auth: btoa(String.fromCharCode.apply(null, new Uint8Array(sub.getKey('auth')))) } : {} });
    return { ok: true };
  } catch (e) {
    const msg = e && e.message ? e.message : String(e);
    if (msg.includes('فشل جلب مفتاح') || msg.includes('fetch') || msg.includes('Network')) {
      return { ok: false, reason: 'لا يمكن الاتصال بالسيرفر. تحقق من VITE_API_URL على Vercel (عنوان الباكند)' };
    }
    if (msg.includes('فشل تسجيل الاشتراك') || msg.includes('401') || msg.includes('انتهت الجلسة')) {
      return { ok: false, reason: 'انتهت الجلسة أو فشل التسجيل. سجّل دخولاً مرة أخرى' };
    }
    if (msg.includes('push service') || msg.includes('registration failed')) {
      return { ok: false, reason: 'خطأ من خدمة الإشعارات. جرّب: مسح بيانات الموقع ثم إعادة المحاولة، أو توليد مفاتيح VAPID جديدة في Koyeb (بدون مسافات أو أسطر)' };
    }
    return { ok: false, reason: msg.slice(0, 80) };
  }
}

// تحميل الأصوات (بعض المتصفحات لا تعيد الأصوات إلا بعد تفاعل)
if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
  speechSynthesis.getVoices();
  if (speechSynthesis.onvoiceschanged !== undefined) {
    speechSynthesis.onvoiceschanged = () => speechSynthesis.getVoices();
  }
}
