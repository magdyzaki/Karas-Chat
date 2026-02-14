import { useState } from 'react';
import * as api from './api';

const BASE_URL = typeof window !== 'undefined' ? window.location.origin + window.location.pathname : '';

export default function InviteLinkModal({ onClose }) {
  const [loading, setLoading] = useState(false);
  const [link, setLink] = useState('');
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  const handleCreate = async () => {
    setError('');
    setLoading(true);
    try {
      const { token } = await api.createInviteLink();
      const url = `${BASE_URL}?invite=${token}`;
      setLink(url);
    } catch (e) {
      setError(e.message || 'فشل إنشاء الرابط');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (!link) return;
    navigator.clipboard?.writeText(link).then(() => setCopied(true)).catch(() => {});
    setTimeout(() => setCopied(false), 2000);
  };

  const isAndroid = typeof navigator !== 'undefined' && /Android/i.test(navigator.userAgent);
  const isIOS = typeof navigator !== 'undefined' && /iPhone|iPad/i.test(navigator.userAgent);

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: 16 }} onClick={onClose}>
      <div style={{ background: 'var(--surface)', borderRadius: 16, padding: 24, maxWidth: 420, width: '100%', border: '1px solid var(--border)' }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <h2 style={{ margin: 0, fontSize: 20 }}>🔗 رابط الدعوة</h2>
          <button type="button" onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 24, cursor: 'pointer', color: 'var(--text)' }}>×</button>
        </div>
        <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16 }}>أرسل هذا الرابط لشخص ليُضيف التطبيق على الآيفون أو الأندرويد. الرابط يعمل مرة واحدة فقط.</p>
        {error && <p style={{ fontSize: 13, color: '#f85149', marginBottom: 12 }}>{error}</p>}
        {!link ? (
          <button type="button" onClick={handleCreate} disabled={loading} style={{ width: '100%', padding: 12, background: 'var(--primary)', border: 'none', borderRadius: 8, color: '#fff', cursor: loading ? 'wait' : 'pointer', fontSize: 15 }}>{loading ? 'جاري الإنشاء...' : 'إنشاء رابط جديد'}</button>
        ) : (
          <>
            <div style={{ background: 'var(--bg)', padding: 12, borderRadius: 8, marginBottom: 12, wordBreak: 'break-all', fontSize: 13, color: 'var(--text)' }}>{link}</div>
            <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
              <button type="button" onClick={handleCopy} style={{ flex: 1, padding: 10, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', cursor: 'pointer', fontSize: 14 }}>{copied ? '✓ تم النسخ' : '📋 نسخ الرابط'}</button>
              <button type="button" onClick={handleCreate} disabled={loading} style={{ flex: 1, padding: 10, background: 'var(--primary)', border: 'none', borderRadius: 8, color: '#fff', cursor: loading ? 'wait' : 'pointer', fontSize: 14 }}>{loading ? '...' : 'إنشاء رابط جديد'}</button>
            </div>
            <div style={{ marginTop: 20, padding: 16, background: 'var(--bg)', borderRadius: 8 }}>
              <p style={{ margin: '0 0 8px', fontSize: 13, fontWeight: 600 }}>إضافة للتطبيق:</p>
              {isAndroid ? (
                <p style={{ margin: 0, fontSize: 12, color: 'var(--text-muted)' }}>Chrome → القائمة ⋮ → إضافة إلى الشاشة الرئيسية</p>
              ) : isIOS ? (
                <p style={{ margin: 0, fontSize: 12, color: 'var(--text-muted)' }}>Safari → زر المشاركة ☐↑ → إضافة إلى الشاشة الرئيسية</p>
              ) : (
                <p style={{ margin: 0, fontSize: 12, color: 'var(--text-muted)' }}>افتح الرابط من الموبايل (آيفون أو أندرويد) لمشاهدة الخطوات</p>
              )}
            </div>
          </>
        )}
        <button type="button" onClick={onClose} style={{ marginTop: 16, width: '100%', padding: 10, background: 'none', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', cursor: 'pointer', fontSize: 14 }}>إغلاق</button>
      </div>
    </div>
  );
}
