import { useState, useEffect } from 'react';
import * as api from './api';
import ReminderForm from './ReminderForm';

const styles = {
  page: { maxWidth: 560, margin: '0 auto', padding: 16, paddingBottom: 32 },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 },
  title: { fontSize: 20, fontWeight: 700 },
  btn: {
    padding: '8px 14px',
    border: 'none',
    borderRadius: 8,
    background: 'rgba(255,255,255,0.1)',
    color: 'var(--text)',
    fontSize: 14
  },
  err: { color: 'var(--danger)', marginBottom: 12, textAlign: 'center' },
  list: { display: 'flex', flexDirection: 'column', gap: 12 },
  card: {
    background: 'var(--surface)',
    borderRadius: 'var(--radius)',
    padding: 16,
    border: '1px solid rgba(255,255,255,0.08)'
  },
  cardTitle: { fontWeight: 600, marginBottom: 4 },
  cardBody: { color: 'var(--text-muted)', fontSize: 14, marginBottom: 8 },
  cardTime: { fontSize: 13, color: 'var(--primary-light)' },
  cardNotes: { fontSize: 13, color: 'var(--text-muted)', marginTop: 6, paddingRight: 4, borderRight: '2px solid var(--primary)', fontStyle: 'italic' },
  actions: { marginTop: 12, display: 'flex', gap: 8 },
  editBtn: { padding: '6px 12px', borderRadius: 8, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 13 },
  delBtn: { padding: '6px 12px', borderRadius: 8, border: 'none', background: 'rgba(199,92,92,0.3)', color: '#e88', fontSize: 13 },
  notesToggle: { background: 'none', border: 'none', color: 'var(--primary-light)', cursor: 'pointer', padding: '6px 0', fontSize: 13, textAlign: 'right', width: '100%' },
  notesBox: { marginTop: 8, paddingTop: 8, borderTop: '1px solid rgba(255,255,255,0.08)' },
  notesTextarea: { width: '100%', padding: 10, marginBottom: 8, border: '1px solid rgba(255,255,255,0.15)', borderRadius: 8, background: 'rgba(0,0,0,0.2)', color: 'var(--text)', fontSize: 14, minHeight: 70, resize: 'vertical' },
  notesQuick: { display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 8 },
  notesQuickBtn: { padding: '6px 10px', borderRadius: 6, border: 'none', background: 'rgba(255,255,255,0.1)', color: 'var(--text)', fontSize: 12, cursor: 'pointer' },
  notesSave: { padding: '6px 12px', borderRadius: 8, border: 'none', background: 'var(--primary)', color: '#fff', fontSize: 13 }
};

function formatDateTime(iso) {
  const d = new Date(iso);
  return d.toLocaleString('ar-EG', {
    dateStyle: 'short',
    timeStyle: 'short'
  });
}

function todayStr() {
  return new Date().toLocaleDateString('ar-EG', { dateStyle: 'short' });
}

