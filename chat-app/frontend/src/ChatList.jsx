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
  checkbox: { marginLeft: 8 }
};

export default function ChatList({ conversations, currentConvId, onSelect, onNewChat, onStartDirect, onCreateGroup, showNewChat, onCloseNewChat, currentUserId }) {
  const [users, setUsers] = useState([]);
  const [tab, setTab] = useState('direct'); // 'direct' | 'group'
  const [groupName, setGroupName] = useState('');
  const [selectedIds, setSelectedIds] = useState([]);

  useEffect(() => {
    if (showNewChat) {
      api.getUsers().then(setUsers).catch(() => setUsers([]));
      setTab('direct');
      setGroupName('');
      setSelectedIds([]);
    }
  }, [showNewChat]);

  const toggleUser = (id) => {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  const handleStartDirect = (otherUserId) => {
    onStartDirect(otherUserId);
  };

  const handleCreateGroup = () => {
    if (!groupName.trim()) return;
    onCreateGroup(groupName.trim(), selectedIds);
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
            <div style={{ marginBottom: 12 }}>
              <button type="button" onClick={() => setTab('direct')} style={{ marginLeft: 8, padding: '6px 12px', background: tab === 'direct' ? 'var(--primary)' : 'var(--surface)', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer' }}>فردي</button>
              <button type="button" onClick={() => setTab('group')} style={{ padding: '6px 12px', background: tab === 'group' ? 'var(--primary)' : 'var(--surface)', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer' }}>مجموعة</button>
            </div>
            {tab === 'direct' && (
              <div>
                {users.map((u) => (
                  <div key={u.id} style={styles.userRow}>
                    <span>{u.name || u.email || u.phone}</span>
                    <button type="button" style={styles.newBtn} onClick={() => handleStartDirect(u.id)}>محادثة</button>
                  </div>
                ))}
                {users.length === 0 && <p style={{ color: 'var(--text-muted)' }}>لا يوجد مستخدمون آخرون</p>}
              </div>
            )}
            {tab === 'group' && (
              <div>
                <input type="text" placeholder="اسم المجموعة" value={groupName} onChange={(e) => setGroupName(e.target.value)} style={styles.groupInput} />
                {users.map((u) => (
                  <div key={u.id} style={styles.userRow}>
                    <label style={{ cursor: 'pointer' }}>
                      <input type="checkbox" checked={selectedIds.includes(u.id)} onChange={() => toggleUser(u.id)} style={styles.checkbox} />
                      {u.name || u.email || u.phone}
                    </label>
                  </div>
                ))}
                <button type="button" style={{ ...styles.newBtn, marginTop: 12 }} onClick={handleCreateGroup} disabled={!groupName.trim()}>إنشاء المجموعة</button>
                <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 8 }}>اختر أعضاء أو اترك القائمة فارغة لتبدأ مجموعة معك فقط.</p>
              </div>
            )}
            <button type="button" onClick={onCloseNewChat} style={{ marginTop: 12, padding: '8px 16px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', cursor: 'pointer' }}>إلغاء</button>
          </div>
        </div>
      )}
    </>
  );
}
