import { useState, useEffect, useRef } from 'react';
import * as api from './api';

const s = {
  room: { flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', background: '#0d1117' },
  header: { padding: 12, borderBottom: '1px solid #30363d', display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#fff' },
  messages: { flex: 1, overflow: 'auto', padding: 16 },
  msg: { marginBottom: 12, padding: 10, borderRadius: 8, maxWidth: '80%', background: '#21262d', color: '#fff' },
  msgMe: { marginRight: 0, marginLeft: 'auto', background: '#238636' },
  inputRow: { padding: 12, borderTop: '1px solid #30363d', display: 'flex', gap: 8, alignItems: 'center' },
  input: { flex: 1, padding: 12, border: '1px solid #30363d', borderRadius: 8, background: '#161b22', color: '#fff' },
  btn: { padding: '10px 20px', background: '#238636', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer' }
};

export default function ChatRoom({ conversationId, convDetails, socket, currentUserId, onBack, incomingCall, onEndCall }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [callState, setCallState] = useState(null);
  const msgEndRef = useRef(null);

  useEffect(() => {
    if (!conversationId) return;
    api.getMessages(conversationId).then(setMessages).catch(() => setMessages([]));
  }, [conversationId]);

  useEffect(() => {
    if (!socket || !conversationId) return;
    socket.emit('join_conversation', conversationId);
    const onMsg = (msg) => {
      if (Number(msg.conversation_id) === Number(conversationId)) setMessages((p) => [...p, msg]);
    };
    socket.on('new_message', onMsg);
    return () => socket.off('new_message', onMsg);
  }, [socket, conversationId]);

  useEffect(() => {
    msgEndRef.current?.scrollIntoView();
  }, [messages]);

  const send = () => {
    const txt = input.trim();
    if (!txt) return;
    socket?.emit('send_message', { conversationId, type: 'text', content: txt });
    setInput('');
  };

  const startCall = (isVideo) => {
    const targetId = convDetails?.type === 'direct' ? (convDetails?.members || []).find((m) => Number(m) !== Number(currentUserId)) : null;
    if (!targetId) return;
    setCallState({ isVideo, targetId });
    socket?.emit('start_call', { conversationId, toUserId: targetId, isVideo });
  };

  const targetId = convDetails?.type === 'direct' ? (convDetails?.members || []).find((m) => Number(m) !== Number(currentUserId)) : null;

  return (
    <div style={s.room}>
      <div style={s.header}>
        <button type="button" onClick={onBack} style={{ background: 'none', border: 'none', color: '#58a6ff', cursor: 'pointer', fontSize: 14 }}>← رجوع</button>
        <span style={{ fontWeight: 500 }}>{convDetails?.label || 'محادثة'}</span>
        <div style={{ display: 'flex', gap: 8 }}>
          <button type="button" onClick={() => startCall(false)} style={{ ...s.btn, padding: '6px 12px', fontSize: 12 }} title="مكالمة صوتية">📞</button>
          <button type="button" onClick={() => startCall(true)} style={{ ...s.btn, padding: '6px 12px', fontSize: 12 }} title="مكالمة فيديو">📹</button>
        </div>
      </div>

      <div style={s.messages}>
        {messages.map((m) => (
          <div key={m.id} style={{ ...s.msg, ...(Number(m.sender_id) === Number(currentUserId) ? s.msgMe : {}) }}>
            <div style={{ fontSize: 11, color: '#8b949e', marginBottom: 4 }}>{m.sender?.name || m.sender?.phone || '—'}</div>
            <div>{m.content || 'وسائط'}</div>
          </div>
        ))}
        <div ref={msgEndRef} />
      </div>

      <div style={s.inputRow}>
        <input type="text" placeholder="اكتب رسالة..." value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && send()} style={s.input} />
        <button type="button" style={s.btn} onClick={send}>إرسال</button>
      </div>

      {(callState || (incomingCall?.accepted && Number(incomingCall.conversationId) === Number(conversationId))) && (
        <CallOverlay
          socket={socket}
          conversationId={conversationId}
          remoteUserId={callState?.targetId || incomingCall?.fromUserId}
          isVideo={callState?.isVideo ?? incomingCall?.isVideo}
          isInitiator={!!callState}
          onEnd={() => { setCallState(null); onEndCall?.(); }}
        />
      )}
    </div>
  );
}

function CallOverlay({ socket, conversationId, remoteUserId, isVideo, isInitiator, onEnd }) {
  const [status, setStatus] = useState(isInitiator ? 'connecting' : 'incoming');
  const [error, setError] = useState('');
  const [remoteStream, setRemoteStream] = useState(null);
  const localVideoRef = useRef(null);
  const remoteMediaRef = useRef(null);
  const pcRef = useRef(null);
  const localStreamRef = useRef(null);
  const remoteStreamRef = useRef(null);
  const pendingCandidatesRef = useRef([]);
  const pendingSignalsRef = useRef([]);
  const pcReadyRef = useRef(false);

  useEffect(() => {
    if (!socket || !remoteUserId) return;

    const emitSignal = (signal) => {
      socket.emit('webrtc_signal', { conversationId, toUserId: remoteUserId, signal });
    };

    const processSignal = async (pc, signal) => {
      try {
        if (signal.sdp) {
          await pc.setRemoteDescription(new RTCSessionDescription(signal.sdp));
          for (const c of pendingCandidatesRef.current) {
            try { await pc.addIceCandidate(new RTCIceCandidate(c)); } catch (_) {}
          }
          pendingCandidatesRef.current = [];
          if (signal.sdp.type === 'offer') {
            setStatus('connecting');
            const answer = await pc.createAnswer();
            await pc.setLocalDescription(answer);
            emitSignal({ sdp: pc.localDescription });
          } else {
            setStatus('connected');
          }
        } else if (signal.candidate) {
          if (pc.remoteDescription) {
            await pc.addIceCandidate(new RTCIceCandidate(signal.candidate));
          } else {
            pendingCandidatesRef.current.push(signal.candidate);
          }
        }
      } catch (err) {
        setError(err?.message || 'خطأ في الاتصال');
      }
    };

    const onSignal = async (data) => {
      if (Number(data.fromUserId) !== Number(remoteUserId)) return;
      const { signal } = data;
      const pc = pcRef.current;
      if (!pc || !pcReadyRef.current) {
        pendingSignalsRef.current.push(signal);
        return;
      }
      await processSignal(pc, signal);
    };

    socket.on('webrtc_signal', onSignal);
    socket.on('call_answered', ({ calleeUserId }) => {
      if (Number(calleeUserId) === Number(remoteUserId)) setStatus('connected');
    });
    socket.on('call_rejected', () => setError('تم رفض المكالمة'));
    socket.on('call_ended', () => onEnd());

    const setup = async () => {
      if (!navigator.mediaDevices?.getUserMedia) {
        setError(window.isSecureContext ? 'المتصفح لا يدعم الكاميرا/الميكروفون' : 'المكالمات تتطلب HTTPS');
        return;
      }
      try {
        pcReadyRef.current = false;
        pendingCandidatesRef.current = [];
        pendingSignalsRef.current = [];
        remoteStreamRef.current = null;

        const stream = await navigator.mediaDevices.getUserMedia({
          audio: true,
          video: isVideo ? { width: 640, height: 480 } : false
        });
        localStreamRef.current = stream;
        if (localVideoRef.current && isVideo) localVideoRef.current.srcObject = stream;

        const pc = new RTCPeerConnection({
          iceServers: [
            { urls: 'stun:stun.l.google.com:19302' },
            { urls: 'stun:stun1.l.google.com:19302' }
          ]
        });
        pcRef.current = pc;

        stream.getTracks().forEach((t) => pc.addTrack(t, stream));

        pc.ontrack = (e) => {
          let rs = remoteStreamRef.current;
          if (!rs) { rs = new MediaStream(); remoteStreamRef.current = rs; }
          if (!rs.getTracks().includes(e.track)) {
            rs.addTrack(e.track);
            e.track.onunmute = () => {
              const el = remoteMediaRef.current;
              if (el?.srcObject === rs) el.play?.().catch(() => {});
            };
          }
          setRemoteStream(new MediaStream(rs.getTracks()));
          const el = remoteMediaRef.current;
          if (el) { el.srcObject = rs; el.play?.().catch(() => {}); }
        };

        pc.onicecandidate = (e) => { if (e.candidate) emitSignal({ candidate: e.candidate }); };

        pc.onconnectionstatechange = () => {
          if (pc.connectionState === 'connected') setStatus('connected');
          else if (pc.connectionState === 'failed') setError('فشل الاتصال');
        };

        pcReadyRef.current = true;

        if (isInitiator) {
          const offer = await pc.createOffer();
          await pc.setLocalDescription(offer);
          emitSignal({ sdp: pc.localDescription });
        } else {
          for (const sig of pendingSignalsRef.current.splice(0)) {
            await processSignal(pc, sig);
          }
        }
      } catch (err) {
        setError(err?.message || 'فشل بدء المكالمة');
      }
    };

    setup();

    return () => {
      pcReadyRef.current = false;
      localStreamRef.current?.getTracks().forEach((t) => t.stop());
      pcRef.current?.close();
      socket.off('webrtc_signal', onSignal);
      socket.off('call_answered');
      socket.off('call_rejected');
      socket.off('call_ended');
    };
  }, [socket, remoteUserId, conversationId, isVideo, isInitiator]);

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.9)', zIndex: 20, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
      <p style={{ marginBottom: 12 }}>{status === 'connecting' ? 'جاري الاتصال...' : status === 'connected' ? 'متصل' : status === 'incoming' ? 'جاري التحضير...' : status}</p>
      {error && <p style={{ color: '#f85149', marginBottom: 12 }}>{error}</p>}
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', justifyContent: 'center' }}>
        {isVideo && (
          <div style={{ width: 160, background: '#222', borderRadius: 8, overflow: 'hidden' }}>
            <video ref={localVideoRef} autoPlay muted playsInline style={{ width: '100%', transform: 'scaleX(-1)' }} />
            <p style={{ fontSize: 11, color: '#888', margin: 0, padding: 4 }}>أنت</p>
          </div>
        )}
        <div style={{ width: isVideo ? 240 : 120, background: '#222', borderRadius: 8, overflow: 'hidden', minHeight: isVideo ? 180 : 60 }}>
          {isVideo && <p style={{ fontSize: 11, color: '#888', margin: '0 0 4px', padding: 4 }}>الطرف الآخر</p>}
          {isVideo ? (
            <video ref={remoteMediaRef} srcObject={remoteStream || undefined} autoPlay playsInline style={{ width: '100%', minHeight: 160 }} />
          ) : (
            <audio ref={remoteMediaRef} srcObject={remoteStream || undefined} autoPlay style={{ width: '100%' }} />
          )}
        </div>
      </div>
      <button type="button" onClick={() => { socket?.emit('hangup_call', { conversationId }); onEnd(); }} style={{ marginTop: 24, ...s.btn, background: '#da3633' }}>إنهاء المكالمة</button>
    </div>
  );
}
