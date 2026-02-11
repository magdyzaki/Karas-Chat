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
    const { conversationId, type, content, file_name, reply_to_id, reply_to_snippet } = payload || {};
    if (!conversationId || (!content && type === 'text')) return;
    const conv = db.getConversationByIdAndUser(conversationId, uid);
    if (!conv) return;
    const msg = db.addMessage({
      conversation_id: conversationId,
      sender_id: uid,
      type: type || 'text',
      content: content || '',
      file_name: file_name || null,
      reply_to_id: reply_to_id || null,
      reply_to_snippet: reply_to_snippet || null
    });
    const user = db.findUserById(uid);
    io.to('conv_' + conversationId).emit('new_message', {
      ...msg,
      sender: user ? { id: user.id, name: user.name, email: user.email, phone: user.phone } : null
    });
  });

  socket.on('typing', (data) => {
    const { conversationId } = data || {};
    if (!conversationId) return;
    const user = db.findUserById(uid);
    socket.to('conv_' + conversationId).emit('user_typing', { userId: uid, userName: user ? user.name || user.email || user.phone : 'شخص' });
  });

  socket.on('stop_typing', (data) => {
    const { conversationId } = data || {};
    if (!conversationId) return;
    socket.to('conv_' + conversationId).emit('user_stop_typing', { userId: uid });
  });

  socket.on('mark_read', (data) => {
    const { conversationId, lastMessageId } = data || {};
    if (!conversationId) return;
    const conv = db.getConversationByIdAndUser(conversationId, uid);
    if (!conv) return;
    db.setConversationRead(conversationId, uid, lastMessageId);
    socket.to('conv_' + conversationId).emit('read_receipt', { userId: uid, conversationId: Number(conversationId), lastMessageId: lastMessageId != null ? Number(lastMessageId) : null });
  });

  socket.on('delete_message', (data) => {
    const { conversationId, messageId, forEveryone } = data || {};
    if (!conversationId || !messageId) return;
    const conv = db.getConversationByIdAndUser(conversationId, uid);
    if (!conv) return;
    const payload = { messageId: Number(messageId), conversationId: Number(conversationId) };
    if (forEveryone) {
      const ok = db.deleteMessageForEveryone(messageId, conversationId, uid);
      if (ok) io.to('conv_' + conversationId).emit('message_deleted', payload);
    } else {
      const ok = db.deleteMessageForMe(messageId, conversationId, uid);
      if (ok) socket.emit('message_deleted', payload);
    }
  });

  socket.on('start_call', (data) => {
    const { conversationId } = data || {};
    if (!conversationId) return;
    const conv = db.getConversationByIdAndUser(conversationId, uid);
    if (!conv || conv.type !== 'direct' || !conv.members || conv.members.length !== 2) return;
    const user = db.findUserById(uid);
    socket.to('conv_' + conversationId).emit('incoming_call', {
      conversationId: Number(conversationId),
      fromUserId: uid,
      fromUserName: user ? user.name || user.email || user.phone : 'شخص'
    });
  });

  socket.on('webrtc_signal', (data) => {
    const { conversationId, toUserId, signal } = data || {};
    if (!conversationId || toUserId == null || !signal) return;
    const targetSockets = userSockets.get(Number(toUserId));
    if (targetSockets && targetSockets.size) {
      targetSockets.forEach((sid) => io.to(sid).emit('webrtc_signal', { fromUserId: uid, conversationId: Number(conversationId), signal }));
    }
  });

  socket.on('reject_call', (data) => {
    const { conversationId, callerUserId } = data || {};
    if (!conversationId || callerUserId == null) return;
    const targetSockets = userSockets.get(Number(callerUserId));
    if (targetSockets && targetSockets.size) {
      targetSockets.forEach((sid) => io.to(sid).emit('call_rejected', { conversationId: Number(conversationId) }));
    }
  });

  socket.on('hangup_call', (data) => {
    const { conversationId } = data || {};
    if (!conversationId) return;
    socket.to('conv_' + conversationId).emit('call_ended', { conversationId: Number(conversationId) });
  });

  socket.on('disconnect', () => {
    if (userSockets.has(uid)) {
      userSockets.get(uid).delete(socket.id);
      if (userSockets.get(uid).size === 0) userSockets.delete(uid);
    }
  });
});
