import { useState } from 'react';
import * as api from './api';

const styles = {
  page: { minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 },
  box: { background: 'var(--surface)', borderRadius: 12, padding: 24, width: '100%', maxWidth: 360, border: '1px solid var(--border)' },
  title: { marginTop: 0, marginBottom: 20, fontSize: 22 },
  input: { width: '100%', padding: 12, marginBottom: 12, border: '1px solid var(--border)', borderRadius: 8, background: 'var(--bg)', color: 'var(--text)', fontSize: 16 },
  btn: { width: '100%', padding: 12, border: 'none', borderRadius: 8, background: 'var(--primary)', color: '#fff', fontSize: 16, cursor: 'pointer' },
  err: { color: '#f85149', fontSize: 14, marginBottom: 12 },
  toggle: { marginTop: 12, textAlign: 'center' },
  hint: { fontSize: 12, color: 'var(--text-muted)', marginTop: -6, marginBottom: 12 }
};

export default function Auth({ onLogin }) {
  const [mode, setMode] = useState('login'); // login | register | verify | pending | forgot | reset
  const [emailOrPhone, setEmailOrPhone] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const goTo = (m) => { setMode(m); setError(''); setCode(''); setNewPassword(''); };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (mode === 'login') {
        if (!emailOrPhone.trim() || !password) {
          setError('البريد أو رقم الموبايل وكلمة المرور مطلوبان');
          return;
        }
        const data = await api.login(emailOrPhone.trim(), password);
        onLogin(data);
      } else if (mode === 'register') {
        if (!emailOrPhone.trim() || !password) {
          setError('البريد أو رقم الموبايل وكلمة المرور مطلوبان');
          return;
        }
        const data = await api.register(emailOrPhone.trim(), password, name);
        if (data.token && data.user) {
          onLogin(data);
        } else if (data.needsApproval) {
          setMode('pending');
        } else if (data.needsVerification) {
          setMode('verify');
        } else {
          onLogin(data);
        }
      } else if (mode === 'verify') {
        if (!code.trim()) { setError('أدخل رمز التحقق'); return; }
        const data = await api.verify(emailOrPhone.trim(), code.trim());
        onLogin(data);
      } else if (mode === 'forgot') {
        if (!emailOrPhone.trim()) { setError('أدخل البريد أو رقم الموبايل'); return; }
        await api.forgotPassword(emailOrPhone.trim());
        setMode('reset');
      } else if (mode === 'reset') {
        if (!code.trim() || !newPassword || newPassword.length < 6) {
          setError('رمز الاستعادة وكلمة مرور جديدة (6 أحرف على الأقل) مطلوبان');
          return;
        }
        const data = await api.resetPassword(emailOrPhone.trim(), code.trim(), newPassword);
        onLogin(data);
      }
    } catch (err) {
      setError(err.message || 'حدث خطأ');
    } finally {
      setLoading(false);
    }
  };

  if (mode === 'pending') {
    return (
      <div style={styles.page}>
        <div style={styles.box}>
          <h1 style={styles.title}>في انتظار التفعيل</h1>
          <p style={{ ...styles.hint, marginBottom: 20 }}>تم تسجيل حسابك بنجاح. المسؤول سيقوم بتفعيله قريباً. حاول تسجيل الدخول لاحقاً.</p>
          <button type="button" onClick={() => goTo('login')} style={styles.btn}>تسجيل الدخول</button>
        </div>
      </div>
    );
  }

  const fetchDevCode = async () => {
    try {
      const r = await api.getDevLastCode(emailOrPhone);
      if (r?.code) { setCode(r.code); setError(''); } else { setError(r?.msg || 'لا يوجد رمز. راجع ملف last_codes.json في مجلد backend'); }
    } catch (e) { setError(e.message || 'لم يُعثر على الرمز. تأكد من ALLOW_DEV_CODE=true ووجود last_codes.json'); }
  };

  if (mode === 'verify') {
    return (
      <div style={styles.page}>
        <div style={styles.box}>
          <h1 style={styles.title}>تأكيد الحساب</h1>
          <p style={styles.hint}>أدخل الرمز المرسل إلى بريدك أو جوالك ({emailOrPhone})</p>
          <p style={{ ...styles.hint, marginTop: -4, fontSize: 11, opacity: 0.8 }}>في وضع التطوير: الرمز يُحفظ في ملف last_codes.json (حتى لو أغلقت الباورشيل)</p>
          {error && <p style={styles.err}>{error}</p>}
          <form onSubmit={handleSubmit}>
            <input type="text" placeholder="رمز التحقق (6 أرقام)" value={code} onChange={(e) => setCode(e.target.value)} style={styles.input} maxLength={6} required />
            <button type="submit" style={styles.btn} disabled={loading}>{loading ? 'جاري...' : 'تأكيد'}</button>
          </form>
          <button type="button" onClick={fetchDevCode} style={{ width: '100%', marginTop: 8, padding: 8, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--primary)', cursor: 'pointer', fontSize: 13 }}>عرض الرمز من الملف (وضع التطوير)</button>
          <p style={styles.toggle}>
            <button type="button" onClick={() => goTo('login')} style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', fontSize: 14 }}>تسجيل الدخول</button>
          </p>
        </div>
      </div>
    );
  }

  if (mode === 'forgot') {
    return (
      <div style={styles.page}>
        <div style={styles.box}>
          <h1 style={styles.title}>نسيت كلمة المرور</h1>
          {error && <p style={styles.err}>{error}</p>}
          <form onSubmit={handleSubmit}>
            <input type="text" inputMode="email" placeholder="البريد أو رقم الموبايل" value={emailOrPhone} onChange={(e) => setEmailOrPhone(e.target.value)} style={styles.input} required />
            <button type="submit" style={styles.btn} disabled={loading}>{loading ? 'جاري...' : 'إرسال الرمز'}</button>
          </form>
          <p style={styles.toggle}>
            <button type="button" onClick={() => goTo('login')} style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', fontSize: 14 }}>رجوع لتسجيل الدخول</button>
          </p>
        </div>
      </div>
    );
  }

  if (mode === 'reset') {
    return (
      <div style={styles.page}>
        <div style={styles.box}>
          <h1 style={styles.title}>تغيير كلمة المرور</h1>
          <p style={styles.hint}>أدخل الرمز المرسل إلى {emailOrPhone} وكلمة مرور جديدة</p>
          {error && <p style={styles.err}>{error}</p>}
          <form onSubmit={handleSubmit}>
            <input type="text" placeholder="رمز الاستعادة" value={code} onChange={(e) => setCode(e.target.value)} style={styles.input} maxLength={6} required />
            <button type="button" onClick={fetchDevCode} style={{ width: '100%', marginBottom: 8, padding: 6, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, color: 'var(--primary)', cursor: 'pointer', fontSize: 12 }}>عرض الرمز من الملف</button>
            <input type="password" placeholder="كلمة المرور الجديدة (6+ أحرف)" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} style={styles.input} minLength={6} required />
            <button type="submit" style={styles.btn} disabled={loading}>{loading ? 'جاري...' : 'حفظ'}</button>
          </form>
          <p style={styles.toggle}>
            <button type="button" onClick={() => goTo('forgot')} style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', fontSize: 14 }}>طلب رمز جديد</button>
          </p>
        </div>
      </div>
    );
  }

  const isLogin = mode === 'login';
  return (
    <div style={styles.page}>
      <div style={styles.box}>
        <h1 style={styles.title}>{isLogin ? 'تسجيل الدخول' : 'إنشاء حساب'}</h1>
        {error && <p style={styles.err}>{error}</p>}
        <form onSubmit={handleSubmit}>
          {!isLogin && (
            <input type="text" placeholder="الاسم" value={name} onChange={(e) => setName(e.target.value)} style={styles.input} />
          )}
          <input
            type="text"
            inputMode="email"
            placeholder="البريد الإلكتروني أو رقم الموبايل"
            value={emailOrPhone}
            onChange={(e) => setEmailOrPhone(e.target.value)}
            style={styles.input}
            required
          />
          <p style={styles.hint}>أدخل بريدك أو رقم هاتفك (مثال: 01234567890)</p>
          <input type="password" placeholder="كلمة المرور" value={password} onChange={(e) => setPassword(e.target.value)} style={styles.input} required />
          <button type="submit" style={styles.btn} disabled={loading}>
            {loading ? 'جاري...' : isLogin ? 'دخول' : 'تسجيل'}
          </button>
        </form>
        <p style={styles.toggle}>
          {isLogin ? (
            <>
              <button type="button" onClick={() => goTo('register')} style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', fontSize: 14 }}>إنشاء حساب جديد</button>
              <span style={{ margin: '0 8px', color: 'var(--text-muted)' }}>|</span>
              <button type="button" onClick={() => goTo('forgot')} style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', fontSize: 14 }}>نسيت كلمة المرور</button>
            </>
          ) : (
            <button type="button" onClick={() => goTo('login')} style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', fontSize: 14 }}>لديك حساب؟ تسجيل الدخول</button>
          )}
        </p>
      </div>
    </div>
  );
}
