import { useState, useEffect, useRef, useMemo } from 'react';
import EmojiPicker from 'emoji-picker-react';
import * as api from './api';

function PollCreateModal({ onClose, onSent }) {
  const [question, setQuestion] = useState('');
  const [options, setOptions] = useState(['', '']);
  const addOpt = () => { if (options.length < 10) setOptions((o) => [...o, '']); };
  const rmOpt = (i) => { if (options.length > 2) setOptions((o) => o.filter((_, j) => j !== i)); };
  const handleSubmit = (e) => {
    e.preventDefault();
    const opts = options.filter((o) => String(o).trim());
    if (!question.trim() || opts.length < 2) return;
    onSent(JSON.stringify({ question: question.trim(), options: opts }));
  };
  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 150 }} onClick={onClose}>
      <div style={{ background: 'var(--surface)', borderRadius: 12, padding: 20, maxWidth: 360, width: '100%', border: '1px solid var(--border)' }} onClick={(e) => e.stopPropagation()}>
        <h3 style={{ margin: '0 0 12px' }}>استطلاع جديد</h3>
        <form onSubmit={handleSubmit}>
          <input type="text" value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="السؤال" required style={{ width: '100%', padding: 10, marginBottom: 12, border: '1px solid var(--border)', borderRadius: 8, background: 'var(--bg)', color: 'var(--text)' }} />
          {options.map((opt, i) => (
            <div key={i} style={{ display: 'flex', gap: 4, marginBottom: 8 }}>
              <input type="text" value={opt} onChange={(e) => setOptions((o) => o.map((x, j) => j === i ? e.target.value : x))} placeholder={`الخيار ${i + 1}`} style={{ flex: 1, padding: 8, border: '1px solid var(--border)', borderRadius: 8, background: 'var(--bg)', color: 'var(--text)' }} />
              <button type="button" onClick={() => rmOpt(i)} style={{ padding: '8px 12px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', cursor: 'pointer' }}>−</button>
            </div>
          ))}
          {options.length < 10 && <button type="button" onClick={addOpt} style={{ marginBottom: 12, padding: '6px 12px', fontSize: 12, background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', cursor: 'pointer' }}>+ خيار</button>}
          <div style={{ display: 'flex', gap: 8 }}>
            <button type="submit" style={{ padding: '10px 20px', background: 'var(--primary)', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer' }}>إرسال</button>
            <button type="button" onClick={onClose} style={{ padding: '10px 20px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', cursor: 'pointer' }}>إلغاء</button>
          </div>
        </form>
      </div>
    </div>
  );
}
import GroupInfo from './GroupInfo';
import CallModal from './CallModal';
import WebRTCCall from './WebRTCCall';
import GifPicker from './GifPicker';
import * as e2e from './e2e';
import { playSent, stopCallRing } from './sounds';

const styles = {
  room: { flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', borderRight: '1px solid var(--border)' },
  header: { padding: 12, borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 12 },
  backBtn: { padding: '6px 12px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', cursor: 'pointer' },
  messages: { flex: 1, overflow: 'auto', padding: 16, display: 'flex', flexDirection: 'column', gap: 8 },
  msg: { maxWidth: '80%', padding: '10px 14px', borderRadius: 12, alignSelf: 'flex-start', wordBreak: 'break-word' },
  msgOwn: { alignSelf: 'flex-end', background: 'var(--msg-bg-own, var(--primary))', color: 'var(--msg-text-own)' },
  msgOther: { background: 'var(--msg-bg-other)', color: 'var(--msg-text-other, var(--text))', border: '1px solid var(--border)' },
  msgMeta: { fontSize: 11, opacity: 0.8, marginTop: 4 },
  form: { padding: 12, borderTop: '1px solid var(--border)', display: 'flex', gap: 6, alignItems: 'flex-end', flexWrap: 'wrap' },
  input: { flex: 1, minWidth: 120, padding: '10px 14px', border: '1px solid var(--border)', borderRadius: 8, background: 'var(--bg)', color: 'var(--text)', fontSize: 15, minHeight: 44, textAlign: 'right' },
  sendBtn: { padding: '10px 20px', border: 'none', borderRadius: 8, background: 'var(--primary)', color: '#fff', cursor: 'pointer', fontSize: 15 },
  fileBtn: { padding: 10, border: '1px solid var(--border)', borderRadius: 8, background: 'var(--surface)', color: 'var(--text)', cursor: 'pointer', fontSize: 18 },
  img: { maxWidth: '100%', maxHeight: 200, borderRadius: 8, marginTop: 4 },
  link: { color: 'var(--primary)', wordBreak: 'break-all' }
};

export default function ChatRoom({ conversation, conversations = [], socket, currentUserId, onBack, onMembersUpdated }) {
  const [messages, setMessages] = useState([]);
  const [convDetails, setConvDetails] = useState(conversation);
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(true);
  const [fileError, setFileError] = useState('');
  const [showGroupInfo, setShowGroupInfo] = useState(false);
  const [showEmoji, setShowEmoji] = useState(false);
  const [optimisticVersion, setOptimisticVersion] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [callState, setCallState] = useState(null);
  const [typingUser, setTypingUser] = useState(null);
  const [replyTo, setReplyTo] = useState(null);
  const [msgMenuId, setMsgMenuId] = useState(null);
  const [groupCallParticipants, setGroupCallParticipants] = useState(null);
  const [readReceipts, setReadReceipts] = useState([]);
  const [reactions, setReactions] = useState({});
  const [pollVotes, setPollVotes] = useState([]);
  const [showPollCreate, setShowPollCreate] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [showForward, setShowForward] = useState(null);
  const [showGifPicker, setShowGifPicker] = useState(false);
  const [webrtcCall, setWebrtcCall] = useState(null);
  const [e2eReady, setE2eReady] = useState(false);
  const [e2eTheirKey, setE2eTheirKey] = useState(null);
  const [decryptedMap, setDecryptedMap] = useState({});
  const typingTimeoutRef = useRef(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const imageInputRef = useRef(null);
  const videoInputRef = useRef(null);
  const emojiWrapRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const optimisticRef = useRef([]);
  const sentPlaintextQueueRef = useRef([]);

  useEffect(() => {
    if (!conversation?.id) return;
    setConvDetails(conversation);
    optimisticRef.current = [];
    setDecryptedMap({});
    setLoading(true);
    api.getMessages(conversation.id).then((data) => {
      const { messages: list = [], readReceipts: rr = [], reactions: rx = [], pollVotes: pv = [] } = typeof data === 'object' && data ? data : { messages: [], readReceipts: [], reactions: [], pollVotes: [] };
      setMessages(Array.isArray(list) ? list : []);
      setReadReceipts(Array.isArray(rr) ? rr : []);
      const byMsg = {};
      (Array.isArray(rx) ? rx : []).forEach((r) => { if (!byMsg[r.message_id]) byMsg[r.message_id] = []; byMsg[r.message_id].push(r); });
      setReactions(byMsg);
      setPollVotes(Array.isArray(pv) ? pv : []);
      setLoading(false);
    }).catch(() => setLoading(false));
    api.getConversation(conversation.id).then((c) => setConvDetails(c)).catch(() => {});
  }, [conversation?.id]);

  const isGroupConv = convDetails?.type === 'group';
  const membersList = convDetails?.members || convDetails?.memberIds || conversation?.members || conversation?.memberIds || [];
  const otherUserIdConv = !isGroupConv && membersList.length ? membersList.find((m) => Number(m) !== Number(currentUserId)) : null;

  useEffect(() => {
    if (!conversation?.id || isGroupConv || !otherUserIdConv) {
      setE2eReady(false);
      setE2eTheirKey(null);
      setDecryptedMap({});
      return;
    }
    (async () => {
      try {
        const { publicKey } = await e2e.initE2EKeys();
        if (!publicKey) return;
        await api.setMyE2EPublicKey(publicKey);
        const theirKey = await api.getUserE2EPublicKey(otherUserIdConv);
        setE2eTheirKey(theirKey);
        setE2eReady(!!theirKey);
      } catch (_) {
        setE2eReady(false);
      }
    })();
  }, [conversation?.id, isGroupConv, otherUserIdConv]);

  useEffect(() => {
    const enc = (messages || []).filter((m) => m.encrypted && m.content && m.iv && m.sender_public_key && !m.deleted);
    if (enc.length === 0) return;
    let cancelled = false;
    enc.forEach(async (m) => {
      const dec = await e2e.decryptFromUser(m.content, m.iv, m.sender_public_key);
      if (!cancelled && dec != null) setDecryptedMap((prev) => (prev[m.id] ? prev : { ...prev, [m.id]: dec }));
    });
    return () => { cancelled = true; };
  }, [messages]);

  const lastRealMessageIdRef = useRef(null);
  useEffect(() => {
    if (!socket || !conversation?.id) return;
    const real = (messages || []).filter((m) => m.id && !String(m.id).startsWith('temp-'));
    const last = real[real.length - 1];
    const lastId = last?.id ?? null;
    if (lastId !== lastRealMessageIdRef.current) {
      lastRealMessageIdRef.current = lastId;
      socket.emit('mark_read', { conversationId: conversation.id, lastMessageId: lastId });
    }
  }, [conversation?.id, socket, messages]);

  useEffect(() => {
    if (socket && conversation?.id) {
      socket.emit('join_conversation', conversation.id);
      const onNew = (msg) => {
        if (msg.conversation_id !== conversation.id) return;
        const isOwn = Number(msg.sender_id) === Number(currentUserId);
        if (isOwn && msg.encrypted && sentPlaintextQueueRef.current.length > 0) {
          const plain = sentPlaintextQueueRef.current.shift();
          setDecryptedMap((prev) => ({ ...prev, [msg.id]: plain }));
          let idx = -1;
          for (let i = optimisticRef.current.length - 1; i >= 0; i--) {
            if (String(optimisticRef.current[i].sender_id) === String(currentUserId) && optimisticRef.current[i].type === 'text') {
              idx = i;
              break;
            }
          }
          if (idx >= 0) optimisticRef.current.splice(idx, 1);
        } else {
          optimisticRef.current = optimisticRef.current.filter(
            (o) => !(o.content === msg.content && o.sender_id === msg.sender_id && o.type === msg.type)
          );
        }
        setOptimisticVersion((v) => v + 1);
        setMessages((prev) => [...prev, msg]);
      };
      const onCallRejected = (data) => {
        if (data.conversationId === conversation.id) { setCallState(null); setWebrtcCall(null); stopCallRing(); }
      };
      const onCallAnswered = (data) => {
        if (data.conversationId !== conversation.id) return;
        setWebrtcCall({ remoteUserId: data.calleeUserId, isVideo: callState?.isVoice === false });
      };
      const onCallEnded = (data) => {
        if (data.conversationId === conversation.id) { setCallState(null); setWebrtcCall(null); stopCallRing(); }
      };
      const onTyping = (data) => {
        if (Number(data.userId) === Number(currentUserId)) return;
        setTypingUser({ id: data.userId, name: data.userName });
      };
      const onStopTyping = (data) => {
        if (Number(data.userId) === Number(currentUserId)) return;
        setTypingUser(null);
      };
      const onDeleted = (data) => {
        if (data.conversationId !== conversation.id) return;
        const { messageId } = data;
        setMessages((prev) => prev.map((m) => (m.id === messageId || String(m.id) === String(messageId)) ? { ...m, content: '', type: 'text', deleted: true } : m));
        setMsgMenuId(null);
      };
      const onReadReceipt = (data) => {
        if (data.conversationId !== conversation.id) return;
        setReadReceipts((prev) => {
          const rest = prev.filter((r) => r.user_id !== data.userId);
          if (data.lastMessageId != null) rest.push({ user_id: data.userId, last_message_id: data.lastMessageId });
          return rest;
        });
      };
      const onReactionAdded = (data) => {
        const { messageId, userId, emoji } = data;
        setReactions((prev) => {
          const list = (prev[messageId] || []).filter((r) => r.user_id !== userId);
          return { ...prev, [messageId]: [...list, { message_id: messageId, user_id: userId, emoji }] };
        });
      };
      const onReactionRemoved = (data) => {
        const { messageId, userId } = data;
        setReactions((prev) => {
          const list = (prev[messageId] || []).filter((r) => r.user_id !== userId);
          if (list.length === 0) { const next = { ...prev }; delete next[messageId]; return next; }
          return { ...prev, [messageId]: list };
        });
      };
      const onPollVoted = (data) => {
        if (data.conversationId !== conversation.id) return;
        setPollVotes((prev) => prev.filter((v) => !(v.message_id === data.messageId && v.user_id === data.userId)).concat([{ message_id: data.messageId, user_id: data.userId, option_index: data.optionIndex }]));
      };
      socket.on('new_message', onNew);
      socket.on('message_deleted', onDeleted);
      const onGroupCallStarted = (data) => {
        if (data.conversationId !== conversation.id) return;
        setGroupCallParticipants(data.participants || []);
      };
      const onGroupCallUserJoined = (data) => {
        if (data.conversationId !== conversation.id) return;
        setGroupCallParticipants(data.participants || []);
      };
      const onGroupCallUserLeft = (data) => {
        if (data.conversationId !== conversation.id) return;
        setGroupCallParticipants((p) => (data.participants && data.participants.length > 0) ? data.participants : null);
      };
      socket.on('group_call_started', onGroupCallStarted);
      socket.on('group_call_user_joined', onGroupCallUserJoined);
      socket.on('group_call_user_left', onGroupCallUserLeft);
      socket.on('user_typing', onTyping);
      socket.on('user_stop_typing', onStopTyping);
      socket.on('call_answered', onCallAnswered);
      socket.on('call_rejected', onCallRejected);
      socket.on('call_ended', onCallEnded);
      socket.on('read_receipt', onReadReceipt);
      socket.on('reaction_added', onReactionAdded);
      socket.on('reaction_removed', onReactionRemoved);
      socket.on('poll_voted', onPollVoted);
      return () => {
        socket.off('new_message', onNew);
        socket.off('message_deleted', onDeleted);
        socket.off('read_receipt', onReadReceipt);
        socket.off('reaction_added', onReactionAdded);
        socket.off('reaction_removed', onReactionRemoved);
        socket.off('poll_voted', onPollVoted);
        socket.off('group_call_started', onGroupCallStarted);
        socket.off('group_call_user_joined', onGroupCallUserJoined);
        socket.off('group_call_user_left', onGroupCallUserLeft);
        socket.off('user_typing', onTyping);
        socket.off('user_stop_typing', onStopTyping);
        socket.off('call_answered', onCallAnswered);
        socket.off('call_rejected', onCallRejected);
        socket.off('call_ended', onCallEnded);
        socket.emit('leave_conversation', conversation.id);
      };
    }
  }, [conversation?.id, socket, callState?.targetId, callState?.isVoice]);

  useEffect(() => {
    const close = (e) => {
      if (emojiWrapRef.current && !emojiWrapRef.current.contains(e.target)) setShowEmoji(false);
      if (msgMenuId && !e.target.closest('[data-msg-id]')) setMsgMenuId(null);
    };
    document.addEventListener('click', close);
    return () => document.removeEventListener('click', close);
  }, [msgMenuId]);

  const displayMessages = useMemo(() => {
    const fromServer = messages || [];
    const pending = optimisticRef.current || [];
    const serverIds = new Set(fromServer.map((m) => m.id));
    const extra = pending.filter((p) => !serverIds.has(p.id));
    let list = [...fromServer, ...extra].sort((a, b) => new Date(a.created_at || 0) - new Date(b.created_at || 0));
    const q = (searchQuery || '').trim().toLowerCase();
    if (q) {
      const keys = { image: ['صورة', 'image', 'صور', 'gif'], video: ['فيديو', 'video'], voice: ['صوت', 'voice', 'رسالة صوتية'], location: ['موقع', 'location'] };
      list = list.filter((m) => {
        if (m.deleted) return false;
        const textContent = m.type === 'text' ? (m.encrypted ? (decryptedMap[m.id] || '') : (m.content || '')) : '';
        if (m.type === 'text' && textContent.toLowerCase().includes(q)) return true;
        if (m.type === 'image' && keys.image.some((k) => k.includes(q) || q.includes(k))) return true;
        if (m.type === 'video' && keys.video.some((k) => k.includes(q) || q.includes(k))) return true;
        if (m.type === 'voice' && keys.voice.some((k) => k.includes(q) || q.includes(k))) return true;
        if (m.type === 'location' && keys.location.some((k) => k.includes(q) || q.includes(k))) return true;
        if ((m.file_name || '').toLowerCase().includes(q)) return true;
        return false;
      });
    }
    return list;
  }, [messages, optimisticVersion, searchQuery, decryptedMap]);

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [displayMessages]);

  const emitTyping = () => {
    if (!socket || !conversation?.id) return;
    socket.emit('typing', { conversationId: conversation.id });
    if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
    typingTimeoutRef.current = setTimeout(() => {
      socket?.emit('stop_typing', { conversationId: conversation.id });
      typingTimeoutRef.current = null;
    }, 2000);
  };

  const handleDeleteMsg = (msg, forEveryone) => {
    if (!socket || !conversation?.id) return;
    socket.emit('delete_message', { conversationId: conversation.id, messageId: msg.id, forEveryone });
    if (!forEveryone) setMessages((prev) => prev.filter((m) => m.id !== msg.id && String(m.id) !== String(msg.id)));
    setMsgMenuId(null);
  };

  const getMsgSnippet = (m) => {
    if (m.deleted) return 'رسالة محذوفة';
    if (m.type === 'poll') { try { const p = JSON.parse(m.content || '{}'); return '📊 ' + (p.question || 'استطلاع'); } catch (_) { return '📊 استطلاع'; } }
    if (m.type === 'text') return (m.encrypted ? (decryptedMap[m.id] || 'رسالة مشفرة') : (m.content || '')).slice(0, 50) || 'رسالة';
    if (m.type === 'image') return '🖼 صورة';
    if (m.type === 'video') return '🎬 فيديو';
    if (m.type === 'voice') return '🎤 رسالة صوتية';
    if (m.type === 'location') return '📍 موقع';
    return m.file_name || 'ملف';
  };

  const sendMessage = async (type = 'text', content, file_name = null, replyToMsg = null) => {
    if (!content && type === 'text') return;
    const tempId = 'temp-' + Date.now();
    const tempMsg = { id: tempId, content, sender_id: currentUserId, type: type === 'text' ? 'text' : type, file_name, reply_to_id: replyToMsg?.id, reply_to_snippet: replyToMsg ? getMsgSnippet(replyToMsg) : null, created_at: new Date().toISOString(), sender: null };
    optimisticRef.current = [...optimisticRef.current, tempMsg];
    setOptimisticVersion((v) => v + 1);
    if (type === 'text') setText('');
    setReplyTo(null);
    if (typingTimeoutRef.current) { clearTimeout(typingTimeoutRef.current); typingTimeoutRef.current = null; }
    let payload = { conversationId: conversation.id, type, content, file_name };
    if (replyToMsg) { payload.reply_to_id = replyToMsg.id; payload.reply_to_snippet = getMsgSnippet(replyToMsg); }
    if (type === 'text' && e2eReady && e2eTheirKey) {
      try {
        sentPlaintextQueueRef.current.push(content);
        const { content: cipher, iv } = await e2e.encryptForUser(content, e2eTheirKey);
        payload = { ...payload, content: cipher, encrypted: true, iv };
      } catch (_) {
        setFileError('فشل التشفير');
        return;
      }
    }
    if (socket) { socket.emit('stop_typing', { conversationId: conversation.id }); socket.emit('send_message', payload); }
    playSent();
  };

  const handleFile = async (e, imageOnly = false, replyToMsg = null) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileError('');
    try {
      const { url, filename } = await api.uploadFile(file);
      const fullUrl = api.uploadsUrl(url);
      const type = (file.type || '').startsWith('image/') ? 'image' : (file.type || '').startsWith('video/') ? 'video' : (file.type || '').startsWith('audio/') ? 'voice' : 'file';
      sendMessage(type, fullUrl, filename || (type === 'voice' ? 'رسالة صوتية' : file.name), replyToMsg ?? replyTo);
    } catch (err) {
      setFileError(err.message || 'فشل رفع الملف');
    }
    e.target.value = '';
  };

  const handleLocation = () => {
    if (!navigator.geolocation) { setFileError('المتصفح لا يدعم الموقع'); return; }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords;
        const url = `https://www.google.com/maps?q=${latitude},${longitude}`;
        const label = `📍 موقعي: ${latitude.toFixed(4)}, ${longitude.toFixed(4)}`;
        sendMessage('location', `${label}\n${url}`, null, replyTo);
      },
      () => setFileError('فشل الحصول على الموقع')
    );
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      audioChunksRef.current = [];
      mr.ondataavailable = (e) => { if (e.data.size) audioChunksRef.current.push(e.data); };
      mr.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        if (audioChunksRef.current.length === 0) return;
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const file = new File([blob], 'voice.webm', { type: 'audio/webm' });
        const fakeEvent = { target: { files: [file] } };
        handleFile(fakeEvent, false, replyTo ?? undefined);
      };
      mediaRecorderRef.current = mr;
      mr.start();
      setIsRecording(true);
    } catch (err) {
      setFileError(err.message || 'فشل تشغيل الميكروفون');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current = null;
    }
    setIsRecording(false);
  };

  const startCall = (isVoice) => {
    const targetId = convDetails?.type === 'direct'
      ? (convDetails?.members || []).find((m) => Number(m) !== Number(currentUserId))
      : null;
    if (!targetId) return;
    setCallState({ isVoice, targetId });
    socket?.emit('start_call', { conversationId: conversation.id, toUserId: targetId, isVideo: !isVoice });
  };

  const handleRemoveMember = async (convId, memberId) => {
    try {
      await api.removeMemberFromGroup(convId, memberId);
      const updated = await api.getConversation(convId);
      setConvDetails(updated);
      onMembersUpdated?.();
    } catch (_) {}
  };

  if (!conversation) return null;
  const isGroup = convDetails?.type === 'group';
  const otherUserId = !isGroup && convDetails?.members ? convDetails.members.find((m) => Number(m) !== Number(currentUserId)) : null;
  const theme = typeof document !== 'undefined' && document.documentElement?.getAttribute('data-theme') === 'light' ? 'light' : 'dark';

  return (
    <div className="chat-room-inner" style={styles.room}>
      <div className="chat-header-bar" style={styles.header}>
        <button type="button" style={styles.backBtn} onClick={onBack}>← رجوع</button>
        <span style={{ fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1, minWidth: 0 }}>
          {convDetails?.label || convDetails?.name || 'محادثة'}
        </span>
        {!isGroup && otherUserId && (convDetails?.memberDetails || []).find((m) => Number(m.id) === Number(otherUserId))?.last_seen_at && (
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>آخر ظهور: {new Date((convDetails?.memberDetails || []).find((m) => Number(m.id) === Number(otherUserId))?.last_seen_at).toLocaleString('ar-EG')}</span>
        )}
        {!isGroup && otherUserId && (
          <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
            {e2eReady && <span style={{ fontSize: 10, color: 'var(--text-muted)' }} title="تشفير من طرف لطرف">🔒</span>}
            <button type="button" onClick={() => startCall(true)} title="مكالمة صوتية" style={{ ...styles.backBtn, padding: '6px 10px', fontSize: 16 }}>📞</button>
            <button type="button" onClick={() => startCall(false)} title="مكالمة فيديو" style={{ ...styles.backBtn, padding: '6px 10px', fontSize: 16 }}>📹</button>
          </div>
        )}
        {isGroup && (
          <>
            <button type="button" onClick={() => { socket?.emit('start_group_call', { conversationId: conversation.id }); }} style={{ ...styles.backBtn, padding: '6px 10px', fontSize: 13 }}>📞 مكالمة</button>
            <button type="button" onClick={() => setShowGroupInfo(true)} style={{ ...styles.backBtn, padding: '6px 10px', fontSize: 13 }}>ℹ️ المجموعة</button>
          </>
        )}
      </div>
      <div style={{ padding: '8px 12px', borderBottom: '1px solid var(--border)' }}>
        <input type="text" placeholder="بحث في الرسائل..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} style={{ width: '100%', padding: '8px 12px', border: '1px solid var(--border)', borderRadius: 8, background: 'var(--bg)', color: 'var(--text)', fontSize: 14, textAlign: 'right' }} />
      </div>
      <div className="chat-msg-area" style={styles.messages}>
        {loading && <p style={{ color: 'var(--text-muted)' }}>جاري التحميل...</p>}
        {displayMessages.map((m) => {
          const isOwn = Number(m.sender_id) === Number(currentUserId);
          return (
            <div key={m.id} data-msg-id={m.id} style={{ ...styles.msg, ...(isOwn ? styles.msgOwn : styles.msgOther) }}>
              {!isOwn && m.sender && <div style={{ fontSize: 12, opacity: 0.9, color: 'var(--msg-sender-color, var(--text))' }}>{m.sender.name || m.sender.email || m.sender.phone} <span style={{ fontSize: 10, opacity: 0.8 }}>(معرف: {m.sender.id})</span></div>}
              {m.reply_to_id && (
                <div style={{ borderRight: '3px solid var(--primary)', paddingRight: 8, marginBottom: 6, opacity: 0.9, fontSize: 12 }}>
                  {m.reply_to_snippet || 'رسالة'}
                </div>
              )}
              {m.type === 'text' && <div style={{ whiteSpace: 'pre-wrap' }}>{m.deleted ? 'رسالة محذوفة' : (m.encrypted ? (decryptedMap[m.id] ?? '...') : m.content)}</div>}
              {m.type === 'image' && !m.deleted && <img src={m.content} alt="" style={styles.img} />}
              {m.type === 'video' && !m.deleted && <video src={m.content} controls playsInline style={{ marginTop: 4, maxWidth: '100%', maxHeight: 300, borderRadius: 8 }} />}
              {m.type === 'voice' && !m.deleted && <audio src={m.content} controls style={{ marginTop: 4, maxWidth: '100%' }} />}
              {m.type === 'location' && !m.deleted && (() => { const parts = String(m.content || '').split('\n'); const label = parts[0] || '📍 الموقع'; const url = (parts[1] || '').startsWith('http') ? parts[1] : `https://www.google.com/maps?q=${encodeURIComponent(m.content)}`; return <div><a href={url} target="_blank" rel="noopener noreferrer" style={styles.link}>{label}</a></div>; })()}
              {m.type === 'file' && !m.deleted && <a href={m.content} target="_blank" rel="noopener noreferrer" style={styles.link}>{m.file_name || 'ملف'}</a>}
              {m.type === 'poll' && !m.deleted && (() => {
                let poll;
                try { poll = typeof m.content === 'string' ? JSON.parse(m.content) : m.content; } catch (_) { return null; }
                const opts = poll?.options || [];
                const votesForMsg = pollVotes.filter((v) => Number(v.message_id) === Number(m.id));
                const counts = opts.map((_, i) => votesForMsg.filter((v) => v.option_index === i).length);
                const total = counts.reduce((a, b) => a + b, 0);
                const myVote = votesForMsg.find((v) => Number(v.user_id) === Number(currentUserId));
                return (
                  <div style={{ marginTop: 4 }}>
                    <div style={{ fontWeight: 500, marginBottom: 8 }}>{poll.question || 'استطلاع'}</div>
                    {opts.map((opt, i) => (
                      <button key={i} type="button" onClick={async () => { if (myVote) return; try { await api.votePoll(conversation.id, m.id, i); setPollVotes((p) => [...p.filter((v) => !(v.message_id === m.id && v.user_id === currentUserId)), { message_id: m.id, user_id: currentUserId, option_index: i }]); } catch (_) {} }} style={{ display: 'block', width: '100%', padding: '8px 12px', marginBottom: 4, border: '1px solid var(--border)', borderRadius: 8, background: myVote?.option_index === i ? 'rgba(var(--primary-rgb,0,123,255),0.2)' : 'var(--bg)', color: 'var(--text)', cursor: myVote ? 'default' : 'pointer', textAlign: 'right' }}>
                        {opt} {total > 0 && <span style={{ fontSize: 11, opacity: 0.8 }}>({counts[i]})</span>}
                      </button>
                    ))}
                  </div>
                );
              })()}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 4, gap: 8, flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <div style={{ ...styles.msgMeta, color: 'var(--msg-meta-color, inherit)', marginTop: 0 }}>{new Date(m.created_at).toLocaleString('ar-EG')}</div>
                  {isOwn && !m.deleted && !String(m.id).startsWith('temp-') && !isGroup && otherUserId && (() => {
                    const rr = readReceipts.find((r) => Number(r.user_id) === Number(otherUserId));
                    const readUpTo = rr?.last_message_id != null ? Number(rr.last_message_id) : -1;
                    const msgId = typeof m.id === 'number' ? m.id : parseInt(m.id, 10);
                    if (isNaN(msgId)) return null;
                    const isRead = readUpTo >= msgId;
                    return isRead ? <span style={{ fontSize: 11, color: 'var(--primary)', fontWeight: 600 }} title="تمت القراءة">✓✓</span> : <span style={{ fontSize: 11, opacity: 0.7 }} title="مرسلة">✓</span>;
                  })()}
                </div>
                <div style={{ display: 'flex', gap: 4 }}>
                  <button type="button" onClick={() => setReplyTo(m)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: 11 }}>↩ رد</button>
                  <button type="button" onClick={() => setMsgMenuId(msgMenuId === m.id ? null : m.id)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: 11 }}>⋮</button>
                </div>
              </div>
              {(reactions[m.id] || []).length > 0 && (
                <div style={{ display: 'flex', gap: 4, marginTop: 4, flexWrap: 'wrap' }}>
                  {(reactions[m.id] || []).map((r) => (
                    <span key={r.user_id} style={{ fontSize: 14 }} title={`معرف ${r.user_id}`}>{r.emoji}</span>
                  ))}
                </div>
              )}
              {msgMenuId === m.id && (
                <div style={{ marginTop: 6, padding: 4, background: 'var(--bg)', borderRadius: 6, display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {m.type === 'text' && !m.deleted && (
                    <button type="button" onClick={() => { const txt = m.encrypted ? (decryptedMap[m.id] || '') : (m.content || ''); if (txt) navigator.clipboard?.writeText(txt); setMsgMenuId(null); }} style={{ padding: '6px 10px', border: 'none', background: 'none', color: 'var(--text)', cursor: 'pointer', fontSize: 12, textAlign: 'right' }}>📋 نسخ النص</button>
                  )}
                  {!m.deleted && !m.encrypted && (
                    <button type="button" onClick={() => { setShowForward(m); setMsgMenuId(null); }} style={{ padding: '6px 10px', border: 'none', background: 'none', color: 'var(--text)', cursor: 'pointer', fontSize: 12, textAlign: 'right' }}>↪ إعادة توجيه</button>
                  )}
                  {['❤️', '👍', '😂', '😮', '👎'].map((emo) => {
                    const myReaction = (reactions[m.id] || []).find((r) => Number(r.user_id) === Number(currentUserId) && r.emoji === emo);
                    return (
                      <button key={emo} type="button" onClick={() => {
                        if (myReaction) socket?.emit('remove_reaction', { conversationId: conversation.id, messageId: m.id });
                        else socket?.emit('add_reaction', { conversationId: conversation.id, messageId: m.id, emoji: emo });
                        setMsgMenuId(null);
                      }} style={{ padding: '6px 10px', border: 'none', background: myReaction ? 'rgba(var(--primary-rgb, 0,123,255),0.2)' : 'none', color: 'var(--text)', cursor: 'pointer', fontSize: 14, borderRadius: 6 }}>{emo}</button>
                    );
                  })}
                  <button type="button" onClick={() => handleDeleteMsg(m, false)} style={{ padding: '6px 10px', border: 'none', background: 'none', color: 'var(--text)', cursor: 'pointer', fontSize: 12, textAlign: 'right' }}>حذف عندي</button>
                  {Number(m.sender_id) === Number(currentUserId) && (
                    <button type="button" onClick={() => handleDeleteMsg(m, true)} style={{ padding: '6px 10px', border: 'none', background: 'none', color: '#f85149', cursor: 'pointer', fontSize: 12, textAlign: 'right' }}>حذف للجميع</button>
                  )}
                </div>
              )}
            </div>
          );
        })}
        {typingUser && <div style={{ fontSize: 12, color: 'var(--text-muted)', alignSelf: 'flex-start', marginTop: 4 }}>…{typingUser.name} يكتب</div>}
        {groupCallParticipants && groupCallParticipants.length > 0 && (
          <div style={{ padding: 10, background: 'var(--surface)', borderRadius: 8, marginTop: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
            <span style={{ fontSize: 13 }}>📞 مكالمة جماعية ({groupCallParticipants.length} مشارك)</span>
            <div style={{ display: 'flex', gap: 6 }}>
              {!groupCallParticipants.some((id) => Number(id) === Number(currentUserId)) && (
                <button type="button" onClick={() => socket?.emit('join_group_call', { conversationId: conversation.id })} style={{ padding: '6px 12px', background: 'var(--primary)', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer', fontSize: 12 }}>انضم</button>
              )}
              {groupCallParticipants.some((id) => Number(id) === Number(currentUserId)) && (
                <button type="button" onClick={() => { socket?.emit('leave_group_call', { conversationId: conversation.id }); setGroupCallParticipants(null); }} style={{ padding: '6px 12px', background: '#f85149', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer', fontSize: 12 }}>غادر</button>
              )}
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      {fileError && <p style={{ padding: 8, margin: 0, fontSize: 13, color: '#f85149', background: 'rgba(248,81,73,0.1)' }}>{fileError}</p>}
      {replyTo && (
        <div style={{ padding: 8, background: 'var(--bg)', borderRight: '3px solid var(--primary)', margin: '0 12px 8px', borderRadius: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>↩ {getMsgSnippet(replyTo)}</span>
          <button type="button" onClick={() => setReplyTo(null)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: 18 }}>×</button>
        </div>
      )}
      <form
        className="chat-form-row"
        style={styles.form}
        onSubmit={(e) => { e.preventDefault(); sendMessage('text', text.trim(), null, replyTo); }}
      >
        <input type="file" ref={fileInputRef} onChange={(e) => handleFile(e, false)} accept="*" style={{ display: 'none' }} />
        <input type="file" ref={imageInputRef} onChange={(e) => handleFile(e, false)} accept="image/*" style={{ display: 'none' }} />
        <input type="file" ref={videoInputRef} onChange={(e) => handleFile(e, false)} accept="video/*" style={{ display: 'none' }} />
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', alignItems: 'center' }}>
          <button type="button" style={styles.fileBtn} onClick={() => fileInputRef.current?.click()} title="ملف">📎</button>
          <button type="button" style={styles.fileBtn} onClick={() => imageInputRef.current?.click()} title="صورة">📷</button>
          <button type="button" style={styles.fileBtn} onClick={() => videoInputRef.current?.click()} title="فيديو">🎬</button>
          <button type="button" style={styles.fileBtn} onClick={() => setShowGifPicker(true)} title="GIF">🎞️</button>
          {isGroup && <button type="button" style={styles.fileBtn} onClick={() => setShowPollCreate(true)} title="استطلاع">📊</button>}
          <button type="button" style={styles.fileBtn} onClick={handleLocation} title="الموقع">📍</button>
          {!isRecording ? (
            <button type="button" style={styles.fileBtn} onMouseDown={startRecording} onMouseUp={stopRecording} onMouseLeave={stopRecording} onTouchStart={(e) => { e.preventDefault(); startRecording(); }} onTouchEnd={(e) => { e.preventDefault(); stopRecording(); }} title="رسالة صوتية (اضغط مع الاستمرار)">🎤</button>
          ) : (
            <button type="button" style={{ ...styles.fileBtn, background: 'var(--primary)', color: '#fff' }} onMouseUp={stopRecording} onMouseLeave={stopRecording} onTouchEnd={(e) => { e.preventDefault(); stopRecording(); }}>⏹ التوقف</button>
          )}
          <div ref={emojiWrapRef} style={{ position: 'relative' }}>
            <button type="button" style={styles.fileBtn} onClick={() => setShowEmoji((v) => !v)} title="إيموجي">😊</button>
            {showEmoji && (
              <div style={{ position: 'absolute', bottom: '100%', right: 0, marginBottom: 4, zIndex: 20 }}>
                <EmojiPicker theme={theme} onEmojiClick={(e) => { setText((t) => t + (e.emoji || '')); }} width={320} height={360} />
              </div>
            )}
          </div>
        </div>
        <input type="text" placeholder="اكتب رسالة..." value={text} onChange={(e) => { setText(e.target.value); emitTyping(); }} onBlur={() => { if (typingTimeoutRef.current) { clearTimeout(typingTimeoutRef.current); socket?.emit('stop_typing', { conversationId: conversation.id }); } }} style={styles.input} />
        <button type="submit" style={styles.sendBtn}>إرسال</button>
      </form>
      {showGifPicker && <GifPicker onSelect={(url) => sendMessage('image', url, 'GIF')} onClose={() => setShowGifPicker(false)} />}
      {showForward && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 150 }} onClick={() => setShowForward(null)}>
          <div style={{ background: 'var(--surface)', borderRadius: 12, padding: 20, maxWidth: 360, width: '100%', maxHeight: '80vh', overflow: 'auto', border: '1px solid var(--border)' }} onClick={(e) => e.stopPropagation()}>
            <h3 style={{ margin: '0 0 12px' }}>إعادة التوجيه إلى</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {(conversations || []).filter((c) => c.id !== conversation?.id).length === 0 ? (
                <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: 13 }}>لا توجد محادثات أخرى للإعادة التوجيه إليها</p>
              ) : (
                (conversations || []).filter((c) => c.id !== conversation?.id).map((c) => (
                  <button key={c.id} type="button" onClick={async () => { try { await api.forwardMessage(c.id, conversation.id, showForward.id); setShowForward(null); } catch (err) { setFileError(err.message || 'فشل'); } }} style={{ padding: '12px 16px', border: '1px solid var(--border)', borderRadius: 8, background: 'var(--bg)', color: 'var(--text)', cursor: 'pointer', fontSize: 14, textAlign: 'right' }}>{c.label || 'محادثة'}</button>
                ))
              )}
            </div>
            <button type="button" onClick={() => setShowForward(null)} style={{ marginTop: 12, padding: '8px 16px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', cursor: 'pointer' }}>إلغاء</button>
          </div>
        </div>
      )}
      {showPollCreate && isGroup && (
        <PollCreateModal onClose={() => setShowPollCreate(false)} onSent={(content) => { sendMessage('poll', content); setShowPollCreate(false); }} />
      )}
      {showGroupInfo && isGroup && (
        <GroupInfo conversation={convDetails} currentUserId={currentUserId} onClose={() => setShowGroupInfo(false)} onMembersUpdated={async () => { const updated = await api.getConversation(conversation.id); setConvDetails(updated); onMembersUpdated?.(); }} onRemoveMember={handleRemoveMember} disappearingAfter={convDetails?.disappearing_after} onDisappearingChange={async (sec) => { await api.setDisappearing(conversation.id, sec); const updated = await api.getConversation(conversation.id); setConvDetails(updated); onMembersUpdated?.(); }} />
      )}
      {callState && !webrtcCall && <CallModal isVoice={callState.isVoice} callerName="جاري الاتصال..." isOutgoing onHangup={() => { stopCallRing(); socket?.emit('hangup_call', { conversationId: conversation.id }); setCallState(null); }} />}
      {webrtcCall && (
        <WebRTCCall
          socket={socket}
          conversationId={conversation.id}
          remoteUserId={webrtcCall.remoteUserId}
          isInitiator
          isVideo={webrtcCall.isVideo}
          onEnd={() => { socket?.emit('hangup_call', { conversationId: conversation.id }); setWebrtcCall(null); setCallState(null); }}
        />
      )}
    </div>
  );
}
