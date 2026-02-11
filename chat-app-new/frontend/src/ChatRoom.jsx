import { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import EmojiPicker from 'emoji-picker-react';
import * as api from './api';

const s = {
  room: { flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', borderRight: '1px solid var(--border)' },
  header: { padding: 12, borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 12 },
  backBtn: { padding: '6px 12px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', cursor: 'pointer' },
  messages: { flex: 1, overflow: 'auto', padding: 16, display: 'flex', flexDirection: 'column', gap: 8 },
  msg: { maxWidth: '80%', padding: '10px 14px', borderRadius: 12, alignSelf: 'flex-start', wordBreak: 'break-word' },
  msgOwn: { alignSelf: 'flex-end', background: 'var(--primary)', color: '#fff' },
  msgOther: { background: 'var(--surface)', border: '1px solid var(--border)' },
  msgMeta: { fontSize: 11, opacity: 0.8, marginTop: 4 },
  replyBar: { fontSize: 12, opacity: 0.9, padding: '6px 10px', borderRight: '3px solid var(--primary)', marginBottom: 6, background: 'rgba(0,0,0,0.15)', borderRadius: 4 },
  form: { padding: 12, borderTop: '1px solid var(--border)', display: 'flex', gap: 8, alignItems: 'flex-end', flexWrap: 'wrap' },
  input: { flex: 1, minWidth: 120, padding: '10px 14px', border: '1px solid var(--border)', borderRadius: 8, background: 'var(--bg)', color: 'var(--text)', fontSize: 15, minHeight: 44, textAlign: 'right' },
  sendBtn: { padding: '10px 20px', border: 'none', borderRadius: 8, background: 'var(--primary)', color: '#fff', cursor: 'pointer', fontSize: 15 },
  fileBtn: { padding: '10px 14px', border: '1px solid var(--border)', borderRadius: 8, background: 'var(--surface)', color: 'var(--text)', cursor: 'pointer' },
  emojiBtn: { padding: '10px 14px', border: '1px solid var(--border)', borderRadius: 8, background: 'var(--surface)', color: 'var(--text)', cursor: 'pointer', fontSize: 18 },
  img: { maxWidth: '100%', maxHeight: 200, borderRadius: 8, marginTop: 4 },
  link: { color: 'var(--primary)', wordBreak: 'break-all' },
  typingBar: { padding: '4px 12px', fontSize: 12, color: 'var(--text-muted)', fontStyle: 'italic' },
  replyPreview: { padding: '6px 10px', background: 'rgba(0,0,0,0.2)', borderRadius: 6, marginBottom: 6, fontSize: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 },
  replyBtn: { background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: 12, padding: '2px 6px' },
  deleteBtn: { background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: 11, padding: '2px 6px' },
  voiceBtn: { padding: '10px 14px', border: '1px solid var(--border)', borderRadius: 8, background: 'var(--surface)', color: 'var(--text)', cursor: 'pointer', fontSize: 16 },
  audio: { maxWidth: '100%', minWidth: 200, marginTop: 4 },
  callModal: { position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50, padding: 16 },
  callModalBox: { background: 'var(--surface)', borderRadius: 12, padding: 24, textAlign: 'center', minWidth: 260 },
  callBar: { padding: 10, background: 'var(--surface)', borderTop: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12 },
  callVideoWrap: { position: 'fixed', inset: 0, background: '#000', zIndex: 40, display: 'flex', flexDirection: 'column' },
  remoteVideo: { flex: 1, width: '100%', objectFit: 'contain' },
  localVideo: { position: 'absolute', bottom: 80, right: 16, width: 120, height: 90, objectFit: 'cover', borderRadius: 8, border: '2px solid var(--border)' },
  hangupBtn: { position: 'absolute', bottom: 16, left: '50%', transform: 'translateX(-50%)', padding: '12px 24px', background: '#f85149', color: '#fff', border: 'none', borderRadius: 8, cursor: 'pointer', fontSize: 16 },
  locationBtn: { padding: '10px 14px', border: '1px solid var(--border)', borderRadius: 8, background: 'var(--surface)', color: 'var(--text)', cursor: 'pointer', fontSize: 16 },
  searchRow: { padding: '8px 12px', borderBottom: '1px solid var(--border)', display: 'flex', gap: 8, alignItems: 'center' },
  searchInput: { flex: 1, padding: '8px 12px', border: '1px solid var(--border)', borderRadius: 8, background: 'var(--bg)', color: 'var(--text)', fontSize: 14 },
  loadMoreBtn: { padding: '8px 16px', margin: '8px auto', display: 'block', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', cursor: 'pointer', fontSize: 13 },
  copyBtn: { background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: 12, padding: '2px 6px' }
};

export default function ChatRoom({ conversation, socket, currentUserId, onBack, isAdmin, onBlockUser }) {
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(true);
  const [fileError, setFileError] = useState('');
  const [optimisticVersion, setOptimisticVersion] = useState(0);
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [typingUser, setTypingUser] = useState(null);
  const [replyTo, setReplyTo] = useState(null);
  const [readReceipts, setReadReceipts] = useState({});
  const [isRecording, setIsRecording] = useState(false);
  const [voiceError, setVoiceError] = useState('');
  const [locationError, setLocationError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [loadingMore, setLoadingMore] = useState(false);
  const [copyDoneId, setCopyDoneId] = useState(null);
  const [callState, setCallState] = useState('idle');
  const [incomingCallFrom, setIncomingCallFrom] = useState(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const optimisticRef = useRef([]);
  const typingTimeoutRef = useRef(null);
  const emojiPickerRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const peerConnectionRef = useRef(null);
  const localStreamRef = useRef(null);
  const remoteAudioRef = useRef(null);
  const remoteVideoRef = useRef(null);
  const localVideoRef = useRef(null);
  const pendingOfferRef = useRef(null);
  const [callWithVideo, setCallWithVideo] = useState(true);
  const [hasLocalStream, setHasLocalStream] = useState(false);

  useEffect(() => {
    if (!conversation?.id) return;
    optimisticRef.current = [];
    setLoading(true);
    setReplyTo(null);
    api.getMessages(conversation.id).then((data) => {
      const list = data.messages || [];
      const receipts = (data.readReceipts || []).reduce((acc, r) => ({ ...acc, [r.user_id]: r.last_message_id }), {});
      setMessages(Array.isArray(list) ? list : []);
      setReadReceipts(receipts);
      setLoading(false);
      const maxId = list.length ? Math.max(...list.map((m) => m.id)) : null;
      if (socket && maxId != null) socket.emit('mark_read', { conversationId: conversation.id, lastMessageId: maxId });
    }).catch(() => setLoading(false));
    if (socket) {
      socket.emit('join_conversation', conversation.id);
      const onNew = (msg) => {
        if (msg.conversation_id !== conversation.id) return;
        optimisticRef.current = optimisticRef.current.filter((o) => !(o.content === msg.content && o.sender_id === msg.sender_id && o.type === msg.type));
        setOptimisticVersion((v) => v + 1);
        setMessages((prev) => [...prev, msg]);
        if (Number(msg.sender_id) !== Number(currentUserId)) {
          if (msg.id != null) socket.emit('mark_read', { conversationId: conversation.id, lastMessageId: msg.id });
          if (document.hidden) playNotificationSound();
        }
      };
      const onTyping = (data) => {
        if (data.userId === currentUserId) return;
        setTypingUser(data.userName || 'شخص');
      };
      const onStopTyping = (data) => {
        if (data.userId === currentUserId) return;
        setTypingUser(null);
      };
      const onMessageDeleted = (data) => {
        if (data.conversationId !== conversation.id) return;
        setMessages((prev) => prev.map((m) => (m.id === data.messageId ? { ...m, deleted: true, content: '', file_name: null, type: 'text' } : m)));
        optimisticRef.current = optimisticRef.current.map((m) => (m.id === data.messageId ? { ...m, deleted: true, content: '', file_name: null, type: 'text' } : m));
        setOptimisticVersion((v) => v + 1);
      };
      const onReadReceipt = (data) => {
        if (data.conversationId !== conversation.id) return;
        setReadReceipts((prev) => ({ ...prev, [data.userId]: data.lastMessageId }));
      };
      const onIncomingCall = (data) => {
        if (data.conversationId !== conversation.id) return;
        setIncomingCallFrom({ userId: data.fromUserId, userName: data.fromUserName || 'شخص' });
        setCallState('incoming');
      };
      const onWebRTCSignal = (data) => {
        if (data.conversationId !== conversation.id) return;
        const { signal } = data;
        if (signal.type === 'offer') pendingOfferRef.current = { type: 'offer', sdp: signal.sdp };
        if (signal.type === 'answer' && peerConnectionRef.current) {
          peerConnectionRef.current.setRemoteDescription(new RTCSessionDescription({ type: 'answer', sdp: signal.sdp })).then(() => setCallState('connected')).catch(() => {});
        }
        if (signal.type === 'ice' && signal.candidate && peerConnectionRef.current) {
          peerConnectionRef.current.addIceCandidate(new RTCIceCandidate(signal.candidate)).catch(() => {});
        }
      };
      const onCallRejected = (data) => {
        if (data.conversationId !== conversation.id) return;
        setCallState('idle');
        setHasLocalStream(false);
        if (peerConnectionRef.current) {
          peerConnectionRef.current.close();
          peerConnectionRef.current = null;
        }
        if (localStreamRef.current) {
          localStreamRef.current.getTracks().forEach((t) => t.stop());
          localStreamRef.current = null;
        }
      };
      const onCallEnded = (data) => {
        if (data.conversationId !== conversation.id) return;
        setCallState('idle');
        setIncomingCallFrom(null);
        if (peerConnectionRef.current) {
          peerConnectionRef.current.close();
          peerConnectionRef.current = null;
        }
        if (localStreamRef.current) {
          localStreamRef.current.getTracks().forEach((t) => t.stop());
          localStreamRef.current = null;
        }
        if (remoteVideoRef.current) remoteVideoRef.current.srcObject = null;
        if (localVideoRef.current) localVideoRef.current.srcObject = null;
        setHasLocalStream(false);
      };
      socket.on('new_message', onNew);
      socket.on('user_typing', onTyping);
      socket.on('user_stop_typing', onStopTyping);
      socket.on('message_deleted', onMessageDeleted);
      socket.on('read_receipt', onReadReceipt);
      socket.on('incoming_call', onIncomingCall);
      socket.on('webrtc_signal', onWebRTCSignal);
      socket.on('call_rejected', onCallRejected);
      socket.on('call_ended', onCallEnded);
      return () => {
        socket.off('new_message', onNew);
        socket.off('user_typing', onTyping);
        socket.off('user_stop_typing', onStopTyping);
        socket.off('message_deleted', onMessageDeleted);
        socket.off('read_receipt', onReadReceipt);
        socket.off('incoming_call', onIncomingCall);
        socket.off('webrtc_signal', onWebRTCSignal);
        socket.off('call_rejected', onCallRejected);
        socket.off('call_ended', onCallEnded);
        socket.emit('leave_conversation', conversation.id);
      };
    }
  }, [conversation?.id, socket, currentUserId]);

  const displayMessages = useMemo(() => {
    const fromServer = messages || [];
    const pending = optimisticRef.current || [];
    const serverIds = new Set(fromServer.map((m) => m.id));
    const extra = pending.filter((p) => !serverIds.has(p.id));
    return [...fromServer, ...extra].sort((a, b) => new Date(a.created_at || 0) - new Date(b.created_at || 0));
  }, [messages, optimisticVersion]);

  const filteredMessages = useMemo(() => {
    if (!searchQuery.trim()) return displayMessages;
    const q = searchQuery.trim().toLowerCase();
    return displayMessages.filter((m) => {
      if (m.deleted) return false;
      if (m.type === 'text') return (m.content || '').toLowerCase().includes(q);
      if (m.type === 'file' && m.file_name) return String(m.file_name).toLowerCase().includes(q);
      if (m.type === 'location') return (m.content || '').toLowerCase().includes(q) || 'موقع'.includes(q);
      return false;
    });
  }, [displayMessages, searchQuery]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [displayMessages]);

  const loadMoreMessages = async () => {
    if (!conversation?.id || loadingMore) return;
    const numericIds = messages.filter((m) => typeof m.id === 'number').map((m) => m.id);
    if (!numericIds.length) return;
    const oldestId = Math.min(...numericIds);
    setLoadingMore(true);
    try {
      const data = await api.getMessages(conversation.id, 50, oldestId);
      const newList = data.messages || [];
      const existingIds = new Set(messages.map((m) => m.id));
      const toAdd = newList.filter((m) => !existingIds.has(m.id));
      if (toAdd.length) setMessages((prev) => [...toAdd, ...prev]);
      if (data.readReceipts?.length) setReadReceipts((prev) => ({ ...prev, ...(data.readReceipts || []).reduce((acc, r) => ({ ...acc, [r.user_id]: r.last_message_id }), {}) }));
    } finally {
      setLoadingMore(false);
    }
  };

  const copyMessageText = (m) => {
    const text = m.type === 'text' ? m.content : m.type === 'location' ? m.content : '';
    if (!text) return;
    navigator.clipboard.writeText(text).then(() => {
      setCopyDoneId(m.id);
      setTimeout(() => setCopyDoneId(null), 1500);
    });
  };

  useEffect(() => {
    if ((callState === 'calling' || callState === 'connected') && hasLocalStream && localStreamRef.current && localVideoRef.current) {
      localVideoRef.current.srcObject = localStreamRef.current;
    }
  }, [callState, hasLocalStream]);

  const emitTyping = useCallback(() => {
    if (!socket || !conversation?.id) return;
    socket.emit('typing', { conversationId: conversation.id });
    if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
    typingTimeoutRef.current = setTimeout(() => {
      socket.emit('stop_typing', { conversationId: conversation.id });
      typingTimeoutRef.current = null;
    }, 2000);
  }, [socket, conversation?.id]);

  const sendMessage = (type, content, file_name = null, reply_to_id = null, reply_to_snippet = null) => {
    if (!content && type === 'text') return;
    if (socket) socket.emit('stop_typing', { conversationId: conversation.id });
    const tempId = 'temp-' + Date.now();
    optimisticRef.current = [...optimisticRef.current, {
      id: tempId,
      content,
      sender_id: currentUserId,
      type: type === 'text' ? 'text' : type,
      file_name: file_name || null,
      reply_to_id: reply_to_id || null,
      reply_to_snippet: reply_to_snippet || null,
      created_at: new Date().toISOString(),
      sender: null
    }];
    setOptimisticVersion((v) => v + 1);
    if (type === 'text') setText('');
    setReplyTo(null);
    if (socket) socket.emit('send_message', {
      conversationId: conversation.id,
      type,
      content,
      file_name,
      reply_to_id: reply_to_id || undefined,
      reply_to_snippet: reply_to_snippet || undefined
    });
  };

  const handleFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileError('');
    try {
      const { url, filename } = await api.uploadFile(file);
      const fullUrl = api.uploadsUrl(url);
      sendMessage((file.type || '').startsWith('image/') ? 'image' : 'file', fullUrl, filename);
    } catch (err) {
      setFileError(err.message || 'فشل رفع الملف');
    }
    e.target.value = '';
  };

  const getReplySnippet = (m) => {
    if (!m) return '';
    if (m.type === 'text') return (m.content || '').slice(0, 50);
    if (m.type === 'image') return '🖼 صورة';
    if (m.type === 'file') return '📎 ' + (m.file_name || 'ملف');
    if (m.type === 'voice') return '🎤 رسالة صوتية';
    if (m.type === 'location') return '📍 موقع';
    return '';
  };

  const playNotificationSound = () => {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.frequency.value = 800;
      gain.gain.setValueAtTime(0.15, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.15);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.15);
    } catch (_) {}
  };

  const startVoiceRecording = () => {
    setVoiceError('');
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setVoiceError('المتصفح لا يدعم التسجيل الصوتي');
      return;
    }
    navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
      audioChunksRef.current = [];
      const mime = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/ogg';
      const recorder = new MediaRecorder(stream);
      recorder.ondataavailable = (e) => { if (e.data.size > 0) audioChunksRef.current.push(e.data); };
      recorder.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(audioChunksRef.current, { type: mime });
        const ext = mime.includes('webm') ? 'webm' : 'ogg';
        const file = new File([blob], `voice-${Date.now()}.${ext}`, { type: mime });
        api.uploadFile(file).then(({ url, filename }) => {
          const fullUrl = api.uploadsUrl(url);
          sendMessage('voice', fullUrl, 'رسالة صوتية');
        }).catch((err) => setVoiceError(err.message || 'فشل رفع الرسالة الصوتية'));
      };
      recorder.start();
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
    }).catch(() => setVoiceError('لم يتم السماح بالميكروفون'));
  };

  const shareLocation = () => {
    setLocationError('');
    if (!navigator.geolocation) {
      setLocationError('المتصفح لا يدعم الموقع');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords;
        const url = `https://www.google.com/maps?q=${latitude},${longitude}`;
        sendMessage('location', url, 'موقع');
      },
      () => setLocationError('لم يتم الحصول على الموقع أو تم رفض الإذن'),
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  const stopVoiceRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current = null;
    }
    setIsRecording(false);
  };

  const otherUserId = useMemo(() => {
    const ids = conversation?.memberIds || [];
    if (ids.length !== 2) return null;
    return ids.find((id) => Number(id) !== Number(currentUserId)) ?? null;
  }, [conversation?.memberIds, currentUserId]);

  const isDirectTwo = conversation?.type === 'direct' && otherUserId != null;

  const createPeerConnection = () => {
    const pc = new RTCPeerConnection({ iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] });
    pc.ontrack = (e) => {
      if (!e.streams?.[0]) return;
      const stream = e.streams[0];
      if (remoteAudioRef.current) remoteAudioRef.current.srcObject = stream;
      if (remoteVideoRef.current) remoteVideoRef.current.srcObject = stream;
    };
    pc.onicecandidate = (e) => {
      if (e.candidate && socket && conversation?.id && otherUserId != null) {
        socket.emit('webrtc_signal', { conversationId: conversation.id, toUserId: otherUserId, signal: { type: 'ice', candidate: e.candidate } });
      }
    };
    return pc;
  };

  const startCall = async (withVideo = true) => {
    if (!socket || !conversation?.id || !otherUserId) return;
    setCallWithVideo(withVideo);
    setCallState('calling');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: withVideo ? { facingMode: 'user' } : false });
      localStreamRef.current = stream;
      setHasLocalStream(true);
      const pc = createPeerConnection();
      stream.getTracks().forEach((t) => pc.addTrack(t, stream));
      peerConnectionRef.current = pc;
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);
      socket.emit('start_call', { conversationId: conversation.id });
      socket.emit('webrtc_signal', { conversationId: conversation.id, toUserId: otherUserId, signal: { type: 'offer', sdp: offer.sdp } });
    } catch (err) {
      setCallState('idle');
    }
  };

  const acceptCall = async (withVideo = true) => {
    const offer = pendingOfferRef.current;
    if (!socket || !conversation?.id || !otherUserId || !offer) return;
    setCallWithVideo(withVideo);
    setIncomingCallFrom(null);
    setCallState('connected');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: withVideo ? { facingMode: 'user' } : false });
      localStreamRef.current = stream;
      setHasLocalStream(true);
      const pc = createPeerConnection();
      peerConnectionRef.current = pc;
      stream.getTracks().forEach((t) => pc.addTrack(t, stream));
      await pc.setRemoteDescription(new RTCSessionDescription({ type: 'offer', sdp: offer.sdp }));
      pendingOfferRef.current = null;
      const answer = await pc.createAnswer();
      await pc.setLocalDescription(answer);
      socket.emit('webrtc_signal', { conversationId: conversation.id, toUserId: otherUserId, signal: { type: 'answer', sdp: answer.sdp } });
    } catch (err) {
      setCallState('idle');
    }
  };

  const rejectCall = () => {
    if (socket && conversation?.id && incomingCallFrom?.userId) {
      socket.emit('reject_call', { conversationId: conversation.id, callerUserId: incomingCallFrom.userId });
    }
    setCallState('idle');
    setIncomingCallFrom(null);
  };

  const hangupCall = () => {
    if (socket && conversation?.id) socket.emit('hangup_call', { conversationId: conversation.id });
    if (peerConnectionRef.current) {
      peerConnectionRef.current.close();
      peerConnectionRef.current = null;
    }
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach((t) => t.stop());
      localStreamRef.current = null;
    }
    if (remoteVideoRef.current) remoteVideoRef.current.srcObject = null;
    if (localVideoRef.current) localVideoRef.current.srcObject = null;
    setHasLocalStream(false);
    setCallState('idle');
    setIncomingCallFrom(null);
  };

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (showEmojiPicker && emojiPickerRef.current && !emojiPickerRef.current.contains(e.target)) setShowEmojiPicker(false);
    };
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [showEmojiPicker]);

  if (!conversation) return null;

  return (
    <div className="chat-room-inner" style={s.room}>
      <div style={s.header}>
        <button type="button" style={s.backBtn} onClick={onBack}>← رجوع</button>
        <span style={{ fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1, minWidth: 0 }}>{conversation.label || conversation.name || 'محادثة'}</span>
        {isDirectTwo && callState === 'idle' && (
          <>
            {isAdmin && onBlockUser && otherUserId && (
              <button type="button" style={{ ...s.voiceBtn, background: 'rgba(248,81,73,0.2)', color: '#f85149' }} onClick={() => onBlockUser(otherUserId)} title="إيقاف وصوله">⏹</button>
            )}
            <button type="button" style={s.voiceBtn} onClick={() => startCall(false)} title="مكالمة صوتية">📞</button>
            <button type="button" style={s.voiceBtn} onClick={() => startCall(true)} title="مكالمة فيديو">📹</button>
          </>
        )}
        {callState === 'calling' && <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>جاري الاتصال...</span>}
      </div>
      {callState === 'incoming' && incomingCallFrom && (
        <div style={s.callModal}>
          <div style={s.callModalBox}>
            <p style={{ margin: '0 0 16px' }}>{incomingCallFrom.userName} يتصل بك</p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, justifyContent: 'center' }}>
              <button type="button" style={{ ...s.sendBtn, background: '#238636' }} onClick={() => acceptCall(true)}>قبول (فيديو)</button>
              <button type="button" style={{ ...s.sendBtn, background: '#2ea043' }} onClick={() => acceptCall(false)}>قبول (صوت)</button>
              <button type="button" style={{ ...s.backBtn, padding: '10px 20px' }} onClick={rejectCall}>رفض</button>
            </div>
          </div>
        </div>
      )}
      {(callState === 'calling' || callState === 'connected') && (
        <div style={s.callVideoWrap}>
          <video ref={remoteVideoRef} style={s.remoteVideo} autoPlay playsInline muted={false} />
          <video ref={localVideoRef} style={s.localVideo} autoPlay playsInline muted />
          <span style={{ position: 'absolute', top: 16, left: '50%', transform: 'translateX(-50%)', color: '#fff', fontSize: 14 }}>
            {callState === 'connected' ? (callWithVideo ? 'مكالمة فيديو' : 'مكالمة صوتية') : 'جاري الاتصال...'}
          </span>
          <button type="button" style={s.hangupBtn} onClick={hangupCall}>إنهاء المكالمة</button>
        </div>
      )}
      {(callState === 'calling' || callState === 'connected') && <audio ref={remoteAudioRef} autoPlay playsInline style={{ display: 'none' }} />}
      <div style={s.searchRow}>
        <input type="text" placeholder="بحث في الرسائل..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} style={s.searchInput} />
        {searchQuery.trim() && <button type="button" style={s.copyBtn} onClick={() => setSearchQuery('')}>إلغاء</button>}
      </div>
      <div className="chat-msg-area" style={s.messages}>
        {loading && <p style={{ color: 'var(--text-muted)' }}>جاري التحميل...</p>}
        {!loading && messages.length > 0 && (
          <button type="button" style={s.loadMoreBtn} onClick={loadMoreMessages} disabled={loadingMore}>
            {loadingMore ? 'جاري التحميل...' : 'تحميل رسائل أقدم'}
          </button>
        )}
        {filteredMessages.map((m) => {
          const isOwn = Number(m.sender_id) === Number(currentUserId);
          const isDeleted = !!m.deleted;
          const replySnippet = m.reply_to_snippet || (m.reply_to_id ? getReplySnippet(displayMessages.find((x) => x.id === m.reply_to_id)) : '') || 'رسالة';
          const canCopy = !isDeleted && (m.type === 'text' || m.type === 'location') && (m.content || '').trim();
          const handleDelete = (forEveryone) => {
            if (!socket || !conversation?.id) return;
            socket.emit('delete_message', { conversationId: conversation.id, messageId: m.id, forEveryone });
          };
          const others = (conversation.memberIds || []).filter((id) => Number(id) !== Number(currentUserId));
          const isRead = isOwn && others.length > 0 && typeof m.id === 'number' && others.every((uid) => (readReceipts[uid] || 0) >= m.id);
          return (
            <div key={m.id} style={{ ...s.msg, ...(isOwn ? s.msgOwn : s.msgOther) }}>
              {!isOwn && m.sender && <div style={{ fontSize: 12, opacity: 0.9 }}>{m.sender.name || m.sender.email || m.sender.phone}</div>}
              {(m.reply_to_id || m.reply_to_snippet) && !isDeleted && (
                <div style={s.replyBar}>رد على: {replySnippet}</div>
              )}
              {isDeleted ? (
                <div style={{ fontStyle: 'italic', opacity: 0.8 }}>تم حذف هذه الرسالة</div>
              ) : (
                <>
                  {m.type === 'text' && <div>{m.content}</div>}
                  {m.type === 'image' && <img src={m.content} alt="" style={s.img} />}
                  {m.type === 'file' && <a href={m.content} target="_blank" rel="noopener noreferrer" style={s.link}>{m.file_name || 'ملف'}</a>}
                  {m.type === 'voice' && <audio controls src={m.content} style={s.audio} />}
                  {m.type === 'location' && (
                    <a href={m.content} target="_blank" rel="noopener noreferrer" style={s.link}>📍 عرض الموقع على الخريطة</a>
                  )}
                </>
              )}
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4, flexWrap: 'wrap' }}>
                <div style={s.msgMeta}>{new Date(m.created_at).toLocaleString('ar-EG')}</div>
                {isRead && <span style={{ fontSize: 11, opacity: 0.9 }} title="تمت المشاهدة">✓✓</span>}
                {canCopy && (
                  <button type="button" style={s.copyBtn} onClick={() => copyMessageText(m)} title="نسخ">
                    {copyDoneId === m.id ? 'تم النسخ' : 'نسخ'}
                  </button>
                )}
                {!isDeleted && <button type="button" style={s.replyBtn} onClick={() => setReplyTo({ id: m.id, snippet: getReplySnippet(m) || 'رسالة' })} title="رد">↩ رد</button>}
                {!isDeleted && isOwn && socket && (
                  <>
                    <button type="button" style={s.deleteBtn} onClick={() => handleDelete(false)} title="حذف لي">حذف لي</button>
                    <button type="button" style={s.deleteBtn} onClick={() => handleDelete(true)} title="حذف للجميع">حذف للجميع</button>
                  </>
                )}
              </div>
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>
      {typingUser && <div style={s.typingBar}>{typingUser} يكتب...</div>}
      {(fileError || voiceError || locationError) && <p style={{ padding: 8, margin: 0, fontSize: 13, color: '#f85149', background: 'rgba(248,81,73,0.1)' }}>{fileError || voiceError || locationError}</p>}
      {replyTo && (
        <div style={s.replyPreview}>
          <span>رد على: {replyTo.snippet}</span>
          <button type="button" style={s.replyBtn} onClick={() => setReplyTo(null)}>إلغاء</button>
        </div>
      )}
      <form
        className="chat-form-row"
        style={s.form}
        onSubmit={(e) => {
          e.preventDefault();
          const trimmed = text.trim();
          if (trimmed) sendMessage('text', trimmed, null, replyTo?.id || null, replyTo?.snippet || null);
        }}
      >
        <input type="file" ref={fileInputRef} onChange={handleFile} accept="image/*,*" style={{ display: 'none' }} />
        <button type="button" style={s.locationBtn} onClick={shareLocation} title="مشاركة الموقع">📍</button>
        {!isRecording ? (
          <button type="button" style={s.voiceBtn} onClick={startVoiceRecording} title="رسالة صوتية">🎤</button>
        ) : (
          <button type="button" style={{ ...s.voiceBtn, background: '#f85149', color: '#fff' }} onClick={stopVoiceRecording} title="إيقاف وإرسال">⏹ إيقاف</button>
        )}
        <div ref={emojiPickerRef} style={{ position: 'relative' }}>
          <button type="button" style={s.emojiBtn} onClick={() => setShowEmojiPicker((v) => !v)} title="إيموجي">😀</button>
          {showEmojiPicker && (
            <div style={{ position: 'absolute', bottom: '100%', right: 0, marginBottom: 4, zIndex: 20 }}>
              <EmojiPicker onEmojiClick={(e) => { setText((t) => t + (e.emoji || '')); setShowEmojiPicker(false); }} theme="dark" width={320} height={360} />
            </div>
          )}
        </div>
        <button type="button" style={s.fileBtn} onClick={() => fileInputRef.current?.click()}>📎</button>
        <input
          type="text"
          placeholder="اكتب رسالة..."
          value={text}
          onChange={(e) => { setText(e.target.value); emitTyping(); }}
          style={s.input}
        />
        <button type="submit" style={s.sendBtn}>إرسال</button>
      </form>
    </div>
  );
}
