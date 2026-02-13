import { useState, useEffect, useRef } from 'react';
import * as api from './api';

const SETTINGS_KEY = 'chat_appearance';

const defaultSettings = {
  theme: 'dark',
  themePreset: '',
  fontSize: 'medium',
  fontFamily: 'system',
  chatBg: 'solid',
  pageBg: null,
  primaryColor: null,
  borderColor: null,
  msgBgOwn: '#1a5f2a',
  msgTextOwn: '#ffffff',
  msgBgOther: '#1c2128',
  msgTextOther: null,
  msgSenderColor: null,
  msgMetaColor: null,
  listNameColor: null,
  chatWallpaper: null,
  chatWallpaperImage: null,
  menuBg: null
};

const WALLPAPER_IMAGES = [
  { id: 'none', name: 'بدون صورة', url: null },
  { id: 'nature1', name: 'طبيعة', url: 'https://images.unsplash.com/photo-1506905925346-21bda3d9df44?w=800' },
  { id: 'gradient1', name: 'تدرج أزرق', url: 'https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=800' },
  { id: 'abstract1', name: 'مجرد', url: 'https://images.unsplash.com/photo-1579546929518-9e396b3cc329?w=800' }
];

const THEME_PRESETS = [
  { id: 'default', name: 'افتراضي', theme: 'dark' },
  { id: 'whatsapp', name: 'واتساب', theme: 'dark', primaryColor: '#00a884', msgBgOwn: '#005c4b' },
  { id: 'telegram', name: 'تليجرام', theme: 'dark', primaryColor: '#2aabee', msgBgOwn: '#2b5278' },
  { id: 'blue', name: 'أزرق', theme: 'dark', primaryColor: '#1877f2', msgBgOwn: '#0d6b2a' },
  { id: 'purple', name: 'بنفسجي', theme: 'dark', primaryColor: '#7c3aed', msgBgOwn: '#5b21b6' },
  { id: 'red', name: 'أحمر', theme: 'dark', primaryColor: '#dc2626', msgBgOwn: '#991b1b' },
  { id: 'light', name: 'فاتح', theme: 'light' },
  { id: 'sepia', name: 'سيبيا', theme: 'light', pageBg: '#f4ecd8', msgBgOther: '#e8dcc8' }
];

function loadSettings() {
  try {
    const s = localStorage.getItem(SETTINGS_KEY);
    if (s) return { ...defaultSettings, ...JSON.parse(s) };
  } catch (_) {}
  return defaultSettings;
}

function saveSettings(s) {
  try {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(s));
  } catch (_) {}
}

function applySettings(s) {
  document.documentElement.setAttribute('data-theme', s.theme === 'light' ? 'light' : 'dark');
  if (s.fontSize && s.fontSize !== 'medium') document.documentElement.setAttribute('data-font-size', s.fontSize);
  else document.documentElement.removeAttribute('data-font-size');
  if (s.fontFamily && s.fontFamily !== 'system') document.documentElement.setAttribute('data-font', s.fontFamily);
  else document.documentElement.removeAttribute('data-font');
  const root = document.documentElement.style;
  root.setProperty('--msg-bg-own', s.msgBgOwn || '#1a5f2a');
  root.setProperty('--msg-text-own', s.msgTextOwn || '#ffffff');
  root.setProperty('--msg-bg-other', s.msgBgOther || 'var(--surface)');
  if (s.msgTextOther) root.setProperty('--msg-text-other', s.msgTextOther);
  else root.removeProperty('--msg-text-other');
  if (s.msgSenderColor) root.setProperty('--msg-sender-color', s.msgSenderColor);
  else root.removeProperty('--msg-sender-color');
  if (s.msgMetaColor) root.setProperty('--msg-meta-color', s.msgMetaColor);
  else root.removeProperty('--msg-meta-color');
  if (s.listNameColor) root.setProperty('--list-name-color', s.listNameColor);
  else root.removeProperty('--list-name-color');
  if (s.primaryColor) root.setProperty('--primary', s.primaryColor);
  else root.removeProperty('--primary');
  const hasWallpaperImage = s.chatWallpaperImage && String(s.chatWallpaperImage).trim();
  if (hasWallpaperImage) {
    try {
      root.setProperty('--chat-wallpaper-image', `url("${String(s.chatWallpaperImage).replace(/"/g, '%22')}")`);
    } catch (_) {}
  } else {
    root.removeProperty('--chat-wallpaper-image');
  }
  const useImageBg = !!hasWallpaperImage;
  if (s.pageBg && !useImageBg) root.setProperty('--chat-wallpaper', s.pageBg);
  else if (s.chatWallpaper && !useImageBg) root.setProperty('--chat-wallpaper', s.chatWallpaper);
  else if (!useImageBg) root.removeProperty('--chat-wallpaper');
  if (s.menuBg) root.setProperty('--menu-bg', s.menuBg);
  else root.removeProperty('--menu-bg');
  if (s.borderColor) root.setProperty('--border', s.borderColor);
  else root.removeProperty('--border');
  if (document.body) document.body.setAttribute('data-chat-bg', (hasWallpaperImage ? 'image' : s.chatBg) || 'solid');
}

