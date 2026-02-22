# حل مشكلة "Failed to fetch"

اتبع الخطوات بالترتيب.

---

## الخطوة 1 — معرفة الرابطين بالضبط

1. **رابط الواجهة (Vercel):**  
   من Vercel → مشروعك → Deployments → اضغط أي نشر "Ready" → اضغط "Visit".  
   انسخ الرابط من شريط العنوان في المتصفح، مثل:  
   `https://karas-chat-app-xxxxx.vercel.app`  
   **بدون** `/` في الآخر.

2. **رابط الباكند (Koyeb):**  
   `https://Karas-Chat-App.koyeb.app`  
   **بدون** `/` في الآخر.

---

## الخطوة 2 — CORS على Koyeb

1. ادخل **koyeb.com** → خدمتك (Karas-Chat-App).
2. **Settings** → **Environment variables**.
3. لو **CORS_ORIGIN** موجودة: عدّل **Value** وحط **رابط Vercel** اللي نسخته في الخطوة 1 (حرف بحرف، بدون مسافات، بدون `/` في الآخر).
4. لو **CORS_ORIGIN** مش موجودة: اضغط Add → Name: `CORS_ORIGIN`، Value: **رابط Vercel**.
5. **Save** ثم **Redeploy** للخدمة وانتظر لحد ما تخلص.

---

## الخطوة 3 — تشغيل بناء جديد على Vercel (بدون الاعتماد على Create Deployment)

لو زر "Create Deployment" بيطلع 500، نفعّل بناء جديد عن طريق **دفع تعديل بسيط من جهازك**:

1. افتح **PowerShell** ونفّذ:
   ```bash
   cd D:\programs\Karas-Chat-Deploy
   ```
2. ثم:
   ```bash
   git commit --allow-empty -m "Trigger Vercel rebuild"
   git push origin main
   ```
3. ارجع لـ **Vercel** → **Deployments** وانتظر نشر جديد (يبدأ تلقائي من GitHub). استنى لحد ما يبقى **Ready**.
4. بعد ما يخلص، افتح الرابط من **Visit** وجرب الشات.

---

## الخطوة 4 — التأكد من الباكند

في المتصفح افتح:

`https://Karas-Chat-App.koyeb.app/api/auth/login`

- لو ظهرت رسالة JSON (حتى خطأ مثل "البريد وكلمة المرور مطلوبان") يبقى الباكند شغال.
- لو الصفحة فاضية أو خطأ اتصال، يبقى مشكلة من Koyeb (شوف Logs للخدمة).

---

## لو لسه "Failed to fetch"

جرّب على Koyeb وضع **CORS_ORIGIN** مؤقتاً كالتالي لعزل المشكلة:

- **Value:** `*`  
  (نجرب لو المشكلة من CORS. لو اشتغل، رجّع القيمة لرابط Vercel بالضبط.)

ثم **Save** و **Redeploy** وجرب الشات مرة تانية.
