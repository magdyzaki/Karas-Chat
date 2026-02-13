import express from 'express';
import fs from 'fs';
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
import inviteRoutes from './routes/invite.js';
import adminRoutes from './routes/admin.js';
import backupRoutes from './routes/backup.js';
import giphyRoutes from './routes/giphy.js';
import broadcastRoutes from './routes/broadcast.js';
import storyRoutes from './routes/stories.js';
import { pushRoutes, sendPushToUser } from './routes/push.js';
import { jwtVerify } from './middleware/auth.js';
import { upload } from './middleware/upload.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const JWT_SECRET = process.env.JWT_SECRET || 'chat-secret-change-in-production';

const app = express();
app.set('io', null);
const httpServer = createServer(app);
const io = new Server(httpServer, {
  cors: { origin: true, methods: ['GET', 'POST'] }
});

app.use(cors({ origin: true, credentials: true }));
app.use(express.json());
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

app.use('/api/auth', authRoutes);

app.get('/api/dev/last-code', (req, res) => {
  if (process.env.ALLOW_DEV_CODE !== 'true') return res.status(403).json({ error: 'غير مفعّل. أضف ALLOW_DEV_CODE=true في .env' });
  const q = (req.query.q || '').trim();
  if (!q) return res.status(400).json({ error: 'أدخل البريد أو رقم الموبايل في q=' });
  const qNorm = q.replace(/\D/g, '');
  const findKey = (obj) => Object.keys(obj || {}).find((k) => k === q || k.replace(/\D/g, '') === qNorm);
  try {
    const fp = path.join(__dirname, 'last_codes.json');
    if (!fs.existsSync(fp)) return res.json({ code: null, msg: 'لا يوجد رمز محفوظ. افتح ملف last_codes.json في مجلد backend' });
    const data = JSON.parse(fs.readFileSync(fp, 'utf8'));
    const vKey = findKey(data.verification);
    const rKey = findKey(data.reset);
    const v = vKey ? { ...data.verification[vKey], type: 'verification' } : null;
    const r = rKey ? { ...data.reset[rKey], type: 'reset' } : null;
    const latest = !v && !r ? null : (!r ? v : !v ? r : new Date(v.at) > new Date(r.at) ? v : r);
    res.json(latest || { code: null, msg: 'لا يوجد رمز محفوظ. راجع last_codes.json في مجلد backend' });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});
app.use('/api/users', jwtVerify, userRoutes);
app.use('/api/conversations', jwtVerify, convRoutes);
app.use('/api', inviteRoutes);
app.use('/api/admin', adminRoutes);
app.use('/api/backup', jwtVerify, backupRoutes);
app.use('/api/giphy', jwtVerify, giphyRoutes);
app.use('/api/broadcast', jwtVerify, broadcastRoutes);
app.use('/api/stories', jwtVerify, storyRoutes);
app.use('/api/push', jwtVerify, pushRoutes);

app.post('/api/upload', jwtVerify, upload.single('file'), (req, res) => {
  if (!req.file) return res.status(400).json({ error: 'لم يُرفع ملف' });
  const url = '/uploads/' + req.file.filename;
  res.json({ url, filename: req.file.originalname });
});

app.post('/api/upload-avatar', jwtVerify, upload.single('file'), (req, res) => {
  if (!req.file) return res.status(400).json({ error: 'لم يُرفع ملف' });
  const url = '/uploads/' + req.file.filename;
  const user = db.updateUserProfile(req.userId, { avatar_url: url });
  if (!user) return res.status(500).json({ error: 'فشل تحديث البروفايل' });
  res.json({ avatar_url: url });
});

app.set('io', io);
const PORT = process.env.PORT || 5000;
httpServer.listen(PORT, () => console.log('Chat backend on', PORT));

const userSockets = new Map();
const activeGroupCalls = new Map();

io.use((socket, next) => {
  const token = socket.handshake.auth?.token;
  if (!token) return next(new Error('غير مصرح'));
  jwt.verify(token, JWT_SECRET, (err, decoded) => {
    if (err) return next(new Error('رمز غير صالح'));
    if (db.isUserBlocked(decoded.userId)) return next(new Error('تم إيقاف وصولك'));
    socket.userId = decoded.userId;
    next();
  });
});

io.on('connection', (socket) => {
  const uid = socket.userId;
  db.setUserLastSeen(uid);
  if (!userSockets.has(uid)) userSockets.set(uid, new Set());
  userSockets.get(uid).add(socket.id);

  socket.on('join_conversation', (conversationId) => {
    socket.join('conv_' + conversationId);
  });

  socket.on('leave_conversation', (conversationId) => {
    socket.leave('conv_' + conversationId);
  });

  socket.on('send_message', (data) => {
    const { conversationId, type, content, file_name, reply_to_id, reply_to_snippet, encrypted, iv } = data || {};
    if (!conversationId || (!content && (type === 'text' || type === 'poll'))) return;
    const conv = db.getConversationByIdAndUser(conversationId, uid);
    if (!conv) return;
    const msg = db.addMessage({
      conversation_id: conversationId,
      sender_id: uid,
      type: type || 'text',
      content: content || '',
      file_name: file_name || null,
      reply_to_id: reply_to_id || null,
      reply_to_snippet: reply_to_snippet || null,
      encrypted: !!encrypted,
      iv: iv || null
    });
    const user = db.findUserById(uid);
    const payload = { ...msg, sender: user ? { id: user.id, name: user.name, email: user.email, phone: user.phone } : null };
    if (msg.encrypted) payload.sender_public_key = db.getUserPublicKey(uid);
    io.to('conv_' + conversationId).emit('new_message', payload);
    const members = conv.members || db.getMemberIds(conversationId);
    const baseUrl = process.env.BASE_URL || '';
    for (const mid of members) {
      if (Number(mid) === Number(uid)) continue;
      if (db.isConversationMuted(mid, conversationId)) continue;
      const isOnline = userSockets.has(Number(mid));
      if (!isOnline) {
        sendPushToUser(mid, {
          title: 'رسالة جديدة',
          body: (user?.name || user?.email || user?.phone || 'شخص') + ': ' + (msg.type === 'text' ? (msg.content || '').slice(0, 50) : 'وسائط'),
          tag: 'chat-' + conversationId,
          data: { url: baseUrl + '/', conversationId }
        }).catch(() => {});
      }
    }
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

  socket.on('add_reaction', (data) => {
    const { messageId, conversationId, emoji } = data || {};
    if (!messageId || !conversationId || !emoji) return;
    const conv = db.getConversationByIdAndUser(conversationId, uid);
    if (!conv) return;
    if (!db.isMessageInConversation(messageId, conversationId)) return;
    db.addMessageReaction(messageId, uid, emoji);
    io.to('conv_' + conversationId).emit('reaction_added', { messageId: Number(messageId), userId: uid, emoji: String(emoji).slice(0, 10) });
  });

  socket.on('remove_reaction', (data) => {
    const { messageId, conversationId } = data || {};
    if (!messageId || !conversationId) return;
    const conv = db.getConversationByIdAndUser(conversationId, uid);
    if (!conv) return;
    db.removeMessageReaction(messageId, uid);
    io.to('conv_' + conversationId).emit('reaction_removed', { messageId: Number(messageId), userId: uid });
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
    const { conversationId, toUserId } = data || {};
    if (!conversationId) return;
    const conv = db.getConversationByIdAndUser(conversationId, uid);
    if (!conv || !conv.members || conv.members.length < 2) return;
    const targetId = conv.type === 'direct'
      ? conv.members.find((m) => Number(m) !== Number(uid))
      : (toUserId != null ? Number(toUserId) : null);
    if (targetId == null) return;
    const user = db.findUserById(uid);
    const payload = {
      conversationId: Number(conversationId),
      fromUserId: uid,
      fromUserName: user ? user.name || user.email || user.phone : 'شخص'
    };
    const targetSockets = userSockets.get(Number(targetId));
    if (targetSockets && targetSockets.size) {
      targetSockets.forEach((sid) => io.to(sid).emit('incoming_call', payload));
    } else {
      const baseUrl = process.env.BASE_URL || '';
      sendPushToUser(targetId, {
        title: 'مكالمة واردة',
        body: (user?.name || user?.email || user?.phone || 'شخص') + ' يتصل بك',
        tag: 'call-' + conversationId,
        data: { url: baseUrl + '/', conversationId, fromUserId: uid, type: 'call' }
      }).catch(() => {});
    }
  });

  socket.on('webrtc_signal', (data) => {
    const { conversationId, toUserId, signal } = data || {};
    if (!conversationId || toUserId == null || !signal) return;
    const targetSockets = userSockets.get(Number(toUserId));
    if (targetSockets && targetSockets.size) {
      targetSockets.forEach((sid) => io.to(sid).emit('webrtc_signal', { fromUserId: uid, conversationId: Number(conversationId), signal }));
    }
  });

  socket.on('answer_call', (data) => {
    const { conversationId, callerUserId } = data || {};
    if (!conversationId || !callerUserId) return;
    const targetSockets = userSockets.get(Number(callerUserId));
    if (targetSockets && targetSockets.size) {
      targetSockets.forEach((sid) => io.to(sid).emit('call_answered', { conversationId: Number(conversationId), calleeUserId: uid }));
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

  socket.on('start_group_call', (data) => {
    const { conversationId } = data || {};
    if (!conversationId) return;
    const conv = db.getConversationByIdAndUser(conversationId, uid);
    if (!conv || conv.type !== 'group' || !conv.members || conv.members.length < 2) return;
    const cid = Number(conversationId);
    if (!activeGroupCalls.has(cid)) activeGroupCalls.set(cid, new Set());
    activeGroupCalls.get(cid).add(uid);
    const user = db.findUserById(uid);
    const payload = {
      conversationId: cid,
      initiatorId: uid,
      initiatorName: user ? user.name || user.email || user.phone : 'شخص',
      participants: Array.from(activeGroupCalls.get(cid))
    };
    socket.emit('group_call_started', payload);
    socket.to('conv_' + cid).emit('group_call_started', payload);
  });

  socket.on('join_group_call', (data) => {
    const { conversationId } = data || {};
    if (!conversationId) return;
    const conv = db.getConversationByIdAndUser(conversationId, uid);
    if (!conv) return;
    const cid = Number(conversationId);
    if (!activeGroupCalls.has(cid)) return;
    const participants = activeGroupCalls.get(cid);
    participants.add(uid);
    const user = db.findUserById(uid);
    io.to('conv_' + cid).emit('group_call_user_joined', {
      conversationId: cid,
      userId: uid,
      userName: user ? user.name || user.email || user.phone : 'شخص',
      participants: Array.from(participants)
    });
    socket.emit('group_call_you_joined', {
      conversationId: cid,
      participants: Array.from(participants).filter((id) => id !== uid)
    });
  });

  socket.on('leave_group_call', (data) => {
    const { conversationId } = data || {};
    if (!conversationId) return;
    const cid = Number(conversationId);
    if (!activeGroupCalls.has(cid)) return;
    const participants = activeGroupCalls.get(cid);
    participants.delete(uid);
    if (participants.size === 0) {
      activeGroupCalls.delete(cid);
    }
    io.to('conv_' + cid).emit('group_call_user_left', {
      conversationId: cid,
      userId: uid,
      participants: Array.from(participants)
    });
  });

  socket.on('disconnect', () => {
    db.setUserLastSeen(uid);
    if (userSockets.has(uid)) {
      userSockets.get(uid).delete(socket.id);
      if (userSockets.get(uid).size === 0) userSockets.delete(uid);
    }
    for (const [cid, participants] of activeGroupCalls.entries()) {
      if (participants.has(uid)) {
        participants.delete(uid);
        if (participants.size === 0) activeGroupCalls.delete(cid);
        io.to('conv_' + cid).emit('group_call_user_left', { conversationId: cid, userId: uid, participants: Array.from(participants) });
      }
    }
  });
});
