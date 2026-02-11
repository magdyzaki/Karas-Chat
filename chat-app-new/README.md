# شات — نسخة جديدة من الصفر

تطبيق دردشة (فردي ومجموعات) مع رسائل فورية عبر Socket.IO.

## التشغيل محلياً

### الباكند
```bash
cd chat-app-new/backend
npm install
npm run dev
```
يعمل على المنفذ 5000.

### الفرونتند
```bash
cd chat-app-new/frontend
npm install
npm run dev
```
يفتح على المنفذ 5173 مع proxy للـ API و Socket.IO.

## النشر

- **الباكند:** ارفعه إلى Koyeb (أو أي مضيف Node) وضبط `PORT` واختيارياً `JWT_SECRET` و `DB_PATH`.
- **الفرونتند:** ارفعه إلى Vercel وضبط `VITE_API_URL` برابط الباكند (مثل `https://your-app.koyeb.app`).

## المميزات

- تسجيل دخول / إنشاء حساب (بريد أو رقم موبايل)
- محادثات فردية ومجموعات
- رسائل نصية + صور وملفات
- ظهور الرسائل فوراً عبر Socket.IO
- واجهة متجاوبة للموبايل والكمبيوتر
