/** مكوّن WebRTC للمكالمات الفردية - صوت وفيديو */
import { useState, useEffect, useRef } from 'react';

const getIceServers = () => {
  const list = [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' },
    { urls: 'stun:stun2.l.google.com:19302' },
    { urls: 'stun:stun3.l.google.com:19302' }
  ];
  const turn = import.meta.env.VITE_TURN_URL;
  if (turn) list.push({ urls: turn });
  return list;
};

export default function WebRTCCall({ socket, conversationId, remoteUserId, isInitiator, isVideo, onEnd }) {
  const [status, setStatus] = useState(isInitiator ? 'connecting' : 'incoming');
  const [error, setError] = useState('');
  const [remoteStream, setRemoteStream] = useState(null);
  const localVideoRef = useRef(null);
  const remoteVideoRef = useRef(null);
  const peerRef = useRef(null);
  const localStreamRef = useRef(null);
  const remoteStreamRef = useRef(null);
  const pendingCandidatesRef = useRef([]);
  const pendingSignalsRef = useRef([]);
  const pcReadyRef = useRef(false);
  useEffect(() => {
    if (!socket || !conversationId || !remoteUserId) return;

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
          const hasRemote = pc.remoteDescription;
          if (hasRemote) {
            await pc.addIceCandidate(new RTCIceCandidate(signal.candidate));
          } else {
            pendingCandidatesRef.current.push(signal.candidate);
          }
        }
      } catch (err) {
        setError(err?.message || 'خطأ في الإشارة');
      }
    };

    const onSignal = async (data) => {
      if (Number(data.conversationId) !== Number(conversationId)) return;
      if (Number(data.fromUserId) !== Number(remoteUserId)) return;

      const { signal } = data;
      const pc = peerRef.current;
      if (!pc || !pcReadyRef.current) {
        pendingSignalsRef.current.push(signal);
        return;
      }
      await processSignal(pc, signal);
    };

    socket.on('webrtc_signal', onSignal);

    const setupPeer = async () => {
      try {
        if (!navigator.mediaDevices?.getUserMedia) {
          const msg = window.isSecureContext
            ? 'المتصفح لا يدعم الكاميرا/الميكروفون'
            : 'المكالمات تتطلب HTTPS. استخدم الرابط عبر https:// أو افتح من localhost';
          setError(msg);
          setStatus('error');
          return;
        }
        pcReadyRef.current = false;
        pendingCandidatesRef.current = [];
        pendingSignalsRef.current = [];
        remoteStreamRef.current = null;

        const stream = await navigator.mediaDevices.getUserMedia({
          audio: true,
          video: isVideo ? { width: 640, height: 480, frameRate: 24 } : false
        });
        localStreamRef.current = stream;
        if (localVideoRef.current && isVideo) localVideoRef.current.srcObject = stream;

        const pc = new RTCPeerConnection({ iceServers: getIceServers() });
        peerRef.current = pc;

        stream.getTracks().forEach((t) => pc.addTrack(t, stream));

        pc.ontrack = (e) => {
          let stream = remoteStreamRef.current;
          if (!stream) {
            stream = new MediaStream();
            remoteStreamRef.current = stream;
          }
          if (!stream.getTracks().includes(e.track)) {
            stream.addTrack(e.track);
            e.track.onunmute = () => {
              const el = remoteVideoRef.current;
              if (el?.srcObject === stream) el.play().catch(() => {});
            };
          }
          setRemoteStream(new MediaStream(stream.getTracks()));
          const el = remoteVideoRef.current;
          if (el) {
            el.srcObject = stream;
            el.play().catch(() => {});
          }
        };

        pc.onicecandidate = (e) => {
          if (e.candidate) emitSignal({ candidate: e.candidate });
        };

        pc.onconnectionstatechange = () => {
          if (pc.connectionState === 'connected') {
            setStatus('connected');
            const el = remoteVideoRef.current;
            const stream = remoteStreamRef.current;
            if (el && stream) {
              el.srcObject = stream;
              el.play().catch(() => {});
            }
          } else if (pc.connectionState === 'failed') {
            setError('فشل الاتصال');
          }
        };

        pcReadyRef.current = true;

        if (isInitiator) {
          setStatus('connecting');
          const offer = await pc.createOffer();
          await pc.setLocalDescription(offer);
          emitSignal({ sdp: offer });
        } else {
          for (const sig of pendingSignalsRef.current.splice(0)) {
            await processSignal(pc, sig);
          }
        }
      } catch (err) {
        setError(err?.message || 'فشل بدء المكالمة');
        setStatus('error');
      }
    };

    setupPeer();
    return () => {
      socket.off('webrtc_signal');
      pcReadyRef.current = false;
      if (localStreamRef.current) localStreamRef.current.getTracks().forEach((t) => t.stop());
      if (peerRef.current) peerRef.current.close();
    };
  }, [socket, conversationId, remoteUserId, isInitiator, isVideo]);

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.9)', zIndex: 200, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
      <p style={{ color: '#fff', marginBottom: 12 }}>{status === 'connecting' ? 'جاري الاتصال...' : status === 'connected' ? 'متصل' : status}</p>
      {error && <p style={{ color: '#f85149', marginBottom: 12 }}>{error}</p>}
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', justifyContent: 'center' }}>
        {isVideo && (
          <div style={{ width: 160, background: '#222', borderRadius: 8, overflow: 'hidden' }}>
            <video ref={localVideoRef} autoPlay muted playsInline style={{ width: '100%', transform: 'scaleX(-1)' }} />
            <p style={{ fontSize: 11, color: '#888', margin: 0, padding: 4 }}>أنت</p>
          </div>
        )}
        <div style={{ width: isVideo ? 240 : 80, background: '#222', borderRadius: 8, overflow: 'hidden', minHeight: isVideo ? 180 : 40 }}>
          {isVideo && <p style={{ fontSize: 11, color: '#888', margin: '0 0 4px', padding: 4 }}>الطرف الآخر</p>}
          {isVideo ? (
            <video ref={remoteVideoRef} srcObject={remoteStream || undefined} autoPlay playsInline style={{ width: '100%', minHeight: 160 }} />
          ) : (
            <audio ref={remoteVideoRef} srcObject={remoteStream || undefined} autoPlay style={{ width: '100%' }} />
          )}
        </div>
      </div>
      <button type="button" onClick={onEnd} style={{ marginTop: 24, padding: '12px 24px', background: '#ef4444', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer', fontSize: 16 }}>إنهاء المكالمة</button>
    </div>
  );
}
