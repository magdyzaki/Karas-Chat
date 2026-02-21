import { useState, useEffect } from 'react';
import * as api from './api';

const s = {
  list: { width: 260, minWidth: 260, borderLeft: '1px solid #30363d', display: 'flex', flexDirection: 'column', overflow: 'hidden' },
  header: { padding: 12, borderBottom: '1px solid #30363d', display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  btn: { padding: '8px 12px', border: 'none', borderRadius: 8, background: '#238636', color: '#fff', cursor: 'pointer', fontSize: 14 },
  item: { padding: '12px 16px', borderBottom: '1px solid #30363d', cursor: 'pointer', background: 'transparent', color: '#fff' },
  itemActive: { background: '#21262d' },
  modal: { position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 10, padding: 16 },
  box: { background: '#161b22', borderRadius: 12, padding: 20, maxWidth: 400, width: '100%', maxHeight: '80vh', overflow: 'auto', border: '1px solid #30363d' },
  input: { width: '100%', padding: 10, marginBottom: 12, border: '1px solid #30363d', borderRadius: 8, background: '#0d1117', color: '#fff', boxSizing: 'border-box' },
  row: { padding: '10px 0', borderBottom: '1px solid #30363d', display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#fff' }
};

function extractPhones(t) {
  return String(t || '').replace(/[,،\s]+/g, ' ').trim().split(/\s+/).filter(Boolean);
}

export default function ChatList({ conversations, currentConvId, onSelect, onNewChat, onStartDirect, onCreateGroup, showNewChat, onCloseNewChat, currentUserId }) {
  const [users, setUsers] = useState([]);
  const [tab, setTab] = useState('direct');
  const [groupName, setGroupName] = useState('');
  const [selectedIds, setSelectedIds] = useState([]);
  const [searchPhones, setSearchPhones] = useState('');
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState('');

  useEffect(() => {
    if (showNewChat) {
      setTab('direct');
      setGroupName('');
      setSelectedIds([]);
      setUsers([]);
      setSearchPhones('');
    }
  }, [showNewChat]);

  const doSearch = async () => {
    const phones = extractPhones(searchPhones);
    if (!phones.length) { setSearchError('أدخل رقم هاتف'); return; }
    setSearching(true);
    setSearchError('');
    try {
      const list = await api.checkContacts(phones);
      setUsers(list);
      if (!list.length) setSearchError('لا يوجد مستخدمون بهذه الأرقام');
    } catch (e) {
      setSearchError(e.message || 'فشل');
    } finally {
      setSearching(false);
    }
  };

  const toggleUser = (id) => {
    setSelectedIds((p) => (p.includes(id) ? p.filter((x) => x !== id) : [...p, id]));
  };

  return (
    <>
      <div style={s.list}>
        <div style={s.header}>
          <span style={{ fontWeight: 600, color: '#fff' }}>المحادثات</span>
          <button type="button" style={s.btn} onClick={onNewChat}>+ محادثة جديدة</button>
        </div>
        <div style={{ flex: 1, overflow: 'auto' }}>
          {conversations.map((c) => (
            <div key={c.id} onClick={() => onSelect(c.id)} style={{ ...s.item, ...(currentConvId === c.id ? s.itemActive : {}) }}>
              <div style={{ fontWeight: 500 }}>{c.label || 'محادثة'}</div>
              <div style={{ fontSize: 12, color: '#8b949e' }}>{c.type === 'group' ? 'مجموعة' : 'فردي'}</div>
            </div>
          ))}
        </div>
      </div>

      {showNewChat && (
        <div style={s.modal} onClick={onCloseNewChat}>
          <div style={s.box} onClick={(e) => e.stopPropagation()}>
            <h2 style={{ marginTop: 0, color: '#fff' }}>محادثة جديدة</h2>
            <div style={{ marginBottom: 12 }}>
              <button type="button" onClick={() => setTab('direct')} style={{ marginLeft: 8, padding: '6px 12px', background: tab === 'direct' ? '#238636' : '#21262d', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer' }}>فردي</button>
              <button type="button" onClick={() => setTab('group')} style={{ padding: '6px 12px', background: tab === 'group' ? '#238636' : '#21262d', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer' }}>مجموعة</button>
            </div>
            <div style={{ marginBottom: 12, display: 'flex', gap: 8 }}>
              <input type="text" placeholder="رقم الهاتف (01234567890)" value={searchPhones} onChange={(e) => { setSearchPhones(e.target.value); setSearchError(''); }} style={{ ...s.input, flex: 1 }} />
              <button type="button" style={s.btn} onClick={doSearch} disabled={searching}>{searching ? '...' : 'بحث'}</button>
            </div>
            {searchError && <p style={{ color: '#f85149', fontSize: 13, marginBottom: 12 }}>{searchError}</p>}

            {tab === 'direct' && (
              <div>
                {users.map((u) => (
                  <div key={u.id} style={s.row}>
                    <span>{u.name || u.email || u.phone}</span>
                    <button type="button" style={s.btn} onClick={() => onStartDirect(u.id)}>محادثة</button>
                  </div>
                ))}
                {users.length === 0 && !searching && <p style={{ color: '#8b949e' }}>ابحث برقم الهاتف</p>}
              </div>
            )}

            {tab === 'group' && (
              <div>
                <input type="text" placeholder="اسم المجموعة" value={groupName} onChange={(e) => setGroupName(e.target.value)} style={s.input} />
                {users.map((u) => (
                  <div key={u.id} style={s.row}>
                    <label style={{ cursor: 'pointer' }}>
                      <input type="checkbox" checked={selectedIds.includes(u.id)} onChange={() => toggleUser(u.id)} style={{ marginLeft: 8 }} />
                      {u.name || u.email || u.phone}
                    </label>
                  </div>
                ))}
                <button type="button" style={{ ...s.btn, marginTop: 12 }} onClick={() => onCreateGroup(groupName.trim(), selectedIds)} disabled={!groupName.trim()}>إنشاء المجموعة</button>
              </div>
            )}

            <button type="button" onClick={onCloseNewChat} style={{ marginTop: 12, padding: '8px 16px', background: '#21262d', border: '1px solid #30363d', borderRadius: 8, color: '#fff', cursor: 'pointer' }}>إلغاء</button>
          </div>
        </div>
      )}
    </>
  );
}
