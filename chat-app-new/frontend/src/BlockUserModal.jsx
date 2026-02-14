import { useState, useEffect } from 'react';
import * as api from './api';

export default function BlockUserModal({ onClose }) {
  const [users, setUsers] = useState([]);
  const [blocked, setBlocked] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([api.getAdminUsers(), api.getBlockedUsers()]).then(([all, bl]) => {
      setUsers(all || []);
      setBlocked(bl || []);
    }).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, []);

  const handleBlock = async (id) => {
    try {
      await api.blockUser(id);
      setBlocked((prev) => [...prev, { id }]);
      setError('');
    } catch (e) {
      setError(e.message);
    }
  };

  const handleUnblock = async (id) => {
    try {
      await api.unblockUser(id);
      setBlocked((prev) => prev.filter((x) => (x?.id || x) !== id));
      setError('');
    } catch (e) {
      setError(e.message);
    }
  };

  const blockedSet = new Set((blocked || []).map((u) => (typeof u === 'object' ? u.id : u)));

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: 16 }} onClick={onClose}>
      <div style={{ background: 'var(--surface)', borderRadius: 16, padding: 24, maxWidth: 400, width: '100%', maxHeight: '80vh', overflow: 'auto', border: '1px solid var(--border)' }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <h2 style={{ margin: 0, fontSize: 20 }}>إيقاف / إلغاء إيقاف مستخدم</h2>
          <button type="button" onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 24, cursor: 'pointer', color: 'var(--text)' }}>×</button>
        </div>
        {error && <p style={{ fontSize: 13, color: '#f85149', marginBottom: 12 }}>{error}</p>}
        {loading ? (
          <p style={{ color: 'var(--text-muted)' }}>جاري التحميل...</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {users.map((u) => {
              const isB = blockedSet.has(u.id) || blockedSet.has(Number(u.id));
              return (
                <div key={u.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 12, background: 'var(--bg)', borderRadius: 8, border: '1px solid var(--border)' }}>
                  <div>
                    <div style={{ fontWeight: 500 }}>{u.name || u.email || u.phone || '—'}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>معرف: {u.id}</div>
                  </div>
                  <button
                    type="button"
                    onClick={() => (isB ? handleUnblock(u.id) : handleBlock(u.id))}
                    style={{ padding: '6px 12px', borderRadius: 6, border: 'none', background: isB ? 'var(--primary)' : 'rgba(248,81,73,0.3)', color: isB ? '#fff' : '#f85149', cursor: 'pointer', fontSize: 12 }}
                  >{isB ? 'إلغاء الإيقاف' : 'إيقاف'}</button>
                </div>
              );
            })}
            {users.length === 0 && <p style={{ color: 'var(--text-muted)' }}>لا يوجد مستخدمون آخرون</p>}
          </div>
        )}
      </div>
    </div>
  );
}
