import { useState, useEffect, useCallback } from 'react';
import { io } from 'socket.io-client';
import * as api from './api';
import Auth from './Auth';
import ChatList from './ChatList';
import ChatRoom from './ChatRoom';

const SOCKET_URL = import.meta.env.VITE_API_URL || '';

export default function App() {
  const [user, setUser] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [currentConvId, setCurrentConvId] = useState(null);
  const [showNewChat, setShowNewChat] = useState(false);
  const [socket, setSocket] = useState(null);
  const [error, setError] = useState('');
  const [incomingCall, setIncomingCall] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('chat_token');
    const saved = localStorage.getItem('chat_user');
    if (token && saved) {
      try {
        setUser(JSON.parse(saved));
      } catch (_) {
        localStorage.removeItem('chat_token');
        localStorage.removeItem('chat_user');
      }
    }
  }, []);

  const loadConvs = useCallback(async () => {
    try {
      const list = await api.getConversations();
      setConversations(list);
      setError('');
    } catch (e) {
      setError(e.message || 'خطأ');
    }
  }, []);

  useEffect(() => {
    if (user) loadConvs();
  }, [user, loadConvs]);

  useEffect(() => {
    if (!user) return;
    const token = localStorage.getItem('chat_token');
    const sock = io(SOCKET_URL || window.location.origin, { auth: { token }, transports: ['websocket', 'polling'] });
    sock.on('incoming_call', (data) => setIncomingCall(data));
    sock.on('call_ended', () => setIncomingCall(null));
    setSocket(sock);
    return () => sock.disconnect();
  }, [user]);

  useEffect(() => {
    if (socket?.connected && conversations?.length) {
      conversations.forEach((c) => c?.id && socket.emit('join_conversation', c.id));
    }
  }, [socket?.connected, conversations]);

  const handleLogin = (data) => {
    setUser(data.user);
  };

  const handleLogout = () => {
    socket?.disconnect();
    localStorage.removeItem('chat_token');
    localStorage.removeItem('chat_user');
    setUser(null);
    setConversations([]);
    setCurrentConvId(null);
  };

  const handleStartDirect = async (otherUserId) => {
    try {
      const conv = await api.createDirectConversation(otherUserId);
      setConversations((p) => [{ ...conv }, ...p.filter((c) => c.id !== conv.id)]);
      setCurrentConvId(conv.id);
      setShowNewChat(false);
      loadConvs();
    } catch (e) {
      setError(e.message || 'فشل');
    }
  };

  const handleCreateGroup = async (name, memberIds) => {
    try {
      const conv = await api.createGroupConversation(name, memberIds);
      setConversations((p) => [{ ...conv }, ...p.filter((c) => c.id !== conv.id)]);
      setCurrentConvId(conv.id);
      setShowNewChat(false);
      loadConvs();
    } catch (e) {
      setError(e.message || 'فشل');
    }
  };

  const acceptCall = () => {
    if (!incomingCall || !socket) return;
    socket.emit('answer_call', { callerUserId: incomingCall.fromUserId });
    setCurrentConvId(incomingCall.conversationId);
    setIncomingCall({ ...incomingCall, accepted: true }); // سيُعرض CallOverlay في ChatRoom
  };

  const rejectCall = () => {
    if (incomingCall && socket) socket.emit('reject_call', { callerUserId: incomingCall.fromUserId });
    setIncomingCall(null);
  };

  if (!user) {
    return <Auth onLogin={handleLogin} />;
  }

  const currentConv = conversations.find((c) => c.id === currentConvId) || (currentConvId ? { id: currentConvId, label: 'محادثة' } : null);

  return (
    <div style={{ display: 'flex', height: '100dvh', maxWidth: 900, margin: '0 auto', width: '100%', background: '#0d1117', direction: 'rtl' }}>
      <ChatList
        conversations={conversations}
        currentConvId={currentConvId}
        onSelect={setCurrentConvId}
        onNewChat={() => setShowNewChat(true)}
        onCloseNewChat={() => setShowNewChat(false)}
        showNewChat={showNewChat}
        onStartDirect={handleStartDirect}
        onCreateGroup={handleCreateGroup}
        currentUserId={user?.id}
      />
      {currentConv ? (
        <ChatRoom
          conversationId={currentConv.id}
          convDetails={currentConv}
          socket={socket}
          currentUserId={user?.id}
          onBack={() => setCurrentConvId(null)}
          incomingCall={incomingCall}
          onEndCall={() => setIncomingCall(null)}
        />
      ) : (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#8b949e' }}>اختر محادثة أو أنشئ واحدة جديدة</div>
      )}

      {error && <div style={{ position: 'fixed', top: 12, left: '50%', transform: 'translateX(-50%)', padding: '8px 16px', background: '#f85149', color: '#fff', borderRadius: 8, zIndex: 30 }}>{error}</div>}

      {incomingCall && !incomingCall.accepted && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', zIndex: 25, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
          <p style={{ fontSize: 18 }}>مكالمة من {incomingCall.fromUserName || 'شخص'}</p>
          <div style={{ display: 'flex', gap: 16, marginTop: 24 }}>
            <button type="button" onClick={acceptCall} style={{ padding: '12px 24px', background: '#238636', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer' }}>قبول</button>
            <button type="button" onClick={rejectCall} style={{ padding: '12px 24px', background: '#da3633', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer' }}>رفض</button>
          </div>
        </div>
      )}

      <button type="button" onClick={handleLogout} style={{ position: 'fixed', top: 8, left: 8, padding: '6px 12px', background: '#21262d', border: '1px solid #30363d', borderRadius: 6, color: '#fff', cursor: 'pointer', fontSize: 12 }}>خروج</button>
    </div>
  );
}
