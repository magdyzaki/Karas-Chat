import { useState } from 'react';
import * as api from './api';

export default function ApiUrlModal({ onClose }) {
  const [apiUrl, setApiUrl] = useState(() => {
    try { return localStorage.getItem('chat_api_url') || import.meta.env?.VITE_API_URL || ''; } catch { return ''; }
  });
  const [msg, setMsg] = useState('');

  const handleSave = async () => {
    const v = apiUrl.trim().replace(/\/$/, '');
    setMsg('');
    if (!v) {
      api.setApiBase('');
      localStorage.removeItem('chat_api_url');
      setMsg('تم الحذف');
      return;
    }
    try {
      const r = await fetch(`${v}/api/health`, { headers: { 'ngrok-skip-browser-warning': 'true' } });
      const d = await r.json();
      if (d?.ok) {
        api.setApiBase(v);
        localStorage.setItem('chat_api_url', v);
        setMsg('✓ تم الحفظ');
        setTimeout(() => onClose(), 1500);
      } else setMsg('لم يتعرّف السيرفر');
    } catch {
      setMsg('فشل الاتصال. شغّل الباكند و ngrok على الكمبيوتر');
    }
  };

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: 16 }} onClick={onClose}>
      <div style={{ background: 'var(--surface)', borderRadius: 16, padding: 24, maxWidth: 400, width: '100%', border: '1px solid var(--border)' }} onClick={e => e.stopPropagation()}>
        <h2 style={{ margin: '0 0 16px', fontSize: 20 }}>🔗 رابط السيرفر</h2>
        <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 12 }}>ضع رابط ngrok (مثال: https://xxx.ngrok-free.dev)</p>
        <input type="url" placeholder="https://xxx.ngrok-free.dev" value={apiUrl} onChange={e => setApiUrl(e.target.value)} style={{ width: '100%', padding: 12, border: '1px solid var(--border)', borderRadius: 8, background: 'var(--bg)', color: 'var(--text)', marginBottom: 12 }} />
        <button type="button" onClick={handleSave} style={{ width: '100%', padding: 12, background: 'var(--primary)', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer', fontSize: 16 }}>حفظ واختبار</button>
        {msg && <p style={{ fontSize: 13, marginTop: 12, color: msg.startsWith('✓') ? '#4ade80' : '#f85149' }}>{msg}</p>}
        <button type="button" onClick={onClose} style={{ width: '100%', marginTop: 12, padding: 10, background: 'none', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', cursor: 'pointer' }}>إغلاق</button>
      </div>
    </div>
  );
}
