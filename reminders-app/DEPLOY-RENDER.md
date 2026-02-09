# نشر السيرفر على Render — خطوة بخطوة

## الخطوة 1: رفع السيرفر على GitHub

1. ادخل على **https://github.com** وسجّل الدخول.
2. اضغط **New** (أو +) → **New repository**.
3. اسم المستودع مثلاً: `reminders-backend`.
4. اختر **Private** أو **Public** ثم **Create repository**.
5. على جهازك افتح **PowerShell** في مجلد المشروع ونفّذ (غيّر `YOUR_USERNAME` باسمك في GitHub):

```powershell
cd D:\programs\Smart_CRM_Final_Arabic\reminders-app\backend
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/reminders-backend.git
git push -u origin main
```

لو ماعندكش Git مثبت، ثبّته من https://git-scm.com ثم أعد الأوامر.

---

## الخطوة 2: إنشاء Web Service على Render

1. ادخل على **https://dashboard.render.com**.
2. اضغط **New +** → **Web Service**.
3. لو طلب منك ربط GitHub، اختر **Connect GitHub** واختر الحساب/المستودع.
4. من القائمة اختر المستودع **reminders-backend** (أو الاسم اللي أنشأته).
5. الإعدادات:
   - **Name:** مثلاً `reminders-api`.
   - **Region:** اختر الأقرب لك.
   - **Branch:** `main`.
   - **Root Directory:** اتركه **فاضي** (لأنك رفعت محتويات مجلد `backend` فقط).
   - **Runtime:** **Node**.
   - **Build Command:** `npm install`
   - **Start Command:** `npm start`
6. اضغط **Advanced** (اختياري) → **Environment**:
   - اضف متغير إن حابب: `JWT_SECRET` = أي كلمة سر طويلة (اختياري؛ لو ما أضفتش البرنامج يستخدم القيمة الافتراضية).
7. اضغط **Create Web Service**.
8. انتظر حتى ينتهي الـ Build والـ Deploy (دقائق).
9. في أعلى الصفحة هتلقى رابط مثل: **https://reminders-api-xxxx.onrender.com** — هذا هو **عنوان السيرفر**. احفظه.

---

## الخطوة 3: بعد نشر الواجهة (Vercel)

في مشروع الواجهة (frontend) عيّن متغير البيئة:

- **VITE_API_URL** = `https://reminders-api-xxxx.onrender.com` (الرابط اللي من Render بدون / في الآخر).

ثم أعد بناء الواجهة ونشرها حتى تتصل الواجهة بالسيرفر على Render.
