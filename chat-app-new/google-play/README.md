# بناء تطبيق Karas شات كـ App أندرويد (بدل الشورتكت)

هذا المجلد يجعل من الواجهة ويب تطبيق **أندرويد حقيقي** (.apk) يثبّت على الموبايل كبرنامج مستقل — ليس مجرد shortcut.

---

## المتطلبات

1. **Node.js** مثبت
2. **Android Studio** مثبت — [تحميل](https://developer.android.com/studio)
3. **الباكند** يعمل على عنوان ثابت (مثل ngrok أو Koyeb) — التطبيق يحتاج يتصل به

---

## الخطوات بالترتيب

### 1) ضبط عنوان الباكند

في مجلد `chat-app-new/frontend` أنشئ أو عدّل ملف `.env`:

```env
VITE_API_URL=https://رابط-الباكند-لديك
```

مثال لو تستخدم ngrok:
```env
VITE_API_URL=https://xxxx.ngrok-free.app
```

**بدون `/` في النهاية.**

---

### 2) بناء الواجهة

```bash
cd D:\programs\Smart_CRM_Final_Arabic\chat-app-new\frontend
npm install
npm run build
```

سيُنشأ مجلد `dist` — هذا ما سيُحوّل لتطبيق أندرويد.

---

### 3) تجهيز مشروع أندرويد

```bash
cd D:\programs\Smart_CRM_Final_Arabic\chat-app-new\google-play
npm install
npx cap add android
npx cap sync android
```

- أول مرة: `cap add android` ينشئ مجلد `android`
- `cap sync` ينسخ محتوى `frontend/dist` لمشروع أندرويد

---

### 4) فتح المشروع في Android Studio

```bash
npx cap open android
```

أو افتح Android Studio يدوياً واختر مجلد `google-play/android`.

---

### 5) تشغيل التطبيق على الموبايل أو المحاكي

- وصّل الموبايل بالكمبيوتر (مع تفعيل USB debugging)
- أو شغّل محاكي أندرويد
- من Android Studio: اضغط زر **Run** (▶)

---

### 6) بناء ملف APK للتثبيت

داخل **Android Studio**:

1. **Build** → **Build Bundle(s) / APK(s)** → **Build APK(s)**
2. انتظر انتهاء البناء
3. الملف يظهر في: `android/app/build/outputs/apk/debug/app-debug.apk`
4. انسخ الـ APK للموبايل وثبّت

---

### 7) (اختياري) بناء للرفع على جوجل بلاي

1. **Build** → **Generate Signed Bundle / APK**
2. اختر **Android App Bundle** → **Next**
3. إنشاء مفتاح توقيع جديد (أو استخدام موجود)
4. اختر **release** → **Finish**
5. ارفع الملف `.aab` في Play Console

---

## ملخص

| الخطوة | الأمر / الإجراء |
|--------|-----------------|
| 1 | ضبط `VITE_API_URL` في frontend/.env |
| 2 | `cd frontend` → `npm run build` |
| 3 | `cd google-play` → `npm install` → `npx cap add android` → `npx cap sync android` |
| 4 | `npx cap open android` |
| 5 | من Android Studio: Run أو Build APK |

---

## ملاحظات

- **الباكند لازم يكون متاح** — لو تشغّل محلياً (ngrok)، جهازك لازم يكون شغّال حين استخدام التطبيق.
- **لكل تغيير في الواجهة:** أعد `npm run build` ثم `npx cap sync android` قبل إعادة البناء.
- الشورتكت (PWA) يبقى يعمل من المتصفح؛ التطبيق من Capacitor تطبيق منفصل يثبّت كبرنامج.