export default function Settings({ onClose, user, onUserUpdate }) {
  const [s, setS] = useState(loadSettings);
  const [avatarLoading, setAvatarLoading] = useState(false);
  const [avatarError, setAvatarError] = useState('');
  const fileInputRef = useRef(null);

  useEffect(() => {
    applySettings(s);
    saveSettings(s);
  }, [s]);

  const update = (key, val) => setS((prev) => ({ ...prev, [key]: val }));

  const applyPreset = (preset) => {
    setS((prev) => ({
      ...prev,
      themePreset: preset.id,
      theme: preset.theme || prev.theme,
      primaryColor: preset.primaryColor || null,
      msgBgOwn: preset.msgBgOwn || prev.msgBgOwn,
      pageBg: preset.pageBg || null,
      msgBgOther: preset.msgBgOther || null
    }));
  };

  const handleAvatarChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setAvatarError('');
    setAvatarLoading(true);
    try {
      const data = await api.uploadAvatar(file);
      onUserUpdate?.({ ...user, avatar_url: data.avatar_url });
      localStorage.setItem('chat_user', JSON.stringify({ ...user, avatar_url: data.avatar_url }));
    } catch (err) {
      setAvatarError(err.message || 'فشل رفع الصورة');
    } finally {
      setAvatarLoading(false);
      e.target.value = '';
    }
  };

  const handleEnableNotifications = async () => {
    try {
      if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        alert('المتصفح لا يدعم التنبيهات. جرّب Chrome أو Edge.');
        return;
      }
      const key = import.meta.env.VITE_VAPID_PUBLIC_KEY;
      if (!key || !key.trim()) {
        alert('التنبيهات غير مفعّلة. أضف VITE_VAPID_PUBLIC_KEY في frontend/.env (انسخه من backend/.env)');
        return;
      }
      const reg = await navigator.serviceWorker.register('/sw.js', { scope: '/' });
      await reg.update();
      const perm = await Notification.requestPermission();
      if (perm !== 'granted') {
        alert('تم رفض الإذن. فعّل الإشعارات من إعدادات المتصفح.');
        return;
      }
      const base64 = key.replace(/-/g, '+').replace(/_/g, '/');
      const pad = '='.repeat((4 - base64.length % 4) % 4);
      const raw = atob(base64 + pad);
      const arr = new Uint8Array(raw.length);
      for (let i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i);
      const sub = await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: arr });
      await api.subscribePush(sub.toJSON());
      alert('تم تفعيل التنبيهات بنجاح.');
    } catch (e) {
      console.error('Push subscribe:', e);
      const msg = e?.message || 'فشل تفعيل التنبيهات';
      alert(msg + (msg.includes('HTTPS') ? '' : '\nتأكد أنك تستخدم HTTPS أو localhost.'));
    }
  };

  const section = (title, children) => (
    <div style={{ marginBottom: 20 }}>
      <h3 style={{ fontSize: 14, color: 'var(--text-muted)', margin: '0 0 10px', borderBottom: '1px solid var(--border)', paddingBottom: 6 }}>{title}</h3>
      {children}
    </div>
  );

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: 16 }} onClick={onClose}>
      <div style={{ background: 'var(--surface)', borderRadius: 16, padding: 24, maxWidth: 420, width: '100%', maxHeight: '90vh', overflow: 'auto', border: '1px solid var(--border)' }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <h2 style={{ margin: 0, fontSize: 20 }}>إعدادات المظهر والبروفايل</h2>
          <button type="button" onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 24, cursor: 'pointer', color: 'var(--text)' }}>×</button>
        </div>

        {section('النسخة الاحتياطية', (
          <div>
            <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 10 }}>تصدير نسخة احتياطية من محادثاتك ورسائلك كملف JSON على جهازك.</p>
            <button type="button" onClick={async () => { try { const blob = await api.exportBackup(); const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `chat-backup-${Date.now()}.json`; a.click(); URL.revokeObjectURL(a.href); } catch (e) { alert(e.message || 'فشل التصدير'); } }} style={{ padding: '10px 16px', background: 'var(--primary)', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer', fontSize: 14 }}>📥 تصدير نسخة احتياطية</button>
          </div>
        ))}

        {section('التنبيهات (عند إغلاق التطبيق)', (
          <div>
            <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 10 }}>تفعيل التنبيهات يعطيك صوت وتنبيه عند وصول رسالة حتى لو التطبيق مغلق.</p>
            <button type="button" onClick={handleEnableNotifications} style={{ padding: '10px 16px', background: 'var(--primary)', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer', fontSize: 14 }}>🔔 تفعيل التنبيهات</button>
          </div>
        ))}

        {section('صورة البروفايل', (
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <div onClick={() => fileInputRef.current?.click()} style={{ cursor: 'pointer' }}>
              {user?.avatar_url ? (
                <img src={api.uploadsUrl(user.avatar_url)} alt="" style={{ width: 80, height: 80, borderRadius: '50%', objectFit: 'cover', border: '2px solid var(--border)' }} />
              ) : (
                <div style={{ width: 80, height: 80, borderRadius: '50%', background: 'var(--bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 32, border: '2px dashed var(--border)' }}>👤</div>
              )}
            </div>
            <div>
              <p style={{ margin: '0 0 8px', fontSize: 13 }}>{user?.name || user?.email || user?.phone || 'المستخدم'} <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>(معرف: {user?.id})</span></p>
              <input type="file" ref={fileInputRef} onChange={handleAvatarChange} accept="image/*" style={{ display: 'none' }} />
              <button type="button" onClick={() => fileInputRef.current?.click()} disabled={avatarLoading} style={{ padding: '8px 16px', background: 'var(--primary)', border: 'none', borderRadius: 8, color: '#fff', cursor: avatarLoading ? 'wait' : 'pointer', fontSize: 13 }}>{avatarLoading ? 'جاري الرفع...' : 'تغيير الصورة'}</button>
              {avatarError && <p style={{ fontSize: 12, color: '#f85149', marginTop: 6 }}>{avatarError}</p>}
            </div>
          </div>
        ))}

        {section('قالب جاهز', (
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {THEME_PRESETS.map((p) => (
              <button key={p.id} type="button" onClick={() => applyPreset(p)} style={{ padding: '8px 12px', borderRadius: 8, border: `1px solid ${s.themePreset === p.id ? 'var(--primary)' : 'var(--border)'}`, background: s.themePreset === p.id ? 'var(--primary)' : 'var(--bg)', color: s.themePreset === p.id ? '#fff' : 'var(--text)', cursor: 'pointer', fontSize: 12 }}>{p.name}</button>
            ))}
          </div>
        ))}

        {section('المظهر', (
          <div style={{ display: 'flex', gap: 8 }}>
            {['dark', 'light'].map((t) => (
              <button key={t} type="button" onClick={() => update('theme', t)} style={{ padding: '8px 16px', borderRadius: 8, border: `1px solid ${s.theme === t ? 'var(--primary)' : 'var(--border)'}`, background: s.theme === t ? 'var(--primary)' : 'var(--bg)', color: s.theme === t ? '#fff' : 'var(--text)', cursor: 'pointer', fontSize: 14 }}>{t === 'dark' ? 'داكن' : 'فاتح'}</button>
            ))}
          </div>
        ))}

        {section('نوع الخط', (
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {['system', 'tajawal', 'cairo', 'amiri'].map((f) => (
              <button key={f} type="button" onClick={() => update('fontFamily', f)} style={{ padding: '8px 12px', borderRadius: 8, border: `1px solid ${s.fontFamily === f ? 'var(--primary)' : 'var(--border)'}`, background: s.fontFamily === f ? 'var(--primary)' : 'var(--bg)', color: s.fontFamily === f ? '#fff' : 'var(--text)', cursor: 'pointer', fontSize: 13 }}>{f === 'system' ? 'النظام' : f === 'tajawal' ? 'تجنّل' : f === 'cairo' ? 'القاهرة' : 'عامري'}</button>
            ))}
          </div>
        ))}

        {section('حجم الخط', (
          <div style={{ display: 'flex', gap: 8 }}>
            {['small', 'medium', 'large'].map((f) => (
              <button key={f} type="button" onClick={() => update('fontSize', f)} style={{ padding: '8px 16px', borderRadius: 8, border: `1px solid ${s.fontSize === f ? 'var(--primary)' : 'var(--border)'}`, background: s.fontSize === f ? 'var(--primary)' : 'var(--bg)', color: s.fontSize === f ? '#fff' : 'var(--text)', cursor: 'pointer', fontSize: 14 }}>{f === 'small' ? 'صغير' : f === 'large' ? 'كبير' : 'عادي'}</button>
            ))}
          </div>
        ))}

        {section('خلفية الشات', (
          <>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
              {['solid', 'dots', 'lines', 'grid', 'waves'].map((b) => (
                <button key={b} type="button" onClick={() => update('chatBg', b)} style={{ padding: '8px 12px', borderRadius: 8, border: `1px solid ${(s.chatBg === b && !s.chatWallpaperImage) ? 'var(--primary)' : 'var(--border)'}`, background: (s.chatBg === b && !s.chatWallpaperImage) ? 'var(--primary)' : 'var(--bg)', color: (s.chatBg === b && !s.chatWallpaperImage) ? '#fff' : 'var(--text)', cursor: 'pointer', fontSize: 13 }}>{b === 'solid' ? 'سادة' : b === 'dots' ? 'نقاط' : b === 'lines' ? 'خطوط' : b === 'grid' ? 'شبكة' : 'موجات'}</button>
              ))}
            </div>
            <div style={{ marginBottom: 8, fontSize: 13 }}>صورة خلفية:</div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
              {WALLPAPER_IMAGES.map((w) => (
                <button key={w.id} type="button" onClick={() => update('chatWallpaperImage', w.url)} style={{ padding: '6px 10px', borderRadius: 8, border: `1px solid ${(!s.chatWallpaperImage && w.id === 'none') || s.chatWallpaperImage === w.url ? 'var(--primary)' : 'var(--border)'}`, background: (!s.chatWallpaperImage && w.id === 'none') || s.chatWallpaperImage === w.url ? 'var(--primary)' : 'var(--bg)', color: (!s.chatWallpaperImage && w.id === 'none') || s.chatWallpaperImage === w.url ? '#fff' : 'var(--text)', cursor: 'pointer', fontSize: 12 }}>{w.name}</button>
              ))}
            </div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
              <input type="url" placeholder="رابط صورة مخصص..." value={s.chatWallpaperImage && !WALLPAPER_IMAGES.find((w) => w.url === s.chatWallpaperImage) ? s.chatWallpaperImage : ''} onChange={(e) => update('chatWallpaperImage', e.target.value || null)} style={{ flex: 1, minWidth: 120, padding: 8, border: '1px solid var(--border)', borderRadius: 8, background: 'var(--bg)', color: 'var(--text)', fontSize: 13 }} />
              <label style={{ padding: '8px 12px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, cursor: 'pointer', fontSize: 13, color: 'var(--text)' }}>
                رفع صورة
                <input type="file" accept="image/*" style={{ display: 'none' }} onChange={(e) => { const f = e.target.files?.[0]; if (f) { const r = new FileReader(); r.onload = () => update('chatWallpaperImage', r.result); r.readAsDataURL(f); } e.target.value = ''; }} />
              </label>
            </div>
          </>
        ))}

        {section('لون الصفحة / الخلفية', (
          <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
            <input type="color" value={s.pageBg || (s.theme === 'dark' ? '#0d1117' : '#f0f2f5')} onChange={(e) => update('pageBg', e.target.value)} style={{ width: 44, height: 36, padding: 2, border: '1px solid var(--border)', borderRadius: 8 }} />
            <span style={{ fontSize: 13 }}>خلفية الصفحة</span>
          </div>
        ))}

        {section('لون الرسائل المرسلة', (
          <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
            <input type="color" value={s.msgBgOwn} onChange={(e) => update('msgBgOwn', e.target.value)} style={{ width: 44, height: 36, padding: 2, border: '1px solid var(--border)', borderRadius: 8 }} />
            <span style={{ fontSize: 13 }}>الخلفية</span>
            <input type="color" value={s.msgTextOwn} onChange={(e) => update('msgTextOwn', e.target.value)} style={{ width: 44, height: 36, padding: 2, border: '1px solid var(--border)', borderRadius: 8 }} />
            <span style={{ fontSize: 13 }}>نص الرسالة</span>
          </div>
        ))}

        {section('لون الرسائل المستقبلة', (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
              <input type="color" value={s.msgBgOther || '#1c2128'} onChange={(e) => update('msgBgOther', e.target.value)} style={{ width: 44, height: 36, padding: 2, border: '1px solid var(--border)', borderRadius: 8 }} />
              <span style={{ fontSize: 13 }}>الخلفية</span>
              <input type="color" value={s.msgTextOther || (s.theme === 'dark' ? '#e6edf3' : '#050505')} onChange={(e) => update('msgTextOther', e.target.value)} style={{ width: 44, height: 36, padding: 2, border: '1px solid var(--border)', borderRadius: 8 }} />
              <span style={{ fontSize: 13 }}>نص الرسالة</span>
            </div>
            <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
              <input type="color" value={s.msgSenderColor || (s.theme === 'dark' ? '#58a6ff' : '#1877f2')} onChange={(e) => update('msgSenderColor', e.target.value)} style={{ width: 44, height: 36, padding: 2, border: '1px solid var(--border)', borderRadius: 8 }} />
              <span style={{ fontSize: 13 }}>اسم المرسل</span>
              <input type="color" value={s.msgMetaColor || (s.theme === 'dark' ? '#8b949e' : '#65676b')} onChange={(e) => update('msgMetaColor', e.target.value)} style={{ width: 44, height: 36, padding: 2, border: '1px solid var(--border)', borderRadius: 8 }} />
              <span style={{ fontSize: 13 }}>التاريخ والوقت</span>
            </div>
          </div>
        ))}

        {section('لون أسماء المحادثات', (
          <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
            <input type="color" value={s.listNameColor || (s.theme === 'dark' ? '#e6edf3' : '#050505')} onChange={(e) => update('listNameColor', e.target.value)} style={{ width: 44, height: 36, padding: 2, border: '1px solid var(--border)', borderRadius: 8 }} />
            <span style={{ fontSize: 13 }}>أسماء القوائم (المحادثات)</span>
          </div>
        ))}

        {section('لون الأزرار والعناصر', (
          <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
            <input type="color" value={s.primaryColor || '#238636'} onChange={(e) => update('primaryColor', e.target.value)} style={{ width: 44, height: 36, padding: 2, border: '1px solid var(--border)', borderRadius: 8 }} />
            <span style={{ fontSize: 13 }}>اللون الأساسي</span>
          </div>
        ))}

        <button type="button" onClick={onClose} style={{ marginTop: 20, padding: '10px 20px', background: 'var(--primary)', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer', fontSize: 14 }}>تم</button>
      </div>
    </div>
  );
}

export { loadSettings, applySettings };
