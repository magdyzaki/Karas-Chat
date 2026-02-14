import { useState, useEffect } from 'react';
import * as api from './api';

const TRENDING_QUERIES = ['ضحك', 'حب', 'سلام', 'مرح', 'شكراً', 'موافق', 'صداقة'];

export default function GifPicker({ onSelect, onClose }) {
  const [query, setQuery] = useState('');
  const [gifs, setGifs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api.getTrendingGifs()
      .then((list) => { setGifs(list); setError(''); })
      .catch((e) => { setError(e.message); setGifs([]); })
      .finally(() => setLoading(false));
  }, []);

  const doSearch = () => {
    const q = query.trim();
    if (!q) return;
    setLoading(true);
    api.searchGifs(q)
      .then((list) => { setGifs(list); setError(''); })
      .catch((e) => { setError(e.message); setGifs([]); })
      .finally(() => setLoading(false));
  };

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 160 }} onClick={onClose}>
      <div style={{ background: 'var(--surface)', borderRadius: 12, padding: 16, maxWidth: 380, width: '100%', maxHeight: '85vh', overflow: 'hidden', display: 'flex', flexDirection: 'column', border: '1px solid var(--border)' }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h3 style={{ margin: 0, fontSize: 16 }}>اختر GIF</h3>
          <button type="button" onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 22, cursor: 'pointer', color: 'var(--text)' }}>×</button>
        </div>
        <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
          <input
            type="text"
            placeholder="ابحث (مثل: ضحك، حب...)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && doSearch()}
            style={{ flex: 1, padding: '10px 14px', border: '1px solid var(--border)', borderRadius: 8, background: 'var(--bg)', color: 'var(--text)', fontSize: 14, textAlign: 'right' }}
          />
          <button type="button" onClick={doSearch} style={{ padding: '10px 16px', background: 'var(--primary)', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer', fontSize: 14 }}>بحث</button>
        </div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 12 }}>
          {TRENDING_QUERIES.map((q) => (
            <button key={q} type="button" onClick={() => { setQuery(q); setLoading(true); api.searchGifs(q).then((l) => { setGifs(l); setError(''); }).catch((e) => { setError(e.message); }).finally(() => setLoading(false)); }} style={{ padding: '6px 12px', background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 20, color: 'var(--text)', cursor: 'pointer', fontSize: 12 }}>{q}</button>
          ))}
        </div>
        <div style={{ flex: 1, overflow: 'auto', minHeight: 200 }}>
          {loading && <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 24 }}>جاري التحميل...</p>}
          {error && !loading && <p style={{ color: '#f85149', fontSize: 13, padding: 12 }}>{error}</p>}
          {!loading && !error && gifs.length === 0 && <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 24 }}>لا توجد نتائج</p>}
          {!loading && gifs.length > 0 && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8 }}>
              {gifs.map((g) => (
                <button key={g.id} type="button" onClick={() => { onSelect(g.url); onClose(); }} style={{ padding: 0, border: 'none', background: 'var(--bg)', borderRadius: 8, overflow: 'hidden', cursor: 'pointer' }}>
                  <img src={g.url} alt="" style={{ width: '100%', height: 120, objectFit: 'cover', display: 'block' }} />
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
