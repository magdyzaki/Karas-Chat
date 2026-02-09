import path from 'path';
import { fileURLToPath } from 'url';
import multer from 'multer';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const uploadsDir = path.join(__dirname, '..', 'uploads');

const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, uploadsDir),
  filename: (req, file, cb) => {
    const ext = (file.originalname && path.extname(file.originalname)) || '';
    const name = Date.now() + '-' + Math.random().toString(36).slice(2) + (ext || '.bin');
    cb(null, name);
  }
});

export const upload = multer({
  storage,
  limits: { fileSize: 15 * 1024 * 1024 },
  fileFilter: (req, file, cb) => cb(null, true)
});
