# Postgres setup for invite links (fix "رمز الدعوة غير صالح")

## Problem
Render free tier uses ephemeral disk - data is lost on restart. Invite links disappear.

## Solution
Store invite links in Render's free PostgreSQL (persistent).

---

## Steps

### 1. Install pg package
```bash
cd backend
npm install pg --save
```

### 2. Create PostgreSQL on Render
1. Go to https://dashboard.render.com
2. New → **PostgreSQL**
3. Choose a name (e.g. karas-chat-db), Create
4. Copy **Internal Database URL**

### 3. Add env var to Backend
1. Open your backend service (karas-chat-backend) on Render
2. Settings → Environment
3. Add: **Key** `DATABASE_URL`, **Value** = the URL you copied
4. Save (Render will redeploy automatically)

### 4. Deploy backend
Push your code or trigger Manual Deploy. The backend will use Postgres for invite links.

---

## After setup
- Invite links persist across restarts
- Create new invite link and test
