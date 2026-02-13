import { useState, useEffect } from 'react';
import * as api from './api';

export default function PendingCodesModal({ onClose }) {
  const [pendingUsers, setPendingUsers] = useState([]);
  const [codesData, setCodesData] = useState({ verification: {}, reset: {} });
  const [activeTab, setActiveTab] = useState('users');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [approving, setApproving] = useState(null);

  const load = () => {
    setLoading(true);
    setError('');
    Promise.all([
      api.getPendingUsers().then((d) => { setPendingUsers(d.users || []); }).catch((e) => { setError(e.message || 'غير مصرح'); setPendingUsers([]); }),
      api.getPendingCodes().then((d) => { setCodesData(d); }).catch(() => setCodesData({ verification: {}, reset: {} }))
    ]).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleApprove = async (userId) => {
    setApproving(userId);
    try {
      await api.approveUser(userId);
      setPendingUsers((prev) => prev.filter((u) => u.id !== userId));
    } catch (e) {}
    setApproving(null);
  };

  const verification = codesData.verification || {};
  const reset = codesData.reset || {};
  const verificationList = Object.entries(verification).map(([key, v]) => ({ key, ...v, type: 'verification' }));
  const resetList = Object.entries(reset).map(([key, r]) => ({ key, ...r, type: 'reset' }));
  const hasCodes = verificationList.length > 0 || resetList.length > 0;
  const hasUsers = pendingUsers.length > 0;

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: 16 }} onClick={onClose}>
      <div style={{ background: 'var(--surface)', borderRadius: 16, padding: 24, maxWidth: 420, width: '100%', maxHeight: '85vh', overflow: 'auto', border: '1px solid var(--border)' }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <h2 style={{ margin: 0, fontSize: 20 }}>التسجيلات و التفعيل</h2>
          <button type="button" onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 24, cursor: 'pointer', color: 'var(--text)' }}>×</button>
        </div>
        <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
          <button type="button" onClick={() => setActiveTab('users')} style={{ padding: '8px 16px', borderRadius: 8, border: `1px solid ${activeTab === 'users' ? 'var(--primary)' : 'var(--border)'}`, background: activeTab === 'users' ? 'var(--primary)' : 'transparent', color: activeTab === 'users' ? '#fff' : 'var(--text)', cursor: 'pointer', fontSize: 13 }}>مستخدمون بانتظار التفعيل ({pendingUsers.length})</button>
          <button type="button" onClick={() => setActiveTab('codes')} style={{ padding: '8px 16px', borderRadius: 8, border: `1px solid ${activeTab === 'codes' ? 'var(--primary)' : 'var(--border)'}`, background: activeTab === 'codes' ? 'var(--primary)' : 'transparent', color: activeTab === 'codes' ? '#fff' : 'var(--text)', cursor: 'pointer', fontSize: 13 }}>رموز التحقق</button>
        </div>
        {loading ? (
          <p style={{ color: 'var(--text-muted)' }}>جاري التحميل...</p>
        ) : error ? (
          <p style={{ color: '#f85149', fontSize: 14 }}>{error} (هذه الميزة للمسؤول فقط)</p>
        ) : activeTab === 'users' ? (
          <>
            <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 12 }}>اضغط تفعيل لتمكين المستخدم من تسجيل الدخول.</p>
            {!hasUsers ? (
              <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>لا يوجد مستخدمون بانتظار التفعيل.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {pendingUsers.map((u) => (
                  <div key={u.id} style={{ padding: 12, background: 'var(--bg)', borderRadius: 8, border: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
                    <div>
                      <div style={{ fontWeight: 600 }}>{u.name || '—'}</div>
                      <div style={{ fontSize: 12, color: 'var(--text-muted)', direction: 'ltr' }}>{u.phone || u.email || '—'}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>معرف: {u.id}</div>
                    </div>
                    <button type="button" onClick={() => handleApprove(u.id)} disabled={approving === u.id} style={{ padding: '8px 16px', background: 'var(--primary)', border: 'none', borderRadius: 8, color: '#fff', cursor: approving === u.id ? 'wait' : 'pointer', fontSize: 13 }}>{approving === u.id ? '...' : 'تفعيل'}</button>
                  </div>
                ))}
              </div>
            )}
          </>
        ) : !hasCodes ? (
          <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>لا توجد رموز معلقة. (تُستخدم عند تفعيل وضع رمز التحقق وليس وضع الموافقة)</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {verificationList.map((v) => (
              <div key={'v-' + v.key} style={{ padding: 12, background: 'var(--bg)', borderRadius: 8, border: '1px solid var(--border)' }}>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>تأكيد حساب</div>
                <div style={{ fontWeight: 600, direction: 'ltr' }}>{v.key}</div>
                <div style={{ fontSize: 18, color: 'var(--primary)', marginTop: 4, fontFamily: 'monospace' }}>الرمز: {v.code}</div>
              </div>
            ))}
            {resetList.map((r) => (
              <div key={'r-' + r.key} style={{ padding: 12, background: 'var(--bg)', borderRadius: 8, border: '1px solid var(--border)' }}>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>نسيت كلمة المرور</div>
                <div style={{ fontWeight: 600, direction: 'ltr' }}>{r.key}</div>
                <div style={{ fontSize: 18, color: 'var(--primary)', marginTop: 4, fontFamily: 'monospace' }}>الرمز: {r.code}</div>
              </div>
            ))}
          </div>
        )}
        <button type="button" onClick={onClose} style={{ marginTop: 16, padding: '10px 20px', background: 'var(--primary)', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer', fontSize: 14 }}>إغلاق</button>
      </div>
    </div>
  );
}
