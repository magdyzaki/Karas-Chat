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

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const JWT_SECRET = process.env.JWT_SECRET || 'karas-secret-change-me';

process.on('unhandledRejection', (reason) => {
  if (reason?.code === 'ECONNRESET') return;
  console.error('Unhandled Rejection:', reason);
});
const app = express();
const httpServer = createServer(app);
httpServer.on('clientError', (err, sock) => {
  if (err.code === 'ECONNRESET') return;
  sock.end('HTTP/1.1 400 Bad Request\r\n\r\n');
});
const io = new Server(httpServer, { cors: { origin: true } });

app.use(cors({ origin: true, credentials: true }));
app.use(express.json());

app.use('/api/auth', authRoutes);
app.use('/api/users', jwtVerify, userRoutes);
app.use('/api/conversations', jwtVerify, convRoutes);

app.set('io', io);
const PORT = process.env.PORT || 5002;

function shutdown(signal) {
  console.log(signal, '- إغلاق السيرفر...');
  httpServer.close(() => { console.log('تم الإغلاق'); process.exit(0); });
}
process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));

const userSockets = new Map();

io.use((socket, next) => {
  const token = socket.handshake.auth?.token;
  if (!token) return next(new Error('غير مصرح'));
  jwt.verify(token, JWT_SECRET, (err, d) => {
    if (err) return next(new Error('رمز غير صالح'));
    if (db.isUserBlocked(d.userId)) return next(new Error('تم إيقافك'));
    socket.userId = d.userId;
    next();
  });
});

io.on('connection', (socket) => {
  const uid = socket.userId;
  db.setUserLastSeen(uid);
  if (!userSockets.has(uid)) userSockets.set(uid, new Set());
  userSockets.get(uid).add(socket.id);

  socket.on('join_conversation', (id) => socket.join('conv_' + id));
  socket.on('leave_conversation', (id) => socket.leave('conv_' + id));

  socket.on('send_message', (data) => {
    const { conversationId, type, content, file_name } = data || {};
    if (!conversationId || (!content && type === 'text')) return;
    const conv = db.getConversationByIdAndUser(conversationId, uid);
    if (!conv) return;
    const msg = db.addMessage({ conversation_id: conversationId, sender_id: uid, type: type || 'text', content: content || '', file_name: file_name || null });
    const user = db.findUserById(uid);
    const payload = { ...msg, sender: user ? { id: user.id, name: user.name, email: user.email, phone: user.phone } : null };
    io.to('conv_' + conversationId).emit('new_message', payload);
  });

  socket.on('start_call', (data) => {
    const { conversationId, toUserId, isVideo } = data || {};
    if (!conversationId || toUserId == null) return;
    const conv = db.getConversationByIdAndUser(conversationId, uid);
    if (!conv || !conv.members?.includes(Number(toUserId))) return;
    const user = db.findUserById(uid);
    const targetSockets = userSockets.get(Number(toUserId));
    const payload = { conversationId: Number(conversationId), fromUserId: uid, fromUserName: user?.name || user?.phone || 'شخص', isVideo: !!isVideo };
    if (targetSockets?.size) targetSockets.forEach((sid) => io.to(sid).emit('incoming_call', payload));
  });

  socket.on('webrtc_signal', (data) => {
    const { toUserId, signal } = data || {};
    if (toUserId == null || !signal) return;
    const targetSockets = userSockets.get(Number(toUserId));
    if (targetSockets?.size) targetSockets.forEach((sid) => io.to(sid).emit('webrtc_signal', { fromUserId: uid, signal }));
  });

  socket.on('answer_call', (data) => {
    const { callerUserId } = data || {};
    if (callerUserId == null) return;
    const targetSockets = userSockets.get(Number(callerUserId));
    if (targetSockets?.size) targetSockets.forEach((sid) => io.to(sid).emit('call_answered', { calleeUserId: uid }));
  });

  socket.on('reject_call', (data) => {
    const { callerUserId } = data || {};
    if (callerUserId == null) return;
    const targetSockets = userSockets.get(Number(callerUserId));
    if (targetSockets?.size) targetSockets.forEach((sid) => io.to(sid).emit('call_rejected'));
  });

  socket.on('hangup_call', (data) => {
    const convId = data?.conversationId;
    if (convId) socket.to('conv_' + convId).emit('call_ended');
  });

  socket.on('disconnect', () => {
    db.setUserLastSeen(uid);
    if (userSockets.has(uid)) {
      userSockets.get(uid).delete(socket.id);
      if (userSockets.get(uid).size === 0) userSockets.delete(uid);
    }
  });
});

httpServer.listen(PORT, () => console.log('Karas Chat backend على المنفذ', PORT));
