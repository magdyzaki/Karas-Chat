import { useState } from 'react';
import * as api from './api';

export default function Auth({ onLogin }) {
  const [mode, setMode] = useState('login');
  const [emailOrPhone, setEmailOrPhone] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (mode === 'register') {
        const data = await api.register(emailOrPhone, password, name);
        if (data.token) {
          localStorage.setItem('chat_token', data.token);
          localStorage.setItem('chat_user', JSON.stringify(data.user));
          onLogin(data);
        } else if (data.needsVerification) {
          setMode('verify');
        } else {
          setError(data.msg || 'تم التسجيل');
        }
      } else if (mode === 'verify') {
        const data = await api.verify(emailOrPhone, code);
        localStorage.setItem('chat_token', data.token);
        localStorage.setItem('chat_user', JSON.stringify(data.user));
        onLogin(data);
      } else {
        const data = await api.login(emailOrPhone, password);
        localStorage.setItem('chat_token', data.token);
        localStorage.setItem('chat_user', JSON.stringify(data.user));
        onLogin(data);
      }
    } catch (err) {
      setError(err.message || 'خطأ');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20, background: '#0d1117', direction: 'rtl' }}>
      <div style={{ width: '100%', maxWidth: 360, background: '#161b22', borderRadius: 12, padding: 24, border: '1px solid #30363d' }}>
        <h1 style={{ textAlign: 'center', margin: '0 0 24px', color: '#fff', fontSize: 24 }}>Karas شات</h1>
        <form onSubmit={handleSubmit}>
          {mode !== 'verify' && (
            <>
              <input type="text" placeholder="البريد أو رقم الموبايل" value={emailOrPhone} onChange={(e) => setEmailOrPhone(e.target.value)} required style={{ width: '100%', padding: 12, marginBottom: 12, border: '1px solid #30363d', borderRadius: 8, background: '#0d1117', color: '#fff', boxSizing: 'border-box' }} />
              {mode === 'register' && (
                <input type="text" placeholder="الاسم" value={name} onChange={(e) => setName(e.target.value)} style={{ width: '100%', padding: 12, marginBottom: 12, border: '1px solid #30363d', borderRadius: 8, background: '#0d1117', color: '#fff', boxSizing: 'border-box' }} />
              )}
              <input type="password" placeholder="كلمة المرور" value={password} onChange={(e) => setPassword(e.target.value)} required style={{ width: '100%', padding: 12, marginBottom: 12, border: '1px solid #30363d', borderRadius: 8, background: '#0d1117', color: '#fff', boxSizing: 'border-box' }} />
            </>
          )}
          {mode === 'verify' && (
            <input type="text" placeholder="رمز التحقق (6 أرقام)" value={code} onChange={(e) => setCode(e.target.value)} maxLength={6} required style={{ width: '100%', padding: 12, marginBottom: 12, border: '1px solid #30363d', borderRadius: 8, background: '#0d1117', color: '#fff', boxSizing: 'border-box' }} />
          )}
          {error && <p style={{ color: '#f85149', fontSize: 14, marginBottom: 12 }}>{error}</p>}
          <button type="submit" disabled={loading} style={{ width: '100%', padding: 12, background: '#238636', border: 'none', borderRadius: 8, color: '#fff', fontSize: 16, cursor: loading ? 'not-allowed' : 'pointer' }}>{loading ? '...' : mode === 'register' ? 'تسجيل' : mode === 'verify' ? 'تأكيد' : 'دخول'}</button>
        </form>
        <p style={{ textAlign: 'center', marginTop: 16, color: '#8b949e', fontSize: 14 }}>
          {mode === 'login' ? (
            <span onClick={() => setMode('register')} style={{ cursor: 'pointer', color: '#58a6ff' }}>إنشاء حساب</span>
          ) : mode === 'verify' ? (
            <span onClick={() => setMode('login')} style={{ cursor: 'pointer', color: '#58a6ff' }}>رجوع</span>
          ) : (
            <span onClick={() => setMode('login')} style={{ cursor: 'pointer', color: '#58a6ff' }}>لديك حساب؟ ادخل</span>
          )}
        </p>
      </div>
    </div>
  );
}
