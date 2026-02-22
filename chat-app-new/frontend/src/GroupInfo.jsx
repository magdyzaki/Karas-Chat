import { useState } from 'react';
import * as api from './api';

function extractPhones(input) {
  const str = String(input || '').replace(/[,،\s]+/g, ' ');
  return str.trim().split(/\s+/).filter(Boolean);
}

const DISAPPEARING_OPTS = [
  { value: null, label: 'معطّل' },
  { value: 86400, label: '24 ساعة' },
  { value: 604800, label: '7 أيام' },
  { value: 7776000, label: '90 يوماً' }
];

export default function GroupInfo({ conversation, currentUserId, onClose, onMembersUpdated, onRemoveMember, disappearingAfter, onDisappearingChange }) {
  const isCreator = Number(conversation?.created_by) === Number(currentUserId);
  const memberIds = conversation?.memberIds || [];
  const memberDetails = conversation?.memberDetails || [];
  const [searchPhones, setSearchPhones] = useState('');
  const [searchResult, setSearchResult] = useState([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState('');
  const [adding, setAdding] = useState(false);

  const members = memberIds.map((id) => {
    const d = memberDetails.find((m) => Number(m.id) === Number(id));
    return { id, name: d?.name || d?.email || d?.phone || 'عضو', avatar_url: d?.avatar_url };
  });

  const doSearch = async () => {
    const phones = extractPhones(searchPhones);
    if (!phones.length) {
      setSearchError('أدخل رقم هاتف واحد أو أكثر');
      return;
    }
    setSearching(true);
    setSearchError('');
    try {
      const list = await api.checkContacts(phones);
      const alreadyIn = new Set(memberIds.map(Number));
      setSearchResult(list.filter((u) => !alreadyIn.has(Number(u.id))));
      if (list.filter((u) => !alreadyIn.has(Number(u.id))).length === 0 && list.length > 0) setSearchError('جميعهم أعضاء بالفعل');
    } catch (e) {
      setSearchError(e.message || 'فشل البحث');
    } finally {
      setSearching(false);
    }
  };

  const handleAddMember = async (userId) => {
    if (!conversation?.id) return;
    setAdding(true);
    try {
      await api.addMemberToGroup(conversation.id, userId);
      const updated = await api.getConversation(conversation.id);
      onMembersUpdated?.(updated);
      setSearchResult((prev) => prev.filter((u) => u.id !== userId));
    } catch (_) {}
    setAdding(false);
  };

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50, padding: 16 }} onClick={onClose}>
      <div style={{ background: 'var(--surface)', borderRadius: 16, padding: 24, maxWidth: 400, width: '100%', maxHeight: '90vh', overflow: 'auto', border: '1px solid var(--border)' }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <h2 style={{ margin: 0, fontSize: 20 }}>{conversation?.name || 'المجموعة'}</h2>
          <button type="button" onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 24, cursor: 'pointer', color: 'var(--text)' }}>×</button>
        </div>
        {onDisappearingChange && (
          <div style={{ marginBottom: 16 }}>
            <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 8 }}>رسائل مؤقتة</p>
            <select value={disappearingAfter ?? ''} onChange={(e) => { const v = e.target.value === '' ? null : Number(e.target.value); onDisappearingChange(v); }} style={{ padding: '8px 12px', border: '1px solid var(--border)', borderRadius: 8, background: 'var(--bg)', color: 'var(--text)' }}>
              {DISAPPEARING_OPTS.map((o) => (
                <option key={String(o.value)} value={o.value ?? ''}>{o.label}</option>
              ))}
            </select>
          </div>
        )}
        <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 16 }}>الأعضاء ({members.length})</p>
        {members.map((m) => (
          <div key={m.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
            {m.avatar_url ? <img src={api.uploadsUrl(m.avatar_url)} alt="" style={{ width: 40, height: 40, borderRadius: '50%', objectFit: 'cover' }} /> : <span style={{ width: 40, height: 40, borderRadius: '50%', background: 'var(--bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>👤</span>}
            <div style={{ flex: 1 }}>
              <div>{m.name}</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>معرف: {m.id}</div>
            </div>
            {isCreator && Number(m.id) !== Number(currentUserId) && (
              <button type="button" onClick={async () => { await onRemoveMember?.(conversation.id, m.id); onClose(); }} style={{ padding: '6px 12px', background: 'rgba(248,81,73,0.2)', border: 'none', borderRadius: 6, color: '#f85149', cursor: 'pointer', fontSize: 12 }}>طرد</button>
            )}
          </div>
        ))}
        {isCreator && (
          <>
            <div style={{ borderTop: '1px solid var(--border)', marginTop: 16, paddingTop: 16 }}>
              <h3 style={{ fontSize: 14, marginBottom: 12 }}>إضافة عضو</h3>
              <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
                <input
                  type="text"
                  placeholder="رقم الهاتف"
                  value={searchPhones}
                  onChange={(e) => { setSearchPhones(e.target.value); setSearchError(''); }}
                  style={{ flex: 1, padding: 10, border: '1px solid var(--border)', borderRadius: 8, background: 'var(--bg)', color: 'var(--text)' }}
                />
                <button type="button" onClick={doSearch} disabled={searching} style={{ padding: '10px 16px', background: 'var(--primary)', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer' }}>{searching ? '...' : 'بحث'}</button>
              </div>
              {searchError && <p style={{ fontSize: 12, color: '#f85149', marginBottom: 8 }}>{searchError}</p>}
              {searchResult.map((u) => (
                <div key={u.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '8px 0' }}>
                  <span style={{ flex: 1 }}>{u.name || u.phone || u.email} (معرف: {u.id})</span>
                  <button type="button" onClick={() => handleAddMember(u.id)} disabled={adding} style={{ padding: '6px 12px', background: 'var(--primary)', border: 'none', borderRadius: 6, color: '#fff', cursor: 'pointer', fontSize: 12 }}>إضافة</button>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
