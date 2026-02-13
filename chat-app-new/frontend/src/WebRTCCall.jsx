/** مكوّن WebRTC للمكالمات الفردية - صوت وفيديو */
import { useState, useEffect, useRef } from 'react';

export default function WebRTCCall({ socket, conversationId, remoteUserId, isInitiator, isVideo, onEnd }) {
  const [status, setStatus] = useState(isInitiator ? 'connecting' : 'incoming');
  const [error, setError] = useState('');
  const localVideoRef = useRef(null);
  const remoteVideoRef = useRef(null);
  const peerRef = useRef(null);
  const localStreamRef = useRef(null);

  useEffect(() => {
    if (!socket || !conversationId || !remoteUserId) return;

    const setupPeer = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: isVideo });
        localStreamRef.current = stream;
        if (localVideoRef.current && isVideo) localVideoRef.current.srcObject = stream;

        const pc = new RTCPeerConnection({ iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] });
        peerRef.current = pc;

        stream.getTracks().forEach((t) => pc.addTrack(t, stream));

        const remoteStream = new MediaStream();
        pc.ontrack = (e) => {
          if (e.track && !remoteStream.getTracks().includes(e.track)) {
            remoteStream.addTrack(e.track);
          }
          if (remoteVideoRef.current && remoteStream.getTracks().length > 0) {
            remoteVideoRef.current.srcObject = remoteStream;
          }
        };

        pc.onicecandidate = (e) => {
          if (e.candidate) socket.emit('webrtc_signal', { conversationId, toUserId: remoteUserId, signal: { candidate: e.candidate } });
        };

        if (isInitiator) {
          setStatus('connecting');
          const offer = await pc.createOffer();
          await pc.setLocalDescription(offer);
          socket.emit('webrtc_signal', { conversationId, toUserId: remoteUserId, signal: { sdp: offer } });
        }
      } catch (err) {
        setError(err.message || 'فشل بدء المكالمة');
        setStatus('error');
      }
    };

    const onSignal = (data) => {
      if (data.conversationId !== conversationId || data.fromUserId !== Number(remoteUserId)) return;
      const { signal } = data;
      const pc = peerRef.current;
      if (!pc) return;

      (async () => {
        try {
          if (signal.sdp) {
            await pc.setRemoteDescription(new RTCSessionDescription(signal.sdp));
            if (signal.sdp.type === 'offer') {
              setStatus('connecting');
              const answer = await pc.createAnswer();
              await pc.setLocalDescription(answer);
              socket.emit('webrtc_signal', { conversationId, toUserId: remoteUserId, signal: { sdp: pc.localDescription } });
            } else {
              setStatus('connected');
            }
          } else if (signal.candidate) {
            await pc.addIceCandidate(new RTCIceCandidate(signal.candidate));
          }
        } catch (err) {
          setError(err.message || 'خطأ في الإشارة');
        }
      })();
    };

    socket.on('webrtc_signal', onSignal);
    setupPeer();
    return () => {
      socket.off('webrtc_signal', onSignal);
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
        <div style={{ width: isVideo ? 240 : 80, background: '#222', borderRadius: 8, overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          {isVideo ? <video ref={remoteVideoRef} autoPlay playsInline style={{ width: '100%' }} /> : <audio ref={remoteVideoRef} autoPlay style={{ width: '100%' }} />}
        </div>
      </div>
      <button type="button" onClick={onEnd} style={{ marginTop: 24, padding: '12px 24px', background: '#ef4444', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer', fontSize: 16 }}>إنهاء المكالمة</button>
    </div>
  );
}