export default function RemindersList({ user, reminders, error, isAdmin, onLogout, onRefresh, onError, onClearFired, onTestNotification, pushStatus, pushFailReason, onRetryPush, onAdd, onUpdate, onDelete }) {
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [openNotesId, setOpenNotesId] = useState(null);
  const [notesDraft, setNotesDraft] = useState({});
  const [inviteModal, setInviteModal] = useState(null);
  const [inviteLoading, setInviteLoading] = useState(false);
  const [blockedModal, setBlockedModal] = useState(false);
  const [blockedUsers, setBlockedUsers] = useState([]);
  const [blockUserModal, setBlockUserModal] = useState(false);
  const [allUsers, setAllUsers] = useState([]);
  const [serverUrlInput, setServerUrlInput] = useState(() => api.getApiBase());

  useEffect(() => {
    setServerUrlInput(api.getApiBase());
  }, [error]); // تحديث الحقل عند ظهور خطأ (مثلاً بعد إعادة المحاولة)

  const handleSaveServerUrl = () => {
    api.setApiBase(serverUrlInput);
    if (onRefresh) onRefresh();
  };

  const handleSave = async (payload) => {
    if (editing) {
      await onUpdate(editing.id, payload);
      setEditing(null);
    } else {
      await onAdd(payload);
      setShowForm(false);
    }
  };

  const handleCreateInvite = async () => {
    if (inviteLoading) return;
    setInviteLoading(true);
    if (onError) onError('');
    try {
      const data = await api.createInviteLink();
      const link = window.location.origin + '/invite/' + (data.token || '');
      setInviteModal({ link, copied: false });
    } catch (e) {
      if (onError) onError(e.message || 'فشل إنشاء الرابط');
    } finally {
      setInviteLoading(false);
    }
  };

  const copyInviteLink = () => {
    if (inviteModal?.link) {
      navigator.clipboard?.writeText(inviteModal.link).then(() => setInviteModal((p) => (p ? { ...p, copied: true } : null)));
    }
  };

  const loadBlocked = async () => {
    try {
      const list = await api.getBlockedUsers();
      setBlockedUsers(list);
      if (onError) onError('');
    } catch (e) {
      if (onError) onError(e.message || 'غير مصرح');
      setBlockedUsers([]);
    }
  };

  const loadAllUsers = async () => {
    try {
      const list = await api.getAllUsers();
      setAllUsers(list);
      if (onError) onError('');
    } catch (e) {
      if (onError) onError(e.message || 'غير مصرح');
      setAllUsers([]);
    }
  };

  const handleBlock = async (targetId) => {
    if (!confirm('إيقاف وصول هذا المستخدم؟')) return;
    try {
      await api.blockUser(targetId);
      setBlockedUsers((prev) => [...prev, allUsers.find((u) => u.id === targetId)].filter(Boolean));
      setAllUsers((prev) => prev.filter((u) => u.id !== targetId));
    } catch (e) {
      if (onError) onError(e.message || 'فشل');
    }
  };

  const handleUnblock = async (targetId) => {
    try {
      await api.unblockUser(targetId);
      setBlockedUsers((prev) => prev.filter((u) => u.id !== targetId));
    } catch (e) {
      if (onError) onError(e.message || 'فشل');
    }
  };

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <h1 style={styles.title}>Karas — تنبيهات</h1>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          {isAdmin && (
            <>
              <button type="button" style={{ ...styles.btn, background: 'var(--primary)', color: '#fff' }} onClick={handleCreateInvite} disabled={inviteLoading} title="رابط للآيفون والأندرويد">{inviteLoading ? '...' : '📱 رابط دعوة (آيفون/أندرويد)'}</button>
              <button type="button" style={styles.btn} onClick={() => { setBlockedModal(true); loadBlocked(); }}>الموقوفون</button>
              <button type="button" style={{ ...styles.btn, background: 'rgba(248,81,73,0.2)', color: '#f85149' }} onClick={() => { setBlockUserModal(true); loadAllUsers(); loadBlocked(); }}>إيقاف مستخدم</button>
            </>
          )}
          <button type="button" style={styles.btn} onClick={onRefresh}>تحديث</button>
          <button type="button" style={styles.btn} onClick={onLogout}>خروج</button>
        </div>
      </header>
      {isAdmin && (
        <p style={{ fontSize: 12, color: 'var(--primary-light)', marginBottom: 8, padding: '6px 10px', background: 'rgba(26,95,74,0.15)', borderRadius: 8, display: 'inline-block' }}>✓ مسؤول — يمكنك استخدام رابط الدعوة وإيقاف المستخدمين</p>
      )}
      <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16 }}>
        مرحباً، {user?.name || user?.email}. التنبيهات تظهر مكتوبة ويُقرأ نصها بصوت افتراضي عند وقت التذكير.
        جميع التنبيهات تبقى في القائمة ولا تُحذف تلقائياً؛ يمكنك حذف أي تنبيه يدوياً بزر «حذف».
        لو لم يظهر تنبيه: اسمح بالإشعارات، أو اضغط «تحديث» بعد وقت التنبيه. لو استمرت المشكلة اضغط «مسح سجل التنبيهات» ثم حدّث.
        <span style={{ display: 'block', marginTop: 6, fontSize: 11, opacity: 0.7 }}>نسخة واجهة: 3</span>
      </p>
      {pushStatus !== null && (
        <div style={{ fontSize: 13, marginBottom: 10 }}>
          {pushStatus === 'ok' ? (
            <span style={{ color: 'var(--primary-light)' }}>التنبيه مع الشاشة مطفية: مفعّل.</span>
          ) : (
            <div>
              <span style={{ color: 'var(--text-muted)' }}>التنبيه مع الشاشة مطفية غير مفعّل. </span>
              {pushFailReason && (
                <span style={{ display: 'block', fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>{pushFailReason}</span>
              )}
              {onRetryPush && (
                <button type="button" style={{ ...styles.btn, marginTop: 6 }} onClick={onRetryPush}>
                  إعادة المحاولة
                </button>
              )}
            </div>
          )}
        </div>
      )}
      {onClearFired && (
        <button type="button" style={{ ...styles.btn, marginBottom: 8, fontSize: 12 }} onClick={onClearFired}>
          مسح سجل التنبيهات (للاختبار)
        </button>
      )}
      {onTestNotification && reminders.length > 0 && (
        <button
          type="button"
          style={{ ...styles.btn, marginBottom: 12, fontSize: 12, border: '1px solid var(--primary)' }}
          onClick={() => onTestNotification(reminders[0])}
        >
          تجربة تنبيه الآن (أول تنبيه في القائمة)
        </button>
      )}
      {error && <p style={styles.err}>{error}</p>}

      <div style={{ marginBottom: 16, padding: 12, background: 'rgba(255,255,255,0.05)', borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)' }}>
        <label style={{ display: 'block', fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>رابط السيرفر (Backend)</label>
        <input
          type="url"
          value={serverUrlInput}
          onChange={(e) => setServerUrlInput(e.target.value)}
          placeholder="https://your-backend.onrender.com"
          style={{ width: '100%', padding: 10, marginBottom: 8, border: '1px solid rgba(255,255,255,0.2)', borderRadius: 8, background: 'rgba(0,0,0,0.2)', color: 'var(--text)', fontSize: 14, boxSizing: 'border-box' }}
        />
        <button type="button" style={{ ...styles.btn, background: 'var(--primary)', color: '#fff' }} onClick={handleSaveServerUrl}>
          حفظ واختبار
        </button>
      </div>

      {!showForm && !editing && (
        <button style={{ ...styles.btn, width: '100%', padding: 14, marginBottom: 20 }} onClick={() => setShowForm(true)}>
          + إضافة تنبيه
        </button>
      )}

      {(showForm || editing) && (
        <ReminderForm
          initial={editing ? { title: editing.title, body: editing.body, remind_at: editing.remind_at, repeat: editing.repeat, notes: editing.notes } : null}
          onSave={handleSave}
          onCancel={() => { setShowForm(false); setEditing(null); }}
        />
      )}

      <div style={styles.list}>
        {reminders.length === 0 && !showForm && (
          <p style={{ color: 'var(--text-muted)', textAlign: 'center', marginTop: 24 }}>لا توجد تنبيهات. أضف تنبيهاً أولاً.</p>
        )}
        {reminders.map((r) => {
          const isNotesOpen = openNotesId === r.id;
          const draft = notesDraft[r.id] !== undefined ? notesDraft[r.id] : (r.notes || '');
          return (
            <div key={r.id} style={styles.card}>
              <div style={styles.cardTitle}>{r.title}</div>
              {r.body && <div style={styles.cardBody}>{r.body}</div>}
              <div style={styles.cardTime}>{formatDateTime(r.remind_at)} {r.repeat ? ` • ${r.repeat}` : ''}</div>
              {r.notes && r.notes.trim() && (
                <div style={styles.cardNotes}>ملاحظات: {r.notes.trim()}</div>
              )}
              <button
                type="button"
                style={styles.notesToggle}
                onClick={() => {
                  setOpenNotesId((prev) => (prev === r.id ? null : r.id));
                  if (openNotesId !== r.id) setNotesDraft((d) => ({ ...d, [r.id]: r.notes || '' }));
                }}
              >
                {isNotesOpen ? '▼ ملاحظات (حالة التنبيه)' : '▶ ملاحظات (حالة التنبيه)'} {r.notes ? '— مُضافة' : ''}
              </button>
              {isNotesOpen && (
                <div style={styles.notesBox}>
                  <textarea
                    value={draft}
                    onChange={(e) => setNotesDraft((d) => ({ ...d, [r.id]: e.target.value }))}
                    placeholder="مثال: تم الإرسال بتاريخ ... أو لم يتم الإرسال بعد"
                    style={styles.notesTextarea}
                    rows={3}
                  />
                  <div style={styles.notesQuick}>
                    <button type="button" style={styles.notesQuickBtn} onClick={() => setNotesDraft((d) => ({ ...d, [r.id]: `تم الإرسال بتاريخ ${todayStr()}` }))}>
                      تم الإرسال بتاريخ {todayStr()}
                    </button>
                    <button type="button" style={styles.notesQuickBtn} onClick={() => setNotesDraft((d) => ({ ...d, [r.id]: 'لم يتم الإرسال بعد' }))}>
                      لم يتم الإرسال بعد
                    </button>
                  </div>
                  <button
                    type="button"
                    style={styles.notesSave}
                    onClick={async () => {
                      await onUpdate(r.id, { notes: notesDraft[r.id] !== undefined ? notesDraft[r.id] : (r.notes || '') });
                      setOpenNotesId(null);
                    }}
                  >
                    حفظ الملاحظات
                  </button>
                </div>
              )}
              <div style={styles.actions}>
                <button style={styles.editBtn} onClick={() => setEditing(r)}>تعديل</button>
                <button style={styles.delBtn} onClick={() => onDelete(r.id)}>حذف</button>
              </div>
            </div>
          );
        })}
      </div>

      {inviteModal && (
        <div onClick={() => setInviteModal(null)} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 20, padding: 16 }}>
          <div onClick={(e) => e.stopPropagation()} style={{ background: 'var(--surface)', borderRadius: 12, padding: 20, maxWidth: 420, width: '100%', maxHeight: '90vh', overflow: 'auto' }}>
            <h3 style={{ marginTop: 0 }}>رابط دعوة — للآيفون والأندرويد</h3>
            <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12 }}>الرابط يعمل على الجهازين. استخدمه مرة واحدة ولا تُشاركه مع أكثر من شخص.</p>
            <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
              <button type="button" onClick={handleCreateInvite} disabled={inviteLoading} style={{ flex: 1, padding: 12, background: inviteLoading ? 'var(--text-muted)' : 'var(--primary)', border: 'none', borderRadius: 8, color: '#fff', cursor: inviteLoading ? 'wait' : 'pointer', fontSize: 14 }}>{inviteLoading ? '...' : '📱 إنشاء رابط للآيفون'}</button>
              <button type="button" onClick={handleCreateInvite} disabled={inviteLoading} style={{ flex: 1, padding: 12, background: inviteLoading ? 'var(--text-muted)' : 'var(--primary)', border: 'none', borderRadius: 8, color: '#fff', cursor: inviteLoading ? 'wait' : 'pointer', fontSize: 14 }}>{inviteLoading ? '...' : '🤖 إنشاء رابط للأندرويد'}</button>
            </div>
            <p style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 8 }}>الرابط نفسه يعمل على الآيفون والأندرويد — اختر حسب من سيرسله له صديقك.</p>
            {inviteModal.link && (
              <>
                <input type="text" readOnly value={inviteModal.link} style={{ width: '100%', padding: 10, border: '1px solid var(--border)', borderRadius: 8, background: 'var(--bg)', color: 'var(--text)', marginBottom: 12, boxSizing: 'border-box' }} />
                <div style={{ background: 'rgba(0,0,0,0.08)', borderRadius: 8, padding: 12, marginBottom: 12, textAlign: 'right' }}>
                  <p style={{ margin: '0 0 8px', fontSize: 13, fontWeight: 600 }}>تعليمات للصديق:</p>
                  <p style={{ margin: 0, fontSize: 12, color: 'var(--text-muted)' }}><strong>آيفون:</strong> اضغط زر المشاركة → إضافة إلى الشاشة الرئيسية → إضافة</p>
                  <p style={{ margin: '4px 0 0', fontSize: 12, color: 'var(--text-muted)' }}><strong>أندرويد:</strong> في Chrome: القائمة ⋮ → إضافة إلى الشاشة الرئيسية → إضافة</p>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button type="button" onClick={copyInviteLink} style={{ flex: 1, padding: 10, background: 'var(--primary)', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer', fontSize: 14 }}>{inviteModal.copied ? 'تم النسخ ✓' : 'نسخ الرابط'}</button>
                  <button type="button" onClick={() => setInviteModal(null)} style={{ padding: 10, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', cursor: 'pointer' }}>إغلاق</button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {blockedModal && (
        <div onClick={() => setBlockedModal(false)} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 20, padding: 16 }}>
          <div onClick={(e) => e.stopPropagation()} style={{ background: 'var(--surface)', borderRadius: 12, padding: 20, maxWidth: 400, width: '100%', maxHeight: '70vh', overflow: 'auto' }}>
            <h3 style={{ marginTop: 0 }}>المستخدمون الموقوفون</h3>
            {blockedUsers.length === 0 ? <p style={{ color: 'var(--text-muted)' }}>لا يوجد موقوفون</p> : blockedUsers.map((u) => (
              <div key={u.id} style={{ padding: '10px 0', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>{u.name || u.email || '—'}</span>
                <button type="button" onClick={() => handleUnblock(u.id)} style={{ padding: '6px 12px', background: 'var(--primary)', border: 'none', borderRadius: 8, color: '#fff', cursor: 'pointer', fontSize: 12 }}>إعادة التفعيل</button>
              </div>
            ))}
            <button type="button" onClick={() => setBlockedModal(false)} style={{ marginTop: 12, padding: '8px 16px' }}>إغلاق</button>
          </div>
        </div>
      )}

      {blockUserModal && (
        <div onClick={() => setBlockUserModal(false)} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 20, padding: 16 }}>
          <div onClick={(e) => e.stopPropagation()} style={{ background: 'var(--surface)', borderRadius: 12, padding: 20, maxWidth: 400, width: '100%', maxHeight: '70vh', overflow: 'auto' }}>
            <h3 style={{ marginTop: 0 }}>إيقاف مستخدم</h3>
            <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12 }}>اختر المستخدم لإيقاف وصوله</p>
            {allUsers.filter((u) => u.id !== user?.id && !blockedUsers.some((b) => b.id === u.id)).length === 0 ? (
              <p style={{ color: 'var(--text-muted)' }}>لا يوجد مستخدمون آخرون</p>
            ) : (
              allUsers.filter((u) => u.id !== user?.id && !blockedUsers.some((b) => b.id === u.id)).map((u) => (
                <div key={u.id} style={{ padding: '10px 0', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>{u.name || u.email || '—'}</span>
                  <button type="button" onClick={() => handleBlock(u.id)} style={{ padding: '6px 12px', background: 'rgba(248,81,73,0.3)', color: '#f85149', border: 'none', borderRadius: 8, cursor: 'pointer', fontSize: 12 }}>إيقاف</button>
                </div>
              ))
            )}
            <button type="button" onClick={() => setBlockUserModal(false)} style={{ marginTop: 12, padding: '8px 16px' }}>إغلاق</button>
          </div>
        </div>
      )}
    </div>
  );
}
