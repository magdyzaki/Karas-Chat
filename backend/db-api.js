/** واجهة موحدة - يستخدم lowdb (ملف) أو Postgres حسب DATABASE_URL */
import { db as lowdb } from './db.js';

export const db = lowdb;
