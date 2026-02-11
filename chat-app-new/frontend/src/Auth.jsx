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
  const [isLogin, setIsLogin] = useState(true);
  const [emailOrPhone, setEmailOrPhone] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!emailOrPhone.trim() || !password) {
      setError('البريد أو رقم الموبايل وكلمة المرور مطلوبان');
      return;
    }
    setLoading(true);
    try {
      const data = isLogin ? await api.login(emailOrPhone.trim(), password) : await api.register(emailOrPhone.trim(), password, name);
      onLogin(data);
    } catch (err) {
      setError(err.message || 'حدث خطأ');
    } finally {
      setLoading(false);
    }
  };

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
          <button type="button" onClick={() => { setIsLogin(!isLogin); setError(''); }} style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', fontSize: 14 }}>
            {isLogin ? 'إنشاء حساب جديد' : 'لديك حساب؟ تسجيل الدخول'}
          </button>
        </p>
      </div>
    </div>
  );
}
