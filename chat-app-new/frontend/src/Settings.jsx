import { useState, useEffect, useRef } from 'react';
import * as api from './api';

const WALLPAPERS = [
  { id: 'default', name: 'افتراضي', bg: 'var(--bg)' },
  { id: 'dark', name: 'داكن', bg: '#0d1117' },
  { id: 'blue', name: 'أزرق', bg: 'linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%)' },
  { id: 'green', name: 'أخضر', bg: 'linear-gradient(135deg, #0d2818 0%, #1a3d2e 100%)' },
  { id: 'purple', name: 'بنفسجي', bg: 'linear-gradient(135deg, #1a0d2e 0%, #2d1b4e 100%)' },
  { id: 'light', name: 'فاتح', bg: '#f0f2f5' }
];

const CHAT_BGS = [
  { id: 'none', name: 'بدون' },
  { id: 'dots', name: 'نقاط' },
  { id: 'lines', name: 'خطوط' },
  { id: 'grid', name: 'شبكة' }
];

export default function Settings({ user, onClose, onUpdate }) {
  const [name, setName] = useState(user?.name || '');
  const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url || null);
  const [wallpaper, setWallpaper] = useState(() => localStorage.getItem('chat_wallpaper') || 'default');
  const [chatBg, setChatBg] = useState(() => localStorage.getItem('chat_bg') || 'none');
  const [theme, setTheme] = useState(() => localStorage.getItem('chat_theme') || 'dark');
  const [fontSize, setFontSize] = useState(() => localStorage.getItem('chat_font_size') || 'medium');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  useEffect(() => {
    api.getProfile().then((u) => {
      setName(u.name || '');
      setAvatarUrl(u.avatar_url || null);
    }).catch(() => {});
  }, []);

  const handleAvatarChange = (e) => {
    const file = e.target.files?.[0];
    if (!file || !file.type.startsWith('image/')) {
      setError('اختر صورة صالحة (jpg, png, gif)');
      return;
    }
    setUploading(true);
    setError('');
    api.uploadAvatar(file).then(({ avatar_url }) => {
      setAvatarUrl(api.uploadsUrl(avatar_url));
      onUpdate?.({ avatar_url });
    }).catch((err) => setError(err.message || 'فشل الرفع')).finally(() => setUploading(false));
    e.target.value = '';
  };

  const handleSaveName = () => {
    if (!name.trim()) return;
    api.updateProfile({ name: name.trim() }).then(() => onUpdate?.({ name: name.trim() })).catch((e) => setError(e.message));
  };

  const applyWallpaper = (id) => {
    setWallpaper(id);
    localStorage.setItem('chat_wallpaper', id);
    const bg = WALLPAPERS.find((w) => w.id === id)?.bg || 'var(--bg)';
    document.documentElement.style.setProperty('--chat-wallpaper', bg);
    document.body.style.background = bg;
  };

  const applyChatBg = (id) => {
    setChatBg(id);
    localStorage.setItem('chat_bg', id);
    document.body.dataset.chatBg = id;
  };

  const applyTheme = (t) => {
    setTheme(t);
    localStorage.setItem('chat_theme', t);
    document.documentElement.dataset.theme = t;
  };

  const applyFontSize = (s) => {
    setFontSize(s);
    localStorage.setItem('chat_font_size', s);
    document.documentElement.dataset.fontSize = s || 'medium';
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0,0,0,0.7)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 30,
      padding: 16
    }} onClick={onClose}>
      <div style={{
        background: 'var(--surface)',
        borderRadius: 16,
        padding: 24,
        maxWidth: 420,
        width: '100%',
        maxHeight: '90vh',
        overflow: 'auto',
        border: '1px solid var(--border)'
      }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <h2 style={{ margin: 0, fontSize: 20 }}>الإعدادات</h2>
          <button type="button" onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 24, cursor: 'pointer', color: 'var(--text)' }}>×</button>
        </div>

        {error && <p style={{ color: '#f85149', fontSize: 13, marginBottom: 12 }}>{error}</p>}

        <section style={{ marginBottom: 24 }}>
          <h3 style={{ fontSize: 14, color: 'var(--text-muted)', marginBottom: 12 }}>صورة البروفايل</h3>
          <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
            <div
              onClick={() => fileInputRef.current?.click()}
              style={{
                width: 80,
                height: 80,
                borderRadius: '50%',
                background: 'var(--bg)',
                border: '2px dashed var(--border)',
                overflow: 'hidden',
                cursor: uploading ? 'wait' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 28
              }}
            >
              {avatarUrl ? (
                <img src={avatarUrl} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              ) : (
                <span>👤</span>
              )}
            </div>
            <input ref={fileInputRef} type="file" accept="image/*" onChange={handleAvatarChange} style={{ display: 'none' }} />
            <div>
              <p style={{ margin: 0, fontSize: 12, color: 'var(--text-muted)' }}>اضغط على الصورة لتغييرها</p>
              {uploading && <p style={{ margin: '4px 0 0', fontSize: 12, color: 'var(--primary)' }}>جاري الرفع...</p>}
            </div>
          </div>
        </section>

        <section style={{ marginBottom: 24 }}>
          <h3 style={{ fontSize: 14, color: 'var(--text-muted)', marginBottom: 8 }}>الاسم</h3>
          <div style={{ display: 'flex', gap: 8 }}>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              onBlur={handleSaveName}
              style={{ flex: 1, padding: 10, border: '1px solid var(--border)', borderRadius: 8, background: 'var(--bg)', color: 'var(--text)', fontSize: 15 }}
              placeholder="الاسم"
            />
          </div>
        </section>

        <section style={{ marginBottom: 24 }}>
          <h3 style={{ fontSize: 14, color: 'var(--text-muted)', marginBottom: 8 }}>خلفية التطبيق</h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {WALLPAPERS.map((w) => (
              <button
                key={w.id}
                type="button"
                onClick={() => applyWallpaper(w.id)}
                style={{
                  width: 48,
                  height: 48,
                  borderRadius: 8,
                  background: w.bg,
                  border: wallpaper === w.id ? '3px solid var(--primary)' : '2px solid var(--border)',
                  cursor: 'pointer'
                }}
                title={w.name}
              />
            ))}
          </div>
        </section>

        <section style={{ marginBottom: 24 }}>
          <h3 style={{ fontSize: 14, color: 'var(--text-muted)', marginBottom: 8 }}>خلفية المحادثة</h3>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {CHAT_BGS.map((b) => (
              <button
                key={b.id}
                type="button"
                onClick={() => applyChatBg(b.id)}
                style={{
                  padding: '8px 14px',
                  borderRadius: 8,
                  background: chatBg === b.id ? 'var(--primary)' : 'var(--bg)',
                  border: '1px solid var(--border)',
                  color: chatBg === b.id ? '#fff' : 'var(--text)',
                  cursor: 'pointer',
                  fontSize: 13
                }}
              >
                {b.name}
              </button>
            ))}
          </div>
        </section>

        <section style={{ marginBottom: 24 }}>
          <h3 style={{ fontSize: 14, color: 'var(--text-muted)', marginBottom: 8 }}>المظهر</h3>
          <div style={{ display: 'flex', gap: 8 }}>
            <button
              type="button"
              onClick={() => applyTheme('dark')}
              style={{
                padding: '8px 16px',
                borderRadius: 8,
                background: theme === 'dark' ? 'var(--primary)' : 'var(--bg)',
                border: '1px solid var(--border)',
                color: theme === 'dark' ? '#fff' : 'var(--text)',
                cursor: 'pointer',
                fontSize: 13
              }}
            >
              داكن
            </button>
            <button
              type="button"
              onClick={() => applyTheme('light')}
              style={{
                padding: '8px 16px',
                borderRadius: 8,
                background: theme === 'light' ? 'var(--primary)' : 'var(--bg)',
                border: '1px solid var(--border)',
                color: theme === 'light' ? '#fff' : 'var(--text)',
                cursor: 'pointer',
                fontSize: 13
              }}
            >
              فاتح
            </button>
          </div>
        </section>

        <section style={{ marginBottom: 24 }}>
          <h3 style={{ fontSize: 14, color: 'var(--text-muted)', marginBottom: 8 }}>حجم الخط</h3>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {['small', 'medium', 'large'].map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => applyFontSize(s)}
                style={{
                  padding: '8px 14px',
                  borderRadius: 8,
                  background: fontSize === s ? 'var(--primary)' : 'var(--bg)',
                  border: '1px solid var(--border)',
                  color: fontSize === s ? '#fff' : 'var(--text)',
                  cursor: 'pointer',
                  fontSize: s === 'small' ? 12 : s === 'large' ? 16 : 13
                }}
              >
                {s === 'small' ? 'صغير' : s === 'medium' ? 'متوسط' : 'كبير'}
              </button>
            ))}
          </div>
        </section>

        <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 8 }}>
          معرفك: <strong>{user?.id}</strong>
        </p>
      </div>
    </div>
  );
}
