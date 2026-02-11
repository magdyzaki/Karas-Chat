import { useState, useEffect } from 'react';
import * as api from './api';

export default function InvitePage({ token, onValid }) {
  const [status, setStatus] = useState('loading'); // loading | valid | invalid
  const [error, setError] = useState('');

  useEffect(() => {
    if (!token) {
      setStatus('invalid');
      setError('رابط غير صالح');
      return;
    }
    api.validateInviteLink(token).then((data) => {
      if (data.valid) {
        setStatus('valid');
        setTimeout(() => onValid?.(), 1500);
      } else {
        setStatus('invalid');
        setError(data.error || 'هذا الرابط غير صالح أو تم استخدامه مسبقاً');
      }
    }).catch(() => {
      setStatus('invalid');
      setError('فشل التحقق من الرابط');
    });
  }, [token, onValid]);

  if (status === 'loading') {
    return (
      <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 24, textAlign: 'center' }}>
        <p style={{ color: 'var(--text-muted)' }}>جاري التحقق من الرابط...</p>
      </div>
    );
  }

  if (status === 'valid') {
    return (
      <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 24, textAlign: 'center' }}>
        <p style={{ color: 'var(--primary)', fontSize: 18, marginBottom: 16 }}>✓ تم تفعيل الرابط بنجاح</p>
        <p style={{ color: 'var(--text)', marginBottom: 24 }}>يمكنك الآن إضافة Karas شات إلى الشاشة الرئيسية</p>
        <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>في Safari: مشاركة ← إضافة إلى الشاشة الرئيسية</p>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 24, textAlign: 'center' }}>
      <p style={{ color: '#f85149', fontSize: 18, marginBottom: 8 }}>⚠ الرابط غير صالح</p>
      <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>{error}</p>
    </div>
  );
}
