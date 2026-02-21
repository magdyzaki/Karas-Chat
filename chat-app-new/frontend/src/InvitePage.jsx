import { useState, useEffect } from 'react';
import * as api from './api';

export default function InvitePage({ token, onValid }) {
  useEffect(() => { api.prewakeBackend(); }, []);
  const [status, setStatus] = useState('valid'); // valid | invalid
  const [error, setError] = useState('');
  const [consuming, setConsuming] = useState(false);

  const handleGoToApp = async () => {
    if (!token || consuming) return;
    setConsuming(true);
    setError('');
    try {
      const data = await api.consumeInviteLink(token);
      if (data.ok) {
        onValid?.();
      } else {
        setStatus('invalid');
        setError(data.error || 'الرابط مُستهلَك أو غير صالح');
      }
    } catch (e) {
      setStatus('invalid');
      setError(e?.message || 'فشل الاتصال. تحقق من الإنترنت وحاول مرة أخرى.');
    } finally {
      setConsuming(false);
    }
  };

  if (!token) {
    return (
      <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 24, textAlign: 'center' }}>
        <p style={{ color: '#f85149' }}>رابط غير صالح</p>
      </div>
    );
  }

  if (status === 'valid') {
    const isAndroid = /Android/i.test(navigator.userAgent);
    return (
      <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 24, textAlign: 'center' }}>
        <p style={{ color: 'var(--primary)', fontSize: 18, marginBottom: 16 }}>✓ تم تفعيل الرابط بنجاح</p>
        <p style={{ color: '#f85149', fontSize: 14, marginBottom: 20 }}>⚠ لا تُشارك هذا الرابط — يعمل مرة واحدة فقط</p>
        <p style={{ color: 'var(--text)', marginBottom: 20, fontSize: 16 }}>{isAndroid ? 'إضافة Karas شات على الأندرويد:' : 'إضافة Karas شات على الآيفون:'}</p>
        {isAndroid ? (
          <div style={{ background: 'var(--surface)', borderRadius: 12, padding: 20, marginBottom: 24, textAlign: 'right', maxWidth: 340 }}>
            <p style={{ margin: '0 0 12px', fontSize: 15 }}>1. في Chrome اضغط القائمة <strong>⋮</strong> (أعلى اليمين)</p>
            <p style={{ margin: '0 0 12px', fontSize: 15 }}>2. اختر <strong>إضافة إلى الشاشة الرئيسية</strong></p>
            <p style={{ margin: 0, fontSize: 15 }}>3. اضغط <strong>إضافة</strong></p>
          </div>
        ) : (
          <div style={{ background: 'var(--surface)', borderRadius: 12, padding: 20, marginBottom: 24, textAlign: 'right', maxWidth: 340 }}>
            <p style={{ margin: '0 0 12px', fontSize: 15 }}>1. اضغط زر <strong>المشاركة</strong> (المربع والسهم)</p>
            <p style={{ margin: '0 0 12px', fontSize: 15 }}>2. اختر <strong>إضافة إلى الشاشة الرئيسية</strong></p>
            <p style={{ margin: 0, fontSize: 15 }}>3. اضغط <strong>إضافة</strong></p>
          </div>
        )}
        <button type="button" onClick={handleGoToApp} disabled={consuming} style={{ padding: '12px 24px', background: consuming ? 'var(--text-muted)' : 'var(--primary)', border: 'none', borderRadius: 8, color: '#fff', cursor: consuming ? 'wait' : 'pointer', fontSize: 16 }}>{consuming ? 'جاري الاتصال...' : 'انتقل إلى التطبيق'}</button>
      </div>
    );
  }

  const isNetworkError = /fetch|شبكة|اتصال|Failed/i.test(error || '');
  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 24, textAlign: 'center' }}>
      <p style={{ color: '#f85149', fontSize: 18, marginBottom: 8 }}>⚠ حدث خطأ</p>
      <p style={{ color: 'var(--text-muted)', fontSize: 14, marginBottom: 16 }}>{error}</p>
      {isNetworkError && (
        <p style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 16 }}>💡 جرّب شبكة واي فاي بدل بيانات الجوال</p>
      )}
      <button type="button" onClick={() => { setError(''); handleGoToApp(); }} disabled={consuming} style={{ padding: '10px 20px', background: consuming ? 'var(--text-muted)' : 'var(--primary)', border: 'none', borderRadius: 8, color: '#fff', cursor: consuming ? 'wait' : 'pointer', fontSize: 15 }}>{consuming ? 'جاري المحاولة...' : 'حاول مرة أخرى'}</button>
    </div>
  );
}
