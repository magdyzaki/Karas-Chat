import { useState, useEffect, useCallback } from 'react';
import { io } from 'socket.io-client';
import * as api from './api';
import Auth from './Auth';
import ChatList from './ChatList';
import ChatRoom from './ChatRoom';

const SOCKET_URL = import.meta.env.VITE_API_URL || '';

function App() {
  const [user, setUser] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [currentConvId, setCurrentConvId] = useState(null);
  const [showNewChat, setShowNewChat] = useState(false);
  const [socket, setSocket] = useState(null);
  const [error, setError] = useState('');

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
    const sock = io(base, { auth: { token }, transports: ['websocket', 'polling'] });
    sock.on('connect', () => {});
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

  const currentConv = conversations.find((c) => c.id === currentConvId);

  return (
    <div style={{ display: 'flex', height: '100vh', flexDirection: 'column', maxWidth: 900, margin: '0 auto' }}>
      <header style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0, fontSize: 18 }}>شات</h1>
        <span style={{ fontSize: 14, color: 'var(--text-muted)' }}>{user.name || user.email || user.phone || 'أنت'}</span>
        <button type="button" onClick={handleLogout} style={{ padding: '6px 12px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', cursor: 'pointer' }}>خروج</button>
      </header>
      {error && <p style={{ padding: 8, margin: 0, background: 'rgba(248,81,73,0.15)', color: '#f85149', textAlign: 'center' }}>{error}</p>}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
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
        {currentConvId ? (
          <ChatRoom
            conversation={currentConv}
            socket={socket}
            currentUserId={user.id}
            onBack={() => setCurrentConvId(null)}
          />
        ) : (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>اختر محادثة أو ابدأ محادثة جديدة</div>
        )}
      </div>
    </div>
  );
}

export default App;
