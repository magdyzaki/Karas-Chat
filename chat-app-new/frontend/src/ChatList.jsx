import { useState, useEffect } from 'react';
import * as api from './api';
import Stories from './Stories';

const styles = {
  list: { width: 280, minWidth: 280, borderLeft: '1px solid var(--border)', display: 'flex', flexDirection: 'column', overflow: 'hidden' },
  header: { padding: 12, borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  newBtn: { padding: '8px 12px', border: 'none', borderRadius: 8, background: 'var(--primary)', color: '#fff', cursor: 'pointer', fontSize: 14 },
  item: { padding: '12px 16px', borderBottom: '1px solid var(--border)', cursor: 'pointer', background: 'transparent' },
  itemActive: { background: 'var(--surface)' },
  modal: { position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 10, padding: 16 },
  modalBox: { background: 'var(--surface)', borderRadius: 12, padding: 20, maxWidth: 400, width: '100%', maxHeight: '80vh', overflow: 'auto' },
  modalTitle: { marginTop: 0 },
  userRow: { padding: '10px 0', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  groupInput: { width: '100%', padding: 10, marginBottom: 12, border: '1px solid var(--border)', borderRadius: 8, background: 'var(--bg)', color: 'var(--text)' },
  searchRow: { display: 'flex', gap: 8, marginBottom: 12 },
  searchInput: { flex: 1, padding: 10, border: '1px solid var(--border)', borderRadius: 8, background: 'var(--bg)', color: 'var(--text)' },
  hint: { fontSize: 12, color: 'var(--text-muted)', marginBottom: 12 }
};

function extractPhones(input) {
  const str = String(input || '').replace(/[,،\s]+/g, ' ');
  return str.trim().split(/\s+/).filter(Boolean);
}

export default function ChatList(props) {
  const { conversations, currentConvId, onSelect, onNewChat, onStartDirect, onCreateGroup, onCreateBroadcast, showNewChat, onCloseNewChat, onConversationsUpdate, storiesFeed = [], onOpenStoryCreate, onStoriesRefresh, broadcastLists = [], onSelectBroadcast, newChatInitialTab = 'direct' } = props;
  const [searchPhones, setSearchPhones] = useState('');
  const [listFilter, setListFilter] = useState('active'); // 'active' | 'archived' | 'broadcast'
  const [menuConvId, setMenuConvId] = useState(null);
  const [searchConvs, setSearchConvs] = useState('');
  const [users, setUsers] = useState([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState('');
  const [tab, setTab] = useState('direct');
  const [groupName, setGroupName] = useState('');
  const [selectedForGroup, setSelectedForGroup] = useState([]);
  const [importing, setImporting] = useState(false);

  useEffect(() => setMenuConvId(null), [listFilter]);

  useEffect(() => {
    const close = (e) => {
      if (menuConvId && !e.target.closest('.chat-item')) setMenuConvId(null);
    };
    document.addEventListener('click', close);
    return () => document.removeEventListener('click', close);
  }, [menuConvId]);

  useEffect(() => {
    if (showNewChat) {
      setUsers([]);
      setSearchPhones('');
      setSearchError('');
      setTab(newChatInitialTab || 'direct');
      setGroupName('');
      setSelectedForGroup([]);
    }
  }, [showNewChat, newChatInitialTab]);

  const doSearch = async () => {
    const phones = extractPhones(searchPhones);
    if (!phones.length) {
      setSearchError('أدخل رقم هاتف واحد أو أكثر (أرقام منفصلة بمسافة)');
      return;
    }
    setSearching(true);
    setSearchError('');
    try {
      const list = await api.checkContacts(phones);
      setUsers(list);
      if (!list.length) setSearchError('لا يوجد مستخدمون مسجّلون بهذه الأرقام في Karas شات');
    } catch (e) {
      setSearchError(e.message || 'فشل البحث');
    } finally {
      setSearching(false);
    }
  };

  const doImportContacts = async () => {
    if (!navigator.contacts || !navigator.contacts.select) {
      setSearchError('المتصفح لا يدعم استيراد جهات الاتصال. جرّب البحث يدوياً برقم الهاتف.');
      return;
    }
    setImporting(true);
    setSearchError('');
    try {
      const contacts = await navigator.contacts.select(['tel'], { multiple: true });
      const phones = [];
      for (const c of contacts) {
        for (const t of c.tel || []) {
          const n = String(t).replace(/\D/g, '');
          if (n.length >= 10) phones.push(n);
        }
      }
      if (!phones.length) {
        setSearchError('لم يتم العثور على أرقام في جهات الاتصال');
      } else {
        const list = await api.checkContacts([...new Set(phones)]);
        setUsers(list);
        if (!list.length) setSearchError('لا يوجد من جهات اتصالك مسجّل في Karas شات');
      }
    } catch (e) {
      setSearchError(e.message || 'فشل الاستيراد');
    } finally {
      setImporting(false);
    }
  };

  const addToGroup = (u) => {
    if (!selectedForGroup.some((x) => x.id === u.id)) setSelectedForGroup((prev) => [...prev, u]);
  };

  const removeFromGroup = (id) => {
    setSelectedForGroup((prev) => prev.filter((x) => x.id !== id));
  };

  return (
    <>
      <div className="chat-list" style={styles.list}>
        {onOpenStoryCreate && (
          <Stories feed={storiesFeed} currentUserId={props.currentUserId} onCreateStory={onOpenStoryCreate} onRefresh={onStoriesRefresh} />
        )}
        <div style={styles.header}>
          <span style={{ fontWeight: 600 }}>المحادثات</span>
          <button type="button" style={styles.newBtn} onClick={onNewChat}>+ محادثة جديدة</button>
        </div>
        <div style={{ display: 'flex', gap: 4, padding: '8px 12px', borderBottom: '1px solid var(--border)' }}>
          <button type="button" onClick={() => setListFilter('active')} style={{ flex: 1, padding: '6px 12px', border: 'none', borderRadius: 8, background: listFilter === 'active' ? 'var(--primary)' : 'var(--surface)', color: listFilter === 'active' ? '#fff' : 'var(--text)', cursor: 'pointer', fontSize: 13 }}>المحادثات</button>
          <button type="button" onClick={() => setListFilter('archived')} style={{ flex: 1, padding: '6px 12px', border: 'none', borderRadius: 8, background: listFilter === 'archived' ? 'var(--primary)' : 'var(--surface)', color: listFilter === 'archived' ? '#fff' : 'var(--text)', cursor: 'pointer', fontSize: 13 }}>الأرشيف</button>
          <button type="button" onClick={() => setListFilter('broadcast')} style={{ flex: 1, padding: '6px 12px', border: 'none', borderRadius: 8, background: listFilter === 'broadcast' ? 'var(--primary)' : 'var(--surface)', color: listFilter === 'broadcast' ? '#fff' : 'var(--text)', cursor: 'pointer', fontSize: 13 }}>📢 البث</button>
        </div>
        {listFilter !== 'broadcast' && (
          <div style={{ padding: '8px 12px', borderBottom: '1px solid var(--border)' }}>
            <input type="text" placeholder="بحث في المحادثات..." value={searchConvs} onChange={(e) => setSearchConvs(e.target.value)} style={{ width: '100%', padding: '8px 12px', border: '1px solid var(--border)', borderRadius: 8, background: 'var(--bg)', color: 'var(--text)', fontSize: 14, textAlign: 'right' }} />
          </div>
        )}
        <div style={{ flex: 1, overflow: 'auto' }}>
          {listFilter === 'broadcast' ? (
            <>
              <div style={{ padding: '8px 12px', borderBottom: '1px solid var(--border)' }}>
                <button type="button" onClick={() => onNewChat?.('broadcast')} style={{ width: '100%', padding: '10px', background: 'var(--primary)', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer', fontSize: 14 }}>+ قائمة بث جديدة</button>
              </div>
              {broadcastLists.map((b) => {
                const bid = 'broadcast-' + b.id;
                const isActive = currentConvId === bid;
                return (
                  <div key={b.id} onClick={() => onSelectBroadcast?.(b)} style={{ ...styles.item, ...(isActive ? styles.itemActive : {}), display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}>
                    <div>
                      <div style={{ fontWeight: 500 }}>📢 {b.name || 'قائمة بث'}</div>
                      <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{(b.recipients || []).length} جهة اتصال</div>
                    </div>
                  </div>
                );
              })}
              {broadcastLists.length === 0 && <p style={{ padding: 24, color: 'var(--text-muted)', textAlign: 'center', fontSize: 13 }}>لا توجد قوائم بث. أنشئ قائمة جديدة.</p>}
            </>
          ) : conversations
            .filter((c) => (listFilter === 'archived' ? c.archived : !c.archived))
            .filter((c) => {
              const q = (searchConvs || '').trim().toLowerCase();
              if (!q) return true;
              const label = (c.label || '').toLowerCase();
              const members = (c.memberDetails || []).map((m) => String(m.id || '') + (m.name || '') + (m.phone || '') + (m.email || '')).join(' ').toLowerCase();
              return label.includes(q) || members.includes(q);
            })
            .map((c) => (
            <div
              key={c.id}
              className={currentConvId === c.id ? 'chat-item chat-item-active' : 'chat-item'}
              onClick={() => { setMenuConvId(null); onSelect(c.id); }}
              style={{ ...styles.item, ...(currentConvId === c.id ? styles.itemActive : {}), display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, position: 'relative' }}
            >
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 500, color: 'var(--list-name-color, var(--text))', display: 'flex', alignItems: 'center', gap: 6 }}>
                  {c.muted && <span style={{ fontSize: 14 }} title="مكتوم">🔇</span>}
                  {c.label || 'محادثة'}
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                  {c.type === 'group' ? `مجموعة · معرفات: ${(c.memberDetails || []).map((m) => m.id).filter(Boolean).join('، ')}` : (c.memberDetails || []).length ? `معرف: ${c.memberDetails[0]?.id || '—'}` : 'فردي'}
                </div>
              </div>
              <button type="button" onClick={(e) => { e.stopPropagation(); setMenuConvId(menuConvId === c.id ? null : c.id); }} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: 4, fontSize: 16 }} title="المزيد">⋮</button>
              {menuConvId === c.id && (
                <div style={{ position: 'absolute', left: 0, top: '100%', marginTop: 4, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, boxShadow: '0 4px 12px rgba(0,0,0,0.2)', zIndex: 20, minWidth: 160, padding: 4 }} onClick={(e) => e.stopPropagation()}>
                  {c.muted ? (
                    <button type="button" onClick={async () => { try { await api.unmuteConversation(c.id); onConversationsUpdate?.(); setMenuConvId(null); } catch (_) {} }} style={{ display: 'block', width: '100%', padding: '8px 12px', border: 'none', background: 'none', color: 'var(--text)', cursor: 'pointer', fontSize: 13, textAlign: 'right' }}>إلغاء الكتم</button>
                  ) : (
                    <button type="button" onClick={async () => { try { await api.muteConversation(c.id); onConversationsUpdate?.(); setMenuConvId(null); } catch (_) {} }} style={{ display: 'block', width: '100%', padding: '8px 12px', border: 'none', background: 'none', color: 'var(--text)', cursor: 'pointer', fontSize: 13, textAlign: 'right' }}>كتم المحادثة</button>
                  )}
                  {c.archived ? (
                    <button type="button" onClick={async () => { try { await api.unarchiveConversation(c.id); onConversationsUpdate?.(); setMenuConvId(null); } catch (_) {} }} style={{ display: 'block', width: '100%', padding: '8px 12px', border: 'none', background: 'none', color: 'var(--text)', cursor: 'pointer', fontSize: 13, textAlign: 'right' }}>إلغاء الأرشفة</button>
                  ) : (
                    <button type="button" onClick={async () => { try { await api.archiveConversation(c.id); onConversationsUpdate?.(); setMenuConvId(null); } catch (_) {} }} style={{ display: 'block', width: '100%', padding: '8px 12px', border: 'none', background: 'none', color: 'var(--text)', cursor: 'pointer', fontSize: 13, textAlign: 'right' }}>أرشفة</button>
                  )}
                  <div style={{ padding: '6px 12px', fontSize: 12, color: 'var(--text-muted)' }}>رسائل مؤقتة:</div>
                  <select value={c.disappearing_after ?? ''} onChange={async (e) => { const v = e.target.value === '' ? null : Number(e.target.value); try { await api.setDisappearing(c.id, v); onConversationsUpdate?.(); setMenuConvId(null); } catch (_) {} }} style={{ margin: '0 8px 8px', padding: '6px 8px', width: 'calc(100% - 16px)', border: '1px solid var(--border)', borderRadius: 6, background: 'var(--bg)', color: 'var(--text)', fontSize: 12 }}>
                    <option value="">معطّل</option>
                    <option value={86400}>24 ساعة</option>
                    <option value={604800}>7 أيام</option>
                    <option value={7776000}>90 يوماً</option>
                  </select>
                </div>
              )}
            </div>
          ))
          }
        </div>
      </div>

      {showNewChat && (
        <div style={styles.modal} onClick={onCloseNewChat}>
          <div style={styles.modalBox} onClick={(e) => e.stopPropagation()}>
            <h2 style={styles.modalTitle}>محادثة جديدة</h2>
            <p style={styles.hint}>ابحث برقم الهاتف أو استورد من جهات الاتصال — تظهر فقط من لديهم التطبيق</p>
            <div style={{ marginBottom: 12 }}>
              <button type="button" onClick={() => setTab('direct')} style={{ marginLeft: 8, padding: '6px 12px', background: tab === 'direct' ? 'var(--primary)' : 'var(--surface)', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer' }}>فردي</button>
              <button type="button" onClick={() => setTab('group')} style={{ padding: '6px 12px', background: tab === 'group' ? 'var(--primary)' : 'var(--surface)', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer' }}>مجموعة</button>
              <button type="button" onClick={() => setTab('broadcast')} style={{ padding: '6px 12px', background: tab === 'broadcast' ? 'var(--primary)' : 'var(--surface)', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer' }}>📢 قائمة بث</button>
            </div>

            <div style={styles.searchRow}>
              <input
                type="text"
                placeholder="أدخل رقم الهاتف (مثال: 01234567890)"
                value={searchPhones}
                onChange={(e) => { setSearchPhones(e.target.value); setSearchError(''); }}
                style={styles.searchInput}
              />
              <button type="button" style={styles.newBtn} onClick={doSearch} disabled={searching}>{searching ? '...' : 'بحث'}</button>
            </div>
            {typeof navigator !== 'undefined' && navigator.contacts?.select && (
              <button type="button" style={{ ...styles.newBtn, marginBottom: 12, background: 'var(--surface)', color: 'var(--text)', border: '1px solid var(--border)' }} onClick={doImportContacts} disabled={importing}>
                {importing ? 'جاري الاستيراد...' : '📇 استيراد من جهات الاتصال'}
              </button>
            )}
            {searchError && <p style={{ fontSize: 13, color: '#f85149', marginBottom: 12 }}>{searchError}</p>}

            {tab === 'direct' && (
              <div>
                {users.map((u) => (
                  <div key={u.id} style={styles.userRow}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      {u.avatar_url ? <img src={api.uploadsUrl(u.avatar_url)} alt="" style={{ width: 36, height: 36, borderRadius: '50%', objectFit: 'cover' }} /> : <span style={{ width: 36, height: 36, borderRadius: '50%', background: 'var(--bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16 }}>👤</span>}
                      <div>
                        <div>{u.name || u.email || u.phone || '—'}</div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>معرف: {u.id}</div>
                      </div>
                    </div>
                    <button type="button" style={styles.newBtn} onClick={() => onStartDirect(u.id)}>محادثة</button>
                  </div>
                ))}
                {users.length === 0 && !searching && !searchError && <p style={{ color: 'var(--text-muted)' }}>ابحث برقم هاتف أو استورد جهات الاتصال</p>}
              </div>
            )}

            {tab === 'group' && (
              <div>
                <input type="text" placeholder="اسم المجموعة" value={groupName} onChange={(e) => setGroupName(e.target.value)} style={styles.groupInput} />
                {selectedForGroup.length > 0 && (
                  <div style={{ marginBottom: 12 }}>
                    <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>الأعضاء المختارون:</p>
                    {selectedForGroup.map((u) => (
                      <div key={u.id} style={{ ...styles.userRow, padding: '6px 0' }}>
                        <span>{u.name || u.phone || '—'} <span style={{ fontSize: 10, opacity: 0.8 }}>(معرف: {u.id})</span></span>
                        <button type="button" style={{ ...styles.newBtn, fontSize: 12, background: 'var(--surface)', color: 'var(--text)', border: '1px solid var(--border)' }} onClick={() => removeFromGroup(u.id)}>إزالة</button>
                      </div>
                    ))}
                  </div>
                )}
                {users.map((u) => (
                  <div key={u.id} style={styles.userRow}>
                    <span>{u.name || u.email || u.phone || '—'} <span style={{ fontSize: 10, opacity: 0.8 }}>(معرف: {u.id})</span></span>
                    <button type="button" style={styles.newBtn} onClick={() => addToGroup(u)} disabled={selectedForGroup.some((x) => x.id === u.id)}>
                      {selectedForGroup.some((x) => x.id === u.id) ? '✓ مضاف' : 'أضف'}
                    </button>
                  </div>
                ))}
                <button type="button" style={{ ...styles.newBtn, marginTop: 12 }} onClick={() => { if (groupName.trim()) onCreateGroup(groupName.trim(), selectedForGroup.map((u) => u.id)); }} disabled={!groupName.trim()}>إنشاء المجموعة</button>
                <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 8 }}>ابحث عن أعضاء أو استورد جهات الاتصال، ثم أضفهم للمجموعة.</p>
              </div>
            )}

            {tab === 'broadcast' && (
              <div>
                <input type="text" placeholder="اسم القائمة (اختياري)" value={groupName} onChange={(e) => setGroupName(e.target.value)} style={styles.groupInput} />
                {selectedForGroup.length > 0 && (
                  <div style={{ marginBottom: 12 }}>
                    <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>المستلمون:</p>
                    {selectedForGroup.map((u) => (
                      <div key={u.id} style={{ ...styles.userRow, padding: '6px 0' }}>
                        <span>{u.name || u.phone || '—'} <span style={{ fontSize: 10, opacity: 0.8 }}>(معرف: {u.id})</span></span>
                        <button type="button" style={{ ...styles.newBtn, fontSize: 12, background: 'var(--surface)', color: 'var(--text)', border: '1px solid var(--border)' }} onClick={() => removeFromGroup(u.id)}>إزالة</button>
                      </div>
                    ))}
                  </div>
                )}
                {users.map((u) => (
                  <div key={u.id} style={styles.userRow}>
                    <span>{u.name || u.email || u.phone || '—'} <span style={{ fontSize: 10, opacity: 0.8 }}>(معرف: {u.id})</span></span>
                    <button type="button" style={styles.newBtn} onClick={() => addToGroup(u)} disabled={selectedForGroup.some((x) => x.id === u.id) || Number(u.id) === Number(props.currentUserId)}>
                      {selectedForGroup.some((x) => x.id === u.id) ? '✓ مضاف' : 'أضف'}
                    </button>
                  </div>
                ))}
                <button type="button" style={{ ...styles.newBtn, marginTop: 12 }} onClick={() => { if (selectedForGroup.length) onCreateBroadcast(groupName.trim() || 'قائمة بث', selectedForGroup.map((u) => u.id)); }} disabled={selectedForGroup.length === 0}>إنشاء قائمة البث</button>
                <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 8 }}>ابحث عن أعضاء، أضفهم للقائمة، ثم أرسل رسالة واحدة للجميع.</p>
              </div>
            )}

            <button type="button" onClick={onCloseNewChat} style={{ marginTop: 12, padding: '8px 16px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', cursor: 'pointer' }}>إلغاء</button>
          </div>
        </div>
      )}
    </>
  );
}
