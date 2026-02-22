import express from 'express';
import { createServer } from 'http';
import { Server } from 'socket.io';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';
import jwt from 'jsonwebtoken';
import { db } from './db.js';
import authRoutes from './routes/auth.js';
import userRoutes from './routes/users.js';
import convRoutes from './routes/conversations.js';
import { jwtVerify } from './middleware/auth.js';
import { upload } from './middleware/upload.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const JWT_SECRET = process.env.JWT_SECRET || 'chat-secret-change-in-production';

const app = express();
const httpServer = createServer(app);
const io = new Server(httpServer, {
  cors: { origin: true, methods: ['GET', 'POST'] }
});

app.use(cors({ origin: true, credentials: true }));
app.use(express.json());
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

app.use('/api/auth', authRoutes);
app.use('/api/users', jwtVerify, userRoutes);
app.use('/api/conversations', jwtVerify, convRoutes);

app.post('/api/upload', jwtVerify, upload.single('file'), (req, res) => {
  if (!req.file) return res.status(400).json({ error: 'لم يُرفع ملف' });
  const url = '/uploads/' + req.file.filename;
  res.json({ url, filename: req.file.originalname });
});

const PORT = process.env.PORT || 5000;
httpServer.listen(PORT, () => console.log('Chat backend on', PORT));

const userSockets = new Map();

io.use((socket, next) => {
  const token = socket.handshake.auth?.token;
  if (!token) return next(new Error('غير مصرح'));
  jwt.verify(token, JWT_SECRET, (err, decoded) => {
    if (err) return next(new Error('رمز غير صالح'));
    socket.userId = decoded.userId;
    next();
  });
});

io.on('connection', (socket) => {
  const uid = socket.userId;
  if (!userSockets.has(uid)) userSockets.set(uid, new Set());
  userSockets.get(uid).add(socket.id);

  socket.on('join_conversation', (conversationId) => {
    socket.join('conv_' + conversationId);
  });

  socket.on('leave_conversation', (conversationId) => {
    socket.leave('conv_' + conversationId);
  });

  socket.on('send_message', (payload) => {
    const { conversationId, type, content, file_name } = payload || {};
    if (!conversationId || (!content && type === 'text')) return;
    const conv = db.getConversationByIdAndUser(conversationId, uid);
    if (!conv) return;
    const msg = db.addMessage({
      conversation_id: conversationId,
      sender_id: uid,
      type: type || 'text',
      content: content || '',
      file_name: file_name || null
    });
    const user = db.findUserById(uid);
    io.to('conv_' + conversationId).emit('new_message', {
      ...msg,
      sender: user ? { id: user.id, name: user.name, email: user.email, phone: user.phone } : null
    });
  });

  socket.on('disconnect', () => {
    if (userSockets.has(uid)) {
      userSockets.get(uid).delete(socket.id);
      if (userSockets.get(uid).size === 0) userSockets.delete(uid);
    }
  });
});
