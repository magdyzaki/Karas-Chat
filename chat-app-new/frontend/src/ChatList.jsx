import { useState, useEffect } from 'react';
import * as api from './api';

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
  const { conversations, currentConvId, onSelect, onNewChat, onStartDirect, onCreateGroup, showNewChat, onCloseNewChat } = props;
  const [searchPhones, setSearchPhones] = useState('');
  const [users, setUsers] = useState([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState('');
  const [tab, setTab] = useState('direct');
  const [groupName, setGroupName] = useState('');
  const [selectedForGroup, setSelectedForGroup] = useState([]);
  const [importing, setImporting] = useState(false);

  useEffect(() => {
    if (showNewChat) {
      setUsers([]);
      setSearchPhones('');
      setSearchError('');
      setTab('direct');
      setGroupName('');
      setSelectedForGroup([]);
    }
  }, [showNewChat]);

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
        <div style={styles.header}>
          <span style={{ fontWeight: 600 }}>المحادثات</span>
          <button type="button" style={styles.newBtn} onClick={onNewChat}>+ محادثة جديدة</button>
        </div>
        <div style={{ flex: 1, overflow: 'auto' }}>
          {conversations.map((c) => (
            <div
              key={c.id}
              className={currentConvId === c.id ? 'chat-item chat-item-active' : 'chat-item'}
              onClick={() => onSelect(c.id)}
              style={{ ...styles.item, ...(currentConvId === c.id ? styles.itemActive : {}) }}
            >
              <div style={{ fontWeight: 500 }}>{c.label || 'محادثة'}</div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{c.type === 'group' ? 'مجموعة' : 'فردي'}</div>
            </div>
          ))}
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

            <button type="button" onClick={onCloseNewChat} style={{ marginTop: 12, padding: '8px 16px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', cursor: 'pointer' }}>إلغاء</button>
          </div>
        </div>
      )}
    </>
  );
}
