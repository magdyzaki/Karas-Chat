import { useState, useEffect, useCallback } from 'react';
import { io } from 'socket.io-client';
import * as api from './api';
import Auth from './Auth';
import ChatList from './ChatList';
import ChatRoom from './ChatRoom';
import InvitePage from './InvitePage';

const SOCKET_URL = import.meta.env.VITE_API_URL || '';
const ADMIN_IDS = (import.meta.env.VITE_ADMIN_USER_IDS || '1').split(',').map((s) => parseInt(s.trim(), 10)).filter(Boolean);
const isAdmin = (userId) => userId && ADMIN_IDS.length > 0 && ADMIN_IDS.includes(Number(userId));

function parseInviteToken() {
  const m = window.location.pathname.match(/^\/invite\/([a-zA-Z0-9_]+)/);
  return m ? m[1] : null;
}

function App() {
  const [user, setUser] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [currentConvId, setCurrentConvId] = useState(null);
  const [showNewChat, setShowNewChat] = useState(false);
  const [socket, setSocket] = useState(null);
  const [error, setError] = useState('');
  const [inviteToken, setInviteToken] = useState(() => parseInviteToken());
  const [inviteLinkModal, setInviteLinkModal] = useState(null); // { link, copied? }
  const [inviteLoading, setInviteLoading] = useState(false);

  const token = localStorage.getItem('chat_token');
  const savedUser = localStorage.getItem('chat_user');

  const handleInviteValid = () => {
    setInviteToken(null);
    window.history.replaceState({}, '', '/');
  };

  const handleCreateInviteLink = async () => {
    if (inviteLoading) return;
    setInviteLoading(true);
    setError('');
    try {
      const data = await api.createInviteLink();
      const link = window.location.origin + '/invite/' + (data.token || '');
      setInviteLinkModal({ link, copied: false });
    } catch (e) {
      const msg = e.message || 'فشل إنشاء الرابط';
      setError(msg);
      alert(msg);
    } finally {
      setInviteLoading(false);
    }
  };

  const copyInviteLink = () => {
    if (inviteLinkModal?.link) {
      navigator.clipboard?.writeText(inviteLinkModal.link).then(() => {
        setInviteLinkModal((p) => (p ? { ...p, copied: true } : null));
      });
    }
  };

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
    sock.on('new_message', () => {
      loadConversations();
    });
    setSocket(sock);
    return () => sock.disconnect();
  }, [user, token, loadConversations]);

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

  if (inviteToken) {
    return <InvitePage token={inviteToken} onValid={handleInviteValid} />;
  }

  if (!user) {
    return <Auth onLogin={handleLogin} />;
  }

  const currentConv = conversations.find((c) => c.id === currentConvId) || (currentConvId ? { id: currentConvId, label: 'محادثة' } : null);

  return (
    <div className="app-container" style={{ display: 'flex', height: '100dvh', flexDirection: 'column', maxWidth: 900, margin: '0 auto', width: '100%' }}>
      <header className="app-header" style={{ padding: '10px 12px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0 }}>
        <h1 style={{ margin: 0, fontSize: 'clamp(16px, 4vw, 18px)' }}>Karas شات</h1>
        <span style={{ fontSize: 12, color: 'var(--text-muted)', maxWidth: '40%', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{user.name || user.email || user.phone || 'أنت'}</span>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {isAdmin(user?.id) && (
            <button type="button" onClick={handleCreateInviteLink} disabled={inviteLoading} style={{ padding: '6px 10px', background: inviteLoading ? 'var(--text-muted)' : 'var(--primary)', border: 'none', borderRadius: 8, color: '#fff', cursor: inviteLoading ? 'wait' : 'pointer', fontSize: 12 }}>{inviteLoading ? '...' : 'رابط للآيفون'}</button>
          )}
          <button type="button" onClick={handleLogout} style={{ padding: '6px 10px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', cursor: 'pointer', fontSize: 13 }}>خروج</button>
        </div>
      </header>
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
      {inviteLinkModal && (
        <div onClick={() => setInviteLinkModal(null)} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 20, padding: 16 }}>
          <div onClick={(e) => e.stopPropagation()} style={{ background: 'var(--surface)', borderRadius: 12, padding: 20, maxWidth: 400, width: '100%' }}>
            <h3 style={{ marginTop: 0 }}>رابط للآيفون — يستخدم مرة واحدة فقط</h3>
            <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12 }}>أرسل هذا الرابط للشخص. عند فتحه على الآيفون سيُستهلك ولا يعمل على جهاز آخر.</p>
            <input type="text" readOnly value={inviteLinkModal.link} style={{ width: '100%', padding: 10, border: '1px solid var(--border)', borderRadius: 8, background: 'var(--bg)', color: 'var(--text)', marginBottom: 12 }} />
            <div style={{ display: 'flex', gap: 8 }}>
              <button type="button" onClick={copyInviteLink} style={{ flex: 1, padding: 10, background: 'var(--primary)', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer' }}>{inviteLinkModal.copied ? 'تم النسخ ✓' : 'نسخ الرابط'}</button>
              <button type="button" onClick={() => setInviteLinkModal(null)} style={{ padding: 10, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', cursor: 'pointer' }}>إغلاق</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
