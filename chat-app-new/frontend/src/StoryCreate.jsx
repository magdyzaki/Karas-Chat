import { useState, useRef } from 'react';
import * as api from './api';

export default function StoryCreate({ onClose, onCreated }) {
  const [type, setType] = useState('text');
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (type === 'text') {
        await api.createStory('text', text.trim());
        onCreated?.();
        onClose();
      }
    } catch (err) {
      setError(err.message || 'فشل النشر');
    } finally {
      setLoading(false);
    }
  };

  const handleFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError('');
    setLoading(true);
    try {
      const { url, filename } = await api.uploadFile(file);
      const fullUrl = api.uploadsUrl(url);
      const t = (file.type || '').startsWith('image/') ? 'image' : (file.type || '').startsWith('video/') ? 'video' : 'text';
      await api.createStory(t, fullUrl, filename || file.name);
      onCreated?.();
      onClose();
    } catch (err) {
      setError(err.message || 'فشل الرفع');
    } finally {
      setLoading(false);
      e.target.value = '';
    }
  };

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 150 }} onClick={onClose}>
      <div style={{ background: 'var(--surface)', borderRadius: 12, padding: 24, maxWidth: 360, width: '100%', border: '1px solid var(--border)' }} onClick={(e) => e.stopPropagation()}>
        <h3 style={{ margin: '0 0 16px' }}>قصة جديدة</h3>
        <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
          {['text', 'image', 'video'].map((t) => (
            <button key={t} type="button" onClick={() => setType(t)} style={{ padding: '8px 16px', border: `1px solid ${type === t ? 'var(--primary)' : 'var(--border)'}`, borderRadius: 8, background: type === t ? 'var(--primary)' : 'var(--bg)', color: type === t ? '#fff' : 'var(--text)', cursor: 'pointer', fontSize: 14 }}>
              {t === 'text' ? 'نص' : t === 'image' ? 'صورة' : 'فيديو'}
            </button>
          ))}
        </div>
        {type === 'text' && (
          <form onSubmit={handleSubmit}>
            <textarea value={text} onChange={(e) => setText(e.target.value)} placeholder="اكتب قصتك..." rows={4} style={{ width: '100%', padding: 12, border: '1px solid var(--border)', borderRadius: 8, background: 'var(--bg)', color: 'var(--text)', fontSize: 14, resize: 'vertical' }} />
            <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
              <button type="submit" disabled={loading || !text.trim()} style={{ padding: '10px 20px', background: 'var(--primary)', border: 'none', borderRadius: 8, color: '#fff', cursor: loading ? 'wait' : 'pointer', fontSize: 14 }}>{loading ? '...' : 'نشر'}</button>
              <button type="button" onClick={onClose} style={{ padding: '10px 20px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', cursor: 'pointer', fontSize: 14 }}>إلغاء</button>
            </div>
          </form>
        )}
        {(type === 'image' || type === 'video') && (
          <div>
            <input type="file" ref={fileInputRef} accept={type === 'image' ? 'image/*' : 'video/*'} style={{ display: 'none' }} onChange={handleFile} />
            <button type="button" onClick={() => fileInputRef.current?.click()} disabled={loading} style={{ padding: '12px 24px', background: 'var(--primary)', border: 'none', borderRadius: 8, color: '#fff', cursor: loading ? 'wait' : 'pointer', fontSize: 14 }}>{loading ? 'جاري الرفع...' : `اختر ${type === 'image' ? 'صورة' : 'فيديو'}`}</button>
            <button type="button" onClick={onClose} style={{ marginRight: 8, padding: '12px 20px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', cursor: 'pointer', fontSize: 14 }}>إلغاء</button>
          </div>
        )}
        {error && <p style={{ marginTop: 12, color: '#f85149', fontSize: 13 }}>{error}</p>}
      </div>
    </div>
  );
}
