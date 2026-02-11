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
    api.checkInviteLink(token).then((data) => {
      if (data.valid) {
        setStatus('valid');
      } else {
        setStatus('invalid');
        setError(data.error || 'هذا الرابط غير صالح أو تم استخدامه مسبقاً');
      }
    }).catch(() => {
      setStatus('invalid');
      setError('فشل التحقق من الرابط');
    });
  }, [token]);

  const handleGoToApp = async () => {
    const data = await api.consumeInviteLink(token);
    if (data.ok) {
      onValid?.();
    } else {
      setStatus('invalid');
      setError(data.error || 'فشل تفعيل الرابط');
    }
  };

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
        <p style={{ color: 'var(--text)', marginBottom: 20, fontSize: 16 }}>إضافة Karas شات إلى الشاشة الرئيسية على الآيفون:</p>
        <div style={{ background: 'var(--surface)', borderRadius: 12, padding: 20, marginBottom: 24, textAlign: 'right', maxWidth: 340 }}>
          <p style={{ margin: '0 0 12px', fontSize: 15 }}>1. اضغط زر <strong>المشاركة</strong> في أسفل الشاشة (المربع والسهم)</p>
          <p style={{ margin: '0 0 12px', fontSize: 15 }}>2. مرّر للأسفل واختر <strong>إضافة إلى الشاشة الرئيسية</strong></p>
          <p style={{ margin: 0, fontSize: 15 }}>3. اضغط <strong>إضافة</strong></p>
        </div>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 20 }}>استخدم Safari للمتصفح — Chrome يدعمها أيضاً من القائمة ⋮</p>
        <button type="button" onClick={handleGoToApp} style={{ padding: '12px 24px', background: 'var(--primary)', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer', fontSize: 16 }}>انتقل إلى التطبيق</button>
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
