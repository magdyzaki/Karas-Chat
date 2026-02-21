# Karas شات - نسخة نظيفة

تطبيق دردشة بسيط: تسجيل، محادثات فردية ومجموعات، مكالمات صوتية وفيديو.

## هيكل المشروع

```
karas-chat-fresh/
├── backend/          # Express + LowDB + Socket.io
└── (الفرونت في) karas-chat-fresh-frontend/
```

## التشغيل

### الطريقة الأسهل (الباك اند والفرونت معاً)
```powershell
cd karas-chat-fresh
npm install
npm run dev
```
يشغّل الباك اند والفرونت في نفس الوقت.

---

### أو تشغيل كل واحد لوحده

### 1. الباك اند (شغّله أولاً)
```powershell
cd karas-chat-fresh/backend
npm install
npm run dev
```
يعمل على المنفذ 5002

### 2. الفرونت اند
```powershell
cd karas-chat-fresh-frontend
npm install
npm run dev
```
يعمل على المنفذ 5173

### 3. افتح المتصفح
http://localhost:5173

## إعدادات .env (الباك اند)

```
PORT=5002
JWT_SECRET=غيّر-هذا-في-الإنتاج
SKIP_VERIFICATION=true
TRUSTED_PHONES=01229084204,201229084204
```

- `TRUSTED_PHONES`: أرقام تُفعّل فوراً بدون رمز تحقق
- `SKIP_VERIFICATION=true`: تجاوز التحقق للجميع (للتطوير فقط)
