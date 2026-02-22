import { useState } from 'react';
import * as api from './api';

const styles = {
  wrap: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    background: 'linear-gradient(180deg, #0f2e26 0%, #1a3d32 100%)'
  },
  card: {
    width: '100%',
    maxWidth: 360,
    background: 'var(--surface)',
    borderRadius: 'var(--radius)',
    padding: 24,
    boxShadow: '0 8px 32px rgba(0,0,0,0.3)'
  },
  title: { fontSize: 22, fontWeight: 700, marginBottom: 8, textAlign: 'center' },
  sub: { color: 'var(--text-muted)', fontSize: 14, textAlign: 'center', marginBottom: 24 },
  input: {
    width: '100%',
    padding: '12px 14px',
    marginBottom: 12,
    border: '1px solid rgba(255,255,255,0.15)',
    borderRadius: 8,
    background: 'rgba(0,0,0,0.2)',
    color: 'var(--text)',
    fontSize: 16
  },
  btn: {
    width: '100%',
    padding: 14,
    marginTop: 8,
    border: 'none',
    borderRadius: 8,
    background: 'var(--primary)',
    color: '#fff',
    fontSize: 16,
    fontWeight: 600
  },
  link: {
    display: 'block',
    textAlign: 'center',
    marginTop: 16,
    color: 'var(--primary-light)',
    cursor: 'pointer',
    fontSize: 14
  },
  err: { color: 'var(--danger)', fontSize: 14, marginBottom: 12, textAlign: 'center' }
};

export default function Login({ onLogin }) {
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (mode === 'login') {
        const data = await api.login(email, password);
        onLogin(data);
      } else {
        const data = await api.register(email, password, name);
        onLogin(data);
      }
    } catch (e) {
      setError(e.message || 'حدث خطأ');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.wrap}>
      <div style={styles.card}>
        <h1 style={styles.title}>تنبيهاتي</h1>
        <p style={styles.sub}>
          {mode === 'login' ? 'سجّل الدخول للمزامنة بين الموبايل والكمبيوتر' : 'إنشاء حساب جديد'}
        </p>
        {error && <p style={styles.err}>{error}</p>}
        <form onSubmit={submit}>
          <input
            type="email"
            placeholder="البريد الإلكتروني"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={styles.input}
            required
            autoComplete="email"
          />
          <input
            type="password"
            placeholder="كلمة المرور"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={styles.input}
            required
            autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
          />
          {mode === 'register' && (
            <input
              type="text"
              placeholder="الاسم (اختياري)"
              value={name}
              onChange={(e) => setName(e.target.value)}
              style={styles.input}
              autoComplete="name"
            />
          )}
          <button type="submit" style={styles.btn} disabled={loading}>
            {loading ? 'جاري...' : mode === 'login' ? 'تسجيل الدخول' : 'إنشاء الحساب'}
          </button>
        </form>
        <button type="button" style={styles.link} onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>
          {mode === 'login' ? 'إنشاء حساب جديد' : 'لديك حساب؟ تسجيل الدخول'}
        </button>
      </div>
    </div>
  );
}
