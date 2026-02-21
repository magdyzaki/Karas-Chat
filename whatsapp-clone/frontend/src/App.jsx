import { useState, useEffect, useCallback } from 'react';
import { io } from 'socket.io-client';
import * as api from './api';
import Auth from './Auth';
import ChatList from './ChatList';
import ChatRoom from './ChatRoom';
import BroadcastCompose from './BroadcastCompose';
import Stories from './Stories';
import StoryCreate from './StoryCreate';
import Settings from './Settings';
import InvitePage from './InvitePage';
import InviteLinkModal from './InviteLinkModal';
import BlockUserModal from './BlockUserModal';
import PendingCodesModal from './PendingCodesModal';
import CallModal from './CallModal';
import WebRTCCall from './WebRTCCall';
import { playReceived, playCallRing, stopCallRing } from './sounds';

const SOCKET_URL = import.meta.env.VITE_API_URL || '';
const BUILD_ID = 'chat-2026-02-10-02';

function App() {
  const [user, setUser] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [currentConvId, setCurrentConvId] = useState(null);
  const [showNewChat, setShowNewChat] = useState(false);
  const [newChatInitialTab, setNewChatInitialTab] = useState('direct');
  const [socket, setSocket] = useState(null);
  const [error, setError] = useState('');
  const [socketStatus, setSocketStatus] = useState('idle');
  const [socketError, setSocketError] = useState('');
  const [socketBase, setSocketBase] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const [showInviteLink, setShowInviteLink] = useState(false);
  const [showBlockUser, setShowBlockUser] = useState(false);
  const [showMyId, setShowMyId] = useState(false);
  const [showPendingCodes, setShowPendingCodes] = useState(false);
  const [incomingCall, setIncomingCall] = useState(null);
  const [activeCall, setActiveCall] = useState(null);
  const [storiesFeed, setStoriesFeed] = useState([]);
  const [showStoryCreate, setShowStoryCreate] = useState(false);
  const [broadcastLists, setBroadcastLists] = useState([]);

  const token = localStorage.getItem('chat_token');
  const savedUser = localStorage.getItem('chat_user');
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    if (savedUser && token) {
        try {
        const u = JSON.parse(savedUser);
        setUser(u);
        setIsAdmin(!!u?.isAdmin || u?.id === 1);
      } catch (_) {
        localStorage.removeItem('chat_user');
        localStorage.removeItem('chat_token');
      }
    }
  }, [token, savedUser]);

  useEffect(() => {
    if (user && token) {
      api.getMe().then((d) => { if (d) { setIsAdmin(!!d.isAdmin); setUser((u) => u && ({ ...u, ...d })); localStorage.setItem('chat_user', JSON.stringify({ ...user, ...d })); } }).catch(() => {});
    }
  }, [user?.id, token]);

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

  const loadBroadcastLists = useCallback(async () => {
    if (!token) return;
    try {
      const list = await api.getBroadcastLists();
      setBroadcastLists(list);
    } catch (_) {}
  }, [token]);

  useEffect(() => {
    if (user && token) loadBroadcastLists();
  }, [user, token, loadBroadcastLists]);

  const loadStories = useCallback(async () => {
    if (!token) return;
    try {
      const feed = await api.getStories();
      setStoriesFeed(feed || []);
    } catch (_) {}
  }, [token]);

  useEffect(() => {
    if (user && token) loadStories();
  }, [user, token, loadStories]);

  useEffect(() => {
    if (!socket || !user) return;
    socket.on('new_story', () => loadStories());
    return () => socket.off('new_story');
  }, [socket, user, loadStories]);

  useEffect(() => {
    if (!user || !token) return;
    const base = SOCKET_URL || window.location.origin;
    setSocketBase(base);
    setSocketStatus('connecting');
    setSocketError('');
    const sock = io(base, { auth: { token }, transports: ['websocket', 'polling'] });
    sock.on('connect', () => { setSocketStatus('connected'); setSocketError(''); });
    sock.on('disconnect', () => setSocketStatus('disconnected'));
    sock.on('connect_error', (err) => {
      setSocketStatus('error');
      setSocketError(err?.message || 'Socket connect_error');
    });
    sock.on('new_message', (msg) => {
      const isFromOthers = Number(msg.sender_id) !== Number(user?.id);
      if (isFromOthers) playReceived();
      setConversations((prev) => {
        const rest = prev.filter((c) => c.id !== msg.conversation_id);
        const conv = prev.find((c) => c.id === msg.conversation_id);
        if (!conv) return prev;
        return [{ ...conv }, ...rest];
      });
    });
    sock.on('incoming_call', (data) => {
      playCallRing();
      setIncomingCall(data);
    });
    sock.on('call_ended', (data) => { stopCallRing(); setIncomingCall(null); setActiveCall(null); });
    setSocket(sock);
    return () => {
      sock.off('new_message');
      sock.off('incoming_call');
      sock.off('call_ended');
      sock.disconnect();
    };
  }, [user, token]);

  useEffect(() => {
    if (socket?.connected && conversations?.length > 0) {
      conversations.forEach((c) => c?.id && socket.emit('join_conversation', c.id));
    }
  }, [socket, socketStatus, conversations]);

  useEffect(() => {
    if (!user || !token) return;
    const key = import.meta.env.VITE_VAPID_PUBLIC_KEY;
    if (!key || !('serviceWorker' in navigator) || !('PushManager' in window)) return;
    navigator.serviceWorker.ready.then(async (reg) => {
      if (Notification.permission !== 'granted') return;
      try {
        let sub = await reg.pushManager.getSubscription();
        if (!sub) sub = await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: key });
        if (sub) await api.subscribePush(sub.toJSON());
      } catch (_) {}
    }).catch(() => {});
  }, [user?.id, token]);

  const handleLogin = (data) => {
    localStorage.setItem('chat_token', data.token);
    localStorage.setItem('chat_user', JSON.stringify(data.user));
    setUser(data.user);
    setIsAdmin(!!data.user?.isAdmin);
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

  const handleCreateBroadcast = async (name, recipientIds) => {
    try {
      setError('');
      const list = await api.createBroadcastList(name, recipientIds);
      setBroadcastLists((prev) => [{ ...list }, ...prev]);
      setCurrentConvId('broadcast-' + list.id);
      setShowNewChat(false);
      loadBroadcastLists();
    } catch (e) {
      setError(e.message || 'فشل إنشاء القائمة');
    }
  };

  const inviteToken = (() => { const m = typeof window !== 'undefined' && window.location.search.match(/\binvite=([^&]+)/); return m ? m[1] : null; })();

  if (inviteToken && !user) {
    return <InvitePage token={inviteToken} onValid={() => { window.history.replaceState({}, '', window.location.pathname); }} />;
  }

  if (!user) {
    return <Auth onLogin={handleLogin} />;
  }

  const currentConv = conversations.find((c) => c.id === currentConvId) || (currentConvId && !String(currentConvId).startsWith('broadcast-') ? { id: currentConvId, label: 'محادثة' } : null);
  const isBroadcast = currentConvId && String(currentConvId).startsWith('broadcast-');
  const broadcastListId = isBroadcast ? currentConvId.replace('broadcast-', '') : null;
  const currentBroadcastList = broadcastLists.find((b) => String(b.id) === String(broadcastListId));

  return (
    <div className="app-container" style={{ display: 'flex', height: '100dvh', flexDirection: 'column', maxWidth: 900, margin: '0 auto', width: '100%' }}>
      <header className="app-header" style={{ padding: '10px 12px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0 }}>
        <h1 style={{ margin: 0, fontSize: 'clamp(16px, 4vw, 18px)' }}>شات</h1>
        <span style={{ fontSize: 12, color: 'var(--text-muted)', maxWidth: '30%', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: 6 }}>
          {user.avatar_url ? <img src={api.uploadsUrl(user.avatar_url)} alt="" style={{ width: 24, height: 24, borderRadius: '50%', objectFit: 'cover' }} /> : <span style={{ fontSize: 14 }}>👤</span>}
          {user.name || user.email || user.phone || 'أنت'} ({user.id})
        </span>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', position: 'relative' }}>
          <button type="button" onClick={() => setShowMenu((v) => !v)} style={{ padding: '6px 10px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', cursor: 'pointer', fontSize: 13 }} title="القائمة">☰ القائمة</button>
          {showMenu && (
            <>
              <div style={{ position: 'fixed', inset: 0, zIndex: 9 }} onClick={() => setShowMenu(false)} />
              <div style={{ position: 'absolute', top: '100%', left: 0, marginTop: 4, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, boxShadow: '0 4px 12px rgba(0,0,0,0.3)', zIndex: 10, minWidth: 240 }}>
                {currentConvId && (
                  <button type="button" onClick={() => { setCurrentConvId(null); setShowMenu(false); }} style={{ display: 'block', width: '100%', padding: '10px 16px', border: 'none', background: 'none', color: 'var(--text)', cursor: 'pointer', fontSize: 14, textAlign: 'right' }}>📋 المحادثات</button>
                )}
                <button type="button" onClick={() => { setShowMyId(true); setShowMenu(false); }} style={{ display: 'block', width: '100%', padding: '10px 16px', border: 'none', background: 'none', color: 'var(--text)', cursor: 'pointer', fontSize: 14, textAlign: 'right' }}>🆔 معرفي: {user.id}</button>
                {isAdmin && (
                  <>
                    <button type="button" onClick={() => { setShowPendingCodes(true); setShowMenu(false); }} style={{ display: 'block', width: '100%', padding: '10px 16px', border: 'none', background: 'none', color: 'var(--text)', cursor: 'pointer', fontSize: 14, textAlign: 'right' }}>📥 التسجيلات والتفعيل</button>
                    <button type="button" onClick={() => { setShowInviteLink(true); setShowMenu(false); }} style={{ display: 'block', width: '100%', padding: '10px 16px', border: 'none', background: 'none', color: 'var(--text)', cursor: 'pointer', fontSize: 14, textAlign: 'right' }}>🔗 رابط الدعوة (آيفون/أندرويد)</button>
                    <button type="button" onClick={() => { setShowBlockUser(true); setShowMenu(false); }} style={{ display: 'block', width: '100%', padding: '10px 16px', border: 'none', background: 'none', color: 'var(--text)', cursor: 'pointer', fontSize: 14, textAlign: 'right' }}>🚫 إيقاف مستخدم</button>
                  </>
                )}
                <button type="button" onClick={() => { setShowSettings(true); setShowMenu(false); }} style={{ display: 'block', width: '100%', padding: '10px 16px', border: 'none', background: 'none', color: 'var(--text)', cursor: 'pointer', fontSize: 14, textAlign: 'right' }}>⚙️ إعدادات المظهر (خط، ألوان، خلفية)</button>
                {isAdmin && (
                  <button type="button" onClick={async () => { setShowMenu(false); try { await api.resetDatabase(); } catch (_) {} localStorage.removeItem('chat_token'); localStorage.removeItem('chat_user'); setUser(null); setConversations([]); setCurrentConvId(null); if (socket) socket.disconnect(); }} style={{ display: 'block', width: '100%', padding: '10px 16px', border: 'none', background: 'none', color: 'var(--primary)', cursor: 'pointer', fontSize: 14, textAlign: 'right' }}>🗑️ مسح كل البيانات والتسجيل من جديد</button>
                )}
                <button type="button" onClick={() => { handleLogout(); setShowMenu(false); }} style={{ display: 'block', width: '100%', padding: '10px 16px', border: 'none', background: 'none', color: '#f85149', cursor: 'pointer', fontSize: 14, textAlign: 'right' }}>خروج</button>
              </div>
            </>
          )}
        </div>
      </header>
      {showSettings && <Settings onClose={() => setShowSettings(false)} user={user} onUserUpdate={(u) => { setUser(u); localStorage.setItem('chat_user', JSON.stringify(u)); }} />}
      {showInviteLink && <InviteLinkModal onClose={() => setShowInviteLink(false)} />}
      {showBlockUser && <BlockUserModal onClose={() => setShowBlockUser(false)} />}
      {showPendingCodes && <PendingCodesModal onClose={() => setShowPendingCodes(false)} />}
      {incomingCall && !activeCall && (
        <CallModal
          isVoice={!incomingCall.isVideo}
          callerName={incomingCall.fromUserName}
          isOutgoing={false}
          onAnswer={() => {
            stopCallRing();
            socket?.emit('answer_call', { conversationId: incomingCall.conversationId, callerUserId: incomingCall.fromUserId });
            setCurrentConvId(incomingCall.conversationId);
            setActiveCall({ conversationId: incomingCall.conversationId, remoteUserId: incomingCall.fromUserId, isInitiator: false, isVideo: !!incomingCall.isVideo });
            setIncomingCall(null);
          }}
          onReject={() => { stopCallRing(); socket?.emit('reject_call', { conversationId: incomingCall.conversationId, callerUserId: incomingCall.fromUserId }); setIncomingCall(null); }}
        />
      )}
      {activeCall && (
        <WebRTCCall
          socket={socket}
          conversationId={activeCall.conversationId}
          remoteUserId={activeCall.remoteUserId}
          isInitiator={activeCall.isInitiator}
          isVideo={activeCall.isVideo}
          onEnd={() => { socket?.emit('hangup_call', { conversationId: activeCall.conversationId }); setActiveCall(null); }}
        />
      )}
      {showMyId && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }} onClick={() => setShowMyId(false)}>
          <div style={{ background: 'var(--surface)', borderRadius: 12, padding: 24, border: '1px solid var(--border)', textAlign: 'center' }} onClick={(e) => e.stopPropagation()}>
            <p style={{ margin: '0 0 12px', fontSize: 14, color: 'var(--text-muted)' }}>رقم المعرف</p>
            <p style={{ margin: '0 0 16px', fontSize: 24, fontWeight: 600, direction: 'ltr' }}>{user.id}</p>
            <button type="button" onClick={() => { navigator.clipboard?.writeText(String(user.id)); setShowMyId(false); }} style={{ padding: '8px 20px', background: 'var(--primary)', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer', fontSize: 14 }}>نسخ</button>
            <button type="button" onClick={() => setShowMyId(false)} style={{ marginRight: 8, padding: '8px 16px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', cursor: 'pointer', fontSize: 14 }}>إغلاق</button>
          </div>
        </div>
      )}
      {typeof window !== 'undefined' && /[?&]debug=1/.test(window.location.search) && (
        <div style={{ padding: '6px 12px', borderBottom: '1px solid var(--border)', fontSize: 12, color: 'var(--text-muted)' }}>
          <span>Build: {BUILD_ID}</span>
          <span style={{ marginRight: 10 }}>• Socket: {socketStatus}</span>
          {socketError && <span style={{ marginRight: 10, color: '#f85149' }}>({socketError})</span>}
          {socketBase && <span style={{ display: 'block', opacity: 0.75, marginTop: 2, direction: 'ltr', textAlign: 'left' }}>base: {socketBase}</span>}
        </div>
      )}
      {error && <p style={{ padding: 6, margin: 0, background: 'rgba(248,81,73,0.15)', color: '#f85149', textAlign: 'center', fontSize: 13 }}>{error}</p>}
      <div className={`app-flex ${currentConvId ? 'room-open' : ''}`} style={{ flex: 1, display: 'flex', overflow: 'hidden', minHeight: 0 }}>
        <div className="chat-list-wrap">
          <ChatList
            conversations={conversations}
            currentConvId={currentConvId}
            onSelect={setCurrentConvId}
            onNewChat={(tab) => { setShowNewChat(true); setNewChatInitialTab(tab || 'direct'); }}
            onStartDirect={handleStartDirect}
            onCreateGroup={handleCreateGroup}
            onCreateBroadcast={handleCreateBroadcast}
            showNewChat={showNewChat}
            onCloseNewChat={() => setShowNewChat(false)}
            onConversationsUpdate={loadConversations}
            currentUserId={user.id}
            storiesFeed={storiesFeed}
            onOpenStoryCreate={() => setShowStoryCreate(true)}
            onStoriesRefresh={loadStories}
            broadcastLists={broadcastLists}
            onSelectBroadcast={(b) => { setCurrentConvId('broadcast-' + b.id); }}
            newChatInitialTab={newChatInitialTab}
          />
          {showStoryCreate && <StoryCreate onClose={() => setShowStoryCreate(false)} onCreated={loadStories} />}
        </div>
        <div className="chat-room-wrap">
          {isBroadcast && currentBroadcastList ? (
            <BroadcastCompose list={currentBroadcastList} onBack={() => setCurrentConvId(null)} onSent={loadConversations} />
          ) : currentConvId ? (
            <ChatRoom
              conversation={currentConv}
              conversations={conversations}
              socket={socket}
              currentUserId={user.id}
              onBack={() => setCurrentConvId(null)}
              onMembersUpdated={loadConversations}
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
