# نشر الباك اند على Koyeb

## إعدادات مطلوبة في Koyeb

للمستودع `Smart_CRM_Final_Arabic` (أو Karas-Chat):

### 1. Work directory (مجلد العمل)
```
chat-app-new/backend
```
**ضروري** لأن المشروع داخل monorepo.

### 2. Run command (أمر التشغيل)
```
npm run start
```
أو اتركه افتراضي — سيستخدم `npm start` من package.json

### 3. Environment Variables (متغيرات البيئة)
أضف في Koyeb → Service → Settings → Environment variables:

| المتغير | القيمة | ملاحظة |
|---------|--------|--------|
| `JWT_SECRET` | (مفتاح سري قوي) | مطلوب |
| `TRUSTED_PHONES` | `201229084204` | أرقام تتجاوز التحقق |
| `APPROVAL_MODE` | `true` | اختياري |
| `PORT` | يضبطه Koyeb تلقائياً | لا تضف |

### 4. Ports
Koyeb يضبط PORT تلقائياً. التطبيق يقرأ `process.env.PORT`.

---

## إذا فشل النشر
1. تأكد من **Work directory** = `chat-app-new/backend`
2. راجع **Deployment logs** في Koyeb للأخطاء
3. تأكد أن كل متغيرات البيئة مضافة
