import { useState, useEffect, useCallback, useRef } from 'react';
import { io } from 'socket.io-client';
import * as api from './api';
import Auth from './Auth';
import ChatList from './ChatList';
import ChatRoom from './ChatRoom';
import InvitePage from './InvitePage';
import Settings from './Settings';

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
  const [showBlockedModal, setShowBlockedModal] = useState(false);
  const [blockedUsers, setBlockedUsers] = useState([]);
  const [showSettings, setShowSettings] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);

  const token = localStorage.getItem('chat_token');

  useEffect(() => {
    const closeMenu = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false);
    };
    document.addEventListener('click', closeMenu);
    return () => document.removeEventListener('click', closeMenu);
  }, []);
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
    const theme = localStorage.getItem('chat_theme') || 'dark';
    const wp = localStorage.getItem('chat_wallpaper') || 'default';
    const bg = localStorage.getItem('chat_bg') || 'none';
    const fs = localStorage.getItem('chat_font_size') || 'medium';
    document.documentElement.dataset.theme = theme;
    document.body.dataset.chatBg = bg;
    document.documentElement.dataset.fontSize = fs;
    const wpBg = wp === 'default' ? 'var(--bg)' : wp === 'dark' ? '#0d1117' : wp === 'blue' ? 'linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%)' : wp === 'green' ? 'linear-gradient(135deg, #0d2818 0%, #1a3d2e 100%)' : wp === 'purple' ? 'linear-gradient(135deg, #1a0d2e 0%, #2d1b4e 100%)' : wp === 'light' ? '#f0f2f5' : 'var(--bg)';
    document.documentElement.style.setProperty('--chat-wallpaper', wpBg);
    document.body.style.background = wpBg;
  }, []);

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

  const handleUserUpdate = (updates) => {
    if (!user) return;
    const updated = { ...user, ...updates };
    setUser(updated);
    localStorage.setItem('chat_user', JSON.stringify(updated));
  };

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

  const handleBlockUser = async (targetUserId) => {
    if (!confirm('هل تريد إيقاف وصول هذا المستخدم؟ لن يستطيع فتح التطبيق مرة أخرى حتى تعيد تفعيله.')) return;
    try {
      await api.blockUser(targetUserId);
      setError('');
      loadConversations();
      setCurrentConvId(null);
    } catch (e) {
      setError(e.message || 'فشل إيقاف المستخدم');
    }
  };

  const loadBlockedUsers = useCallback(async () => {
    if (!isAdmin(user?.id)) return;
    try {
      const list = await api.getBlockedUsers();
      setBlockedUsers(list);
    } catch (_) {}
  }, [user?.id]);

  const handleUnblockUser = async (targetUserId) => {
    try {
      await api.unblockUser(targetUserId);
      setBlockedUsers((prev) => prev.filter((u) => u.id !== targetUserId));
    } catch (e) {
      setError(e.message || 'فشل إعادة التفعيل');
    }
  };

  const handleLeaveGroup = async (convId) => {
    try {
      await api.leaveGroup(convId);
      setConversations((prev) => prev.filter((c) => c.id !== convId));
      setCurrentConvId(null);
      loadConversations();
    } catch (e) {
      setError(e.message || 'فشل مغادرة المجموعة');
    }
  };

  const handleDeleteGroup = async (convId) => {
    if (!confirm('هل أنت متأكد من حذف المجموعة نهائياً؟')) return;
    try {
      await api.deleteGroup(convId);
      setConversations((prev) => prev.filter((c) => c.id !== convId));
      setCurrentConvId(null);
      loadConversations();
    } catch (e) {
      setError(e.message || 'فشل حذف المجموعة');
    }
  };

  const handleConversationUpdate = (updated) => {
    setConversations((prev) => prev.map((c) => (c.id === updated.id ? { ...c, memberIds: updated.memberIds, memberDetails: updated.memberDetails } : c)));
  };

  const handleRemoveMember = async (convId, targetUserId) => {
    if (!confirm('هل تريد طرد هذا العضو من المجموعة؟')) return;
    try {
      await api.removeMemberFromGroup(convId, targetUserId);
      const updated = await api.getConversation(convId);
      setConversations((prev) => prev.map((c) => (c.id === convId ? { ...c, memberIds: updated.memberIds || c.memberIds, memberDetails: updated.memberDetails || c.memberDetails } : c)));
    } catch (e) {
      setError(e.message || 'فشل طرد العضو');
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
        <span style={{ fontSize: 12, color: 'var(--text-muted)', maxWidth: '40%', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: 6 }}>
          {user?.avatar_url ? <img src={api.uploadsUrl(user.avatar_url)} alt="" style={{ width: 24, height: 24, borderRadius: '50%', objectFit: 'cover' }} /> : null}
          {user.name || user.email || user.phone || 'أنت'}
          <span style={{ fontSize: 10, opacity: 0.8 }}>(معرف: {user.id})</span>
        </span>
        <div ref={menuRef} style={{ position: 'relative' }}>
          <button
            type="button"
            onClick={() => setMenuOpen((o) => !o)}
            style={{ padding: '8px 14px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', cursor: 'pointer', fontSize: 14, display: 'flex', alignItems: 'center', gap: 6 }}
            title="القائمة والإعدادات"
          >
            <span>⚙</span>
            <span>القائمة</span>
          </button>
          {menuOpen && (
            <div
              style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                marginTop: 4,
                background: 'var(--surface)',
                border: '1px solid var(--border)',
                borderRadius: 8,
                boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                minWidth: 180,
                zIndex: 25
              }}
            >
              <button
                type="button"
                onClick={() => { setShowSettings(true); setMenuOpen(false); }}
                style={{ display: 'block', width: '100%', padding: '12px 16px', background: 'none', border: 'none', color: 'var(--text)', cursor: 'pointer', fontSize: 14, textAlign: 'right' }}
              >
                الإعدادات
              </button>
              {isAdmin(user?.id) && (
                <>
                  <button
                    type="button"
                    onClick={() => { setShowBlockedModal(true); loadBlockedUsers(); setMenuOpen(false); }}
                    style={{ display: 'block', width: '100%', padding: '12px 16px', background: 'none', border: 'none', color: 'var(--text)', cursor: 'pointer', fontSize: 14, textAlign: 'right' }}
                  >
                    الموقوفون
                  </button>
                  <button
                    type="button"
                    onClick={() => { handleCreateInviteLink(); setMenuOpen(false); }}
                    disabled={inviteLoading}
                    style={{ display: 'block', width: '100%', padding: '12px 16px', background: 'none', border: 'none', color: inviteLoading ? 'var(--text-muted)' : 'var(--text)', cursor: inviteLoading ? 'wait' : 'pointer', fontSize: 14, textAlign: 'right' }}
                  >
                    {inviteLoading ? 'جاري...' : 'رابط دعوة'}
                  </button>
                </>
              )}
              <div style={{ borderTop: '1px solid var(--border)' }} />
              <button
                type="button"
                onClick={() => { handleLogout(); setMenuOpen(false); }}
                style={{ display: 'block', width: '100%', padding: '12px 16px', background: 'none', border: 'none', color: '#f85149', cursor: 'pointer', fontSize: 14, textAlign: 'right' }}
              >
                خروج
              </button>
            </div>
          )}
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
              isAdmin={isAdmin(user?.id)}
              onBlockUser={handleBlockUser}
              onLeaveGroup={handleLeaveGroup}
              onDeleteGroup={handleDeleteGroup}
              onRemoveMember={handleRemoveMember}
              onConversationUpdate={handleConversationUpdate}
            />
          ) : (
            <div className="chat-placeholder" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', padding: 16, textAlign: 'center' }}>اختر محادثة أو ابدأ محادثة جديدة</div>
          )}
        </div>
      </div>
      {inviteLinkModal && (
        <div onClick={() => setInviteLinkModal(null)} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 20, padding: 16 }}>
          <div onClick={(e) => e.stopPropagation()} style={{ background: 'var(--surface)', borderRadius: 12, padding: 20, maxWidth: 400, width: '100%' }}>
            <h3 style={{ marginTop: 0 }}>رابط دعوة — للآيفون والأندرويد</h3>
            <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12 }}>الرابط يعمل على الجهازين. استخدمه مرة واحدة ولا يُعاد إرساله.</p>
            <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
              <button type="button" onClick={handleCreateInviteLink} disabled={inviteLoading} style={{ flex: 1, padding: 10, background: inviteLoading ? 'var(--text-muted)' : 'rgba(0,0,0,0.1)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', cursor: inviteLoading ? 'wait' : 'pointer', fontSize: 14 }}>{inviteLoading ? '...' : '📱 للآيفون'}</button>
              <button type="button" onClick={handleCreateInviteLink} disabled={inviteLoading} style={{ flex: 1, padding: 10, background: inviteLoading ? 'var(--text-muted)' : 'rgba(0,0,0,0.1)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', cursor: inviteLoading ? 'wait' : 'pointer', fontSize: 14 }}>{inviteLoading ? '...' : '🤖 للأندرويد'}</button>
            </div>
            {inviteLinkModal.link && (
              <>
                <input type="text" readOnly value={inviteLinkModal.link} style={{ width: '100%', padding: 10, border: '1px solid var(--border)', borderRadius: 8, background: 'var(--bg)', color: 'var(--text)', marginBottom: 12 }} />
                <div style={{ display: 'flex', gap: 8 }}>
                  <button type="button" onClick={copyInviteLink} style={{ flex: 1, padding: 10, background: 'var(--primary)', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer' }}>{inviteLinkModal.copied ? 'تم النسخ ✓' : 'نسخ الرابط'}</button>
                  <button type="button" onClick={() => setInviteLinkModal(null)} style={{ padding: 10, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', cursor: 'pointer' }}>إغلاق</button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
      {showSettings && (
        <Settings
          user={user}
          onClose={() => setShowSettings(false)}
          onUpdate={handleUserUpdate}
        />
      )}
      {showBlockedModal && isAdmin(user?.id) && (
        <div onClick={() => setShowBlockedModal(false)} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 20, padding: 16 }}>
          <div onClick={(e) => e.stopPropagation()} style={{ background: 'var(--surface)', borderRadius: 12, padding: 20, maxWidth: 400, width: '100%', maxHeight: '70vh', overflow: 'auto' }}>
            <h3 style={{ marginTop: 0 }}>المستخدمون الموقوفون</h3>
            <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12 }}>يمكنك إعادة تفعيل أي شخص من هنا</p>
            {blockedUsers.length === 0 ? (
              <p style={{ color: 'var(--text-muted)' }}>لا يوجد موقوفون</p>
            ) : (
              blockedUsers.map((u) => (
                <div key={u.id} style={{ padding: '10px 0', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>{u.name || u.phone || u.email || '—'}</span>
                  <button type="button" onClick={() => handleUnblockUser(u.id)} style={{ padding: '6px 12px', background: 'var(--primary)', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer', fontSize: 12 }}>إعادة التفعيل</button>
                </div>
              ))
            )}
            <button type="button" onClick={() => setShowBlockedModal(false)} style={{ marginTop: 12, padding: '8px 16px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', cursor: 'pointer' }}>إغلاق</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
