/**
 * واجهة التخزين: إذا وُجد MONGODB_URI نستخدم MongoDB (تخزين دائم).
 * وإلا نستخدم الملف (lowdb).
 */
const dbLowdb = require('./db-lowdb');
const path = require('path');
const os = require('os');

if (process.env.MONGODB_URI) {
  console.log('استخدام MongoDB للتخزين الدائم (MONGODB_URI مضبوط).');
  module.exports = require('./db-mongo');
  return;
}

if (process.env.PORT && !process.env.DB_PATH) {
  console.warn('');
  console.warn('*** تحذير: DB_PATH غير مضبوط. البيانات ستُفقد عند إعادة التشغيل أو نوم السيرفر. ***');
  console.warn('*** للتخزين الدائم بدون ترقية Koyeb: ضبط MONGODB_URI (MongoDB Atlas مجاني). ***');
  console.warn('');
}

// تغليف دوال lowdb (sync) لتعيد Promise حتى تكون الواجهة واحدة (async)
function wrapSync(obj) {
  const out = {};
  for (const [key, fn] of Object.entries(obj)) {
    out[key] = (...args) => Promise.resolve(fn.apply(obj, args));
  }
  return out;
}

module.exports = wrapSync(dbLowdb);
