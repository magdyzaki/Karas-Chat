import { useState, useRef } from 'react';
import * as api from './api';
import { playSent } from './sounds';

export default function BroadcastCompose({ list, onBack, onSent }) {
  const [text, setText] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  const handleSend = async (type = 'text', content, file_name = null) => {
    if (!content && type === 'text') return;
    setSending(true);
    setError('');
    try {
      await api.sendBroadcastMessage(list.id, { type, content, file_name });
      if (type === 'text') setText('');
      playSent();
      onSent?.();
    } catch (e) {
      setError(e.message || 'فشل الإرسال');
    } finally {
      setSending(false);
    }
  };

  const handleFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError('');
    try {
      const { url, filename } = await api.uploadFile(file);
      const fullUrl = api.uploadsUrl(url);
      const type = (file.type || '').startsWith('image/') ? 'image' : (file.type || '').startsWith('video/') ? 'video' : 'file';
      await handleSend(type, fullUrl, filename || file.name);
    } catch (e) {
      setError(e.message || 'فشل رفع الملف');
    }
    e.target.value = '';
  };

  const count = list?.recipients?.length || list?.recipient_ids?.length || 0;

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', borderRight: '1px solid var(--border)' }}>
      <div style={{ padding: 12, borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 12 }}>
        <button type="button" onClick={onBack} style={{ padding: '6px 12px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', cursor: 'pointer', fontSize: 13 }}>←</button>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 600 }}>📢 {list?.name || 'قائمة بث'}</div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{count} جهة اتصال</div>
        </div>
      </div>
      <div style={{ flex: 1, padding: 16, overflow: 'auto', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', textAlign: 'center' }}>
        <p style={{ margin: 0, fontSize: 15 }}>اكتب رسالتك وأرسلها لجميع المستلمين دفعة واحدة</p>
        <p style={{ margin: '8px 0 0', fontSize: 13, opacity: 0.9 }}>كل مستلم يستقبلها في محادثته الفردية معك</p>
      </div>
      {error && <p style={{ padding: 8, margin: 0, fontSize: 13, color: '#f85149', background: 'rgba(248,81,73,0.1)' }}>{error}</p>}
      <form
        onSubmit={(e) => { e.preventDefault(); handleSend('text', text.trim()); }}
        style={{ padding: 12, borderTop: '1px solid var(--border)', display: 'flex', gap: 6, alignItems: 'flex-end', flexWrap: 'wrap' }}
      >
        <input type="file" ref={fileInputRef} onChange={handleFile} accept="image/*,video/*" style={{ display: 'none' }} />
        <button type="button" onClick={() => fileInputRef.current?.click()} style={{ padding: 10, border: '1px solid var(--border)', borderRadius: 8, background: 'var(--surface)', color: 'var(--text)', cursor: 'pointer', fontSize: 18 }} title="صورة أو فيديو">📷</button>
        <input
          type="text"
          placeholder="اكتب الرسالة..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          style={{ flex: 1, minWidth: 120, padding: '10px 14px', border: '1px solid var(--border)', borderRadius: 8, background: 'var(--bg)', color: 'var(--text)', fontSize: 15, minHeight: 44, textAlign: 'right' }}
        />
        <button type="submit" disabled={sending || !text.trim()} style={{ padding: '10px 20px', border: 'none', borderRadius: 8, background: 'var(--primary)', color: '#fff', cursor: sending ? 'wait' : 'pointer', fontSize: 15 }}>{sending ? '...' : 'إرسال'}</button>
      </form>
    </div>
  );
}
