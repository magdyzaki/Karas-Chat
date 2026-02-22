# حل خطأ SSL عند الاتصال بـ MongoDB (على صفحة التنبيهات)

إذا ظهر خطأ مثل:
`error:0A000438:SSL routines:ssl3_read_bytes:tlsv1 alert internal error`
أو `SSL alert number 80`

فهذا عادةً **فشل اتصال TLS** بين السيرفر (Koyeb) وقاعدة MongoDB Atlas.

---

## 1) التأكد من إصدار Node على Koyeb

- ادخل **Koyeb** → خدمة **reminders-backend** → **Settings**.
- في **Environment** أو **Build** ابحث عن **NODE_VERSION** أو إعدادات الـ Runtime.
- اجعل إصدار Node **18** أو أحدث (مثلاً أضف متغير: **NODE_VERSION** = **18**).
- احفظ ثم اعمل **Redeploy**.

إصدارات Node الأقدم أحياناً تسبب مشاكل TLS مع MongoDB Atlas.

---

## 2) التأكد من رابط الاتصال (MONGODB_URI)

- في **Koyeb** → **Environment** تأكد أن **MONGODB_URI**:
  - بدون مسافات في البداية أو النهاية.
  - كلمة المرور فيها رموز خاصة (مثل `#` أو `@`) يجب أن تكون **مشفّرة** (URL-encoded)، مثلاً من https://www.urlencoder.org/

---

## 3) إضافة خيار TLS في الرابط (اختياري)

في نهاية الرابط قبل أي `?` موجود أضف أو عدّل المعاملات لتصبح تحتوي على:
`?retryWrites=true&w=majority&tls=true`

مثال:
```
mongodb+srv://USER:PASS@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority&tls=true
```

ثم احفظ في Koyeb وعمل **Redeploy**.

---

## 4) التأكد من Network Access في MongoDB Atlas

- ادخل **MongoDB Atlas** → **Network Access**.
- تأكد وجود عنوان **0.0.0.0/0** (السماح من أي مكان) أو أن عناوين Koyeb مسموحة.

---

## 5) بعد التعديلات

ارفع التعديلات على الباكند (إن وُجدت) ثم من Koyeb اعمل **Redeploy**.  
راجع **Logs**؛ إذا استمر الخطأ انسخ السطر الكامل من الـ Log وأرسله للمراجعة.
