import { useState, useEffect, useCallback } from 'react';
import { io } from 'socket.io-client';
import * as api from './api';
import Auth from './Auth';
import ChatList from './ChatList';
import ChatRoom from './ChatRoom';

const SOCKET_URL = import.meta.env.VITE_API_URL || '';
const BUILD_ID = 'chat-2026-02-10-01';

function App() {
  const [user, setUser] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [currentConvId, setCurrentConvId] = useState(null);
  const [showNewChat, setShowNewChat] = useState(false);
  const [socket, setSocket] = useState(null);
  const [error, setError] = useState('');
  const [socketStatus, setSocketStatus] = useState('idle'); // idle | connecting | connected | disconnected | error
  const [socketError, setSocketError] = useState('');
  const [socketBase, setSocketBase] = useState('');

  const token = localStorage.getItem('chat_token');
  const savedUser = localStorage.getItem('chat_user');

  useEffect(() => {
    if (savedUser && token) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (_) {
        localStorage.removeItem('chat_user');
        localStorage.removeItem('chat_token');
      }
    }
  }, [token, savedUser]);

  const loadConversations = useCallback(async () => {
    if (!token) return;
    try {
      const list = await api.getConversations();
      setConversations(list);
      setError('');
    } catch (e) {
      setError(e.message || 'خطأ في التحميل');
    }
  }, [token]);

  useEffect(() => {
    if (!user) return;
    loadConversations();
  }, [user, loadConversations]);

  useEffect(() => {
    if (!user || !token) return;
    const base = SOCKET_URL || window.location.origin;
    setSocketBase(base);
    setSocketStatus('connecting');
    setSocketError('');
    const sock = io(base, { auth: { token }, transports: ['websocket', 'polling'] });
    sock.on('connect', () => {
      setSocketStatus('connected');
      setSocketError('');
    });
    sock.on('disconnect', () => {
      setSocketStatus('disconnected');
    });
    sock.on('connect_error', (err) => {
      setSocketStatus('error');
      setSocketError(err?.message || 'Socket connect_error');
    });
    sock.on('new_message', (msg) => {
      setConversations((prev) => {
        const rest = prev.filter((c) => c.id !== msg.conversation_id);
        const conv = prev.find((c) => c.id === msg.conversation_id);
        if (!conv) return prev;
        return [{ ...conv }, ...rest];
      });
    });
    setSocket(sock);
    return () => sock.disconnect();
  }, [user, token]);

  const handleLogin = (data) => {
    localStorage.setItem('chat_token', data.token);
    localStorage.setItem('chat_user', JSON.stringify(data.user));
    setUser(data.user);
  };

  const handleLogout = () => {
    if (socket) socket.disconnect();
    localStorage.removeItem('chat_token');
    localStorage.removeItem('chat_user');
    setUser(null);
    setConversations([]);
    setCurrentConvId(null);
  };

  const handleStartDirect = async (otherUserId) => {
    try {
      setError('');
      const conv = await api.createDirectConversation(otherUserId);
      setConversations((prev) => [{ ...conv, label: conv.label || conv.name || 'محادثة جديدة' }, ...prev.filter((c) => c.id !== conv.id)]);
      setCurrentConvId(conv.id);
      setShowNewChat(false);
      loadConversations();
    } catch (e) {
      setError(e.message || 'فشل إنشاء المحادثة');
    }
  };

  const handleCreateGroup = async (name, memberIds) => {
    try {
      setError('');
      const conv = await api.createGroupConversation(name, memberIds);
      setConversations((prev) => [{ ...conv, label: conv.name || name || 'مجموعة جديدة' }, ...prev.filter((c) => c.id !== conv.id)]);
      setCurrentConvId(conv.id);
      setShowNewChat(false);
      loadConversations();
    } catch (e) {
      setError(e.message || 'فشل إنشاء المجموعة');
    }
  };

  if (!user) {
    return <Auth onLogin={handleLogin} />;
  }

  const currentConv = conversations.find((c) => c.id === currentConvId) || (currentConvId ? { id: currentConvId, label: 'محادثة' } : null);

  return (
    <div className="app-container" style={{ display: 'flex', height: '100dvh', flexDirection: 'column', maxWidth: 900, margin: '0 auto', width: '100%' }}>
      <header className="app-header" style={{ padding: '10px 12px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0 }}>
        <h1 style={{ margin: 0, fontSize: 'clamp(16px, 4vw, 18px)' }}>شات</h1>
        <span style={{ fontSize: 12, color: 'var(--text-muted)', maxWidth: '40%', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{user.name || user.email || user.phone || 'أنت'}</span>
        <button type="button" onClick={handleLogout} style={{ padding: '6px 10px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', cursor: 'pointer', fontSize: 13 }}>خروج</button>
      </header>
      <div style={{ padding: '6px 12px', borderBottom: '1px solid var(--border)', fontSize: 12, color: 'var(--text-muted)' }}>
        <span>Build: {BUILD_ID}</span>
        <span style={{ marginRight: 10 }}>• Socket: {socketStatus}</span>
        {socketError && <span style={{ marginRight: 10, color: '#f85149' }}>({socketError})</span>}
        {socketBase && <span style={{ display: 'block', opacity: 0.75, marginTop: 2, direction: 'ltr', textAlign: 'left' }}>base: {socketBase}</span>}
      </div>
      {error && <p style={{ padding: 6, margin: 0, background: 'rgba(248,81,73,0.15)', color: '#f85149', textAlign: 'center', fontSize: 13 }}>{error}</p>}
      <div className={`app-flex ${currentConvId ? 'room-open' : ''}`} style={{ flex: 1, display: 'flex', overflow: 'hidden', minHeight: 0 }}>
        <div className="chat-list-wrap">
        <ChatList
          conversations={conversations}
          currentConvId={currentConvId}
          onSelect={setCurrentConvId}
          onNewChat={() => setShowNewChat(true)}
          onStartDirect={handleStartDirect}
          onCreateGroup={handleCreateGroup}
          showNewChat={showNewChat}
          onCloseNewChat={() => setShowNewChat(false)}
          currentUserId={user.id}
        />
        </div>
        <div className="chat-room-wrap">
        {currentConvId ? (
          <ChatRoom
            conversation={currentConv}
            socket={socket}
            currentUserId={user.id}
            onBack={() => setCurrentConvId(null)}
          />
        ) : (
          <div className="chat-placeholder" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', padding: 16, textAlign: 'center' }}>اختر محادثة أو ابدأ محادثة جديدة</div>
        )}
        </div>
      </div>
    </div>
  );
}

export default App;
