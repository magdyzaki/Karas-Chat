# تخزين التنبيهات دائماً باستخدام MongoDB Atlas (مجاني) مع Koyeb Free

لو خدمتك على Koyeb من نوع **Free** ولا تقبل Volumes، يمكنك استخدام **MongoDB Atlas** (خطة مجانية) كقاعدة بيانات خارجية. التنبيهات والمستخدمون يبقون محفوظين حتى بعد نوم السيرفر أو إعادة تشغيله.

---

## الخطوة 1: إنشاء قاعدة بيانات مجانية على MongoDB Atlas

1. ادخل **https://www.mongodb.com/cloud/atlas** وسجّل الدخول (أو أنشئ حساباً مجانياً).
2. اضغط **Build a Database** أو **Create**.
3. اختر الخطة **M0 FREE** (Shared) ثم **Create**.
4. اختر منطقة (Region) قريبة منك أو من منطقة خدمة Koyeb (مثلاً **Frankfurt** إذا كانت خدمتك هناك).
5. اضغط **Create Cluster** وانتظر حتى يُنشأ الـ Cluster (دقائق).

---

## الخطوة 2: السماح بالوصول من الإنترنت وإنشاء مستخدم

1. في القائمة الجانبية: **Network Access** → **Add IP Address**.
   - اختر **Allow Access from Anywhere** (0.0.0.0/0) حتى يقدر Koyeb يتصل — أو أضف عناوين Koyeb إن عرفتها.
   - اضغط **Confirm**.
2. من القائمة: **Database Access** → **Add New Database User**.
   - **Username** و **Password**: اختر اسم وكلمة مرور قوية واحفظهما.
   - **Database User Privileges**: اختر **Read and write to any database** (أو **Atlas admin** للبساطة).
   - اضغط **Add User**.

---

## الخطوة 3: الحصول على رابط الاتصال (Connection String)

1. من الصفحة الرئيسية للـ Cluster اضغط **Connect**.
2. اختر **Connect your application** (أو Drivers).
3. اختر **Node.js** ونسخة مناسبة (مثلاً 5.5 أو أحدث).
4. انسخ **Connection string** — شكله تقريباً:
   ```text
   mongodb+srv://USERNAME:PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
5. استبدل **USERNAME** و **PASSWORD** باسم المستخدم وكلمة المرور اللي أنشأتهما.  
   لو في الرابط رموز خاصة في كلمة المرور (مثل `#` أو `@`) استبدلها بنسخة مشفّرة: [URL Encode](https://www.urlencoder.org/) ثم الصق الناتج مكان PASSWORD.

6. في نهاية الرابط قبل `?` أو بعدها أضف اسم قاعدة البيانات (اختياري؛ الكود يستخدم اسم ثابت `reminders`). يمكن ترك الرابط كما هو — الكود يحدد اسم الـ database تلقائياً.

مثال نهائي:
```text
mongodb+srv://reminders_user:كلمة_السر_المشفرة@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

---

## الخطوة 4: إضافة المتغير في Koyeb

1. ادخل **https://app.koyeb.com** → خدمتك **reminders-backend**.
2. **Settings** → **Environment** (أو **Environment variables**).
3. اضغط **Add variable** أو **Add secret**:
   - **Key:** `MONGODB_URI`
   - **Value:** الصق **رابط الاتصال الكامل** (اللي عدّلته في الخطوة 3).
4. احفظ (Save).

---

## الخطوة 5: رفع الكود وإعادة النشر

- **لو خدمة Koyeb مربوطة بمستودع فيه المشروع الكامل** (مثلاً مستودع واحد فيه `reminders-app` أو فيه مجلد الباكند):
  من مجلد المشروع على جهازك:
  ```powershell
  git add reminders-app/
  git commit -m "دعم MongoDB Atlas للتخزين الدائم مع Koyeb Free"
  git push origin main
  ```
  ثم من Koyeb اضغط **Redeploy**.

- **لو خدمة Koyeb مربوطة بمستودع باكند فقط** (مثلاً **magdyzaki/reminders-backend**):
  1. انسخ من مشروعك المحلي كل محتويات **reminders-app/backend** (بما فيها الملفات الجديدة `db-mongo.js` و `db-lowdb.js` والتعديلات على `db.js` و `package.json` و `index.js` والـ routes) إلى مجلد ذلك المستودع.
  2. من مجلد المستودع نفّذ: `npm install` (لتثبيت حزمة `mongodb`) ثم:
  ```powershell
  git add .
  git commit -m "دعم MongoDB Atlas للتخزين الدائم"
  git push origin main
  ```
  3. من Koyeb اضغط **Redeploy** وانتظر حتى يكتمل النشر.

---

## التأكد أن كل شيء يعمل

- في **Logs** على Koyeb يجب أن تظهر جملة مثل: **"استخدام MongoDB للتخزين الدائم (MONGODB_URI مضبوط)."**
- أضف تنبيهاً من التطبيق، ثم اعمل **Redeploy** من Koyeb، ثم افتح التطبيق مرة ثانية — المفروض تشوف التنبيه والقائمة كما كانت (البيانات محفوظة في MongoDB).

---

## ملخص

| الخطوة | ماذا تفعل |
|--------|-----------|
| 1 | إنشاء Cluster مجاني (M0) على MongoDB Atlas. |
| 2 | Network Access: السماح من أي عنوان (0.0.0.0/0)، وإنشاء مستخدم قاعدة بيانات. |
| 3 | نسخ Connection string واستبدال USERNAME و PASSWORD. |
| 4 | في Koyeb إضافة متغير البيئة **MONGODB_URI** = رابط الاتصال. |
| 5 | رفع الكود وعمل Redeploy من Koyeb. |

بعد ذلك التنبيهات لا تُحذف عند إغلاق البرنامج أو نوم السيرفر، لأنها محفوظة في MongoDB Atlas وليس في ملف مؤقت على Koyeb.
