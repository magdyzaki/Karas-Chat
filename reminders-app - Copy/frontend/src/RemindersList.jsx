import { useState } from 'react';
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

export default function RemindersList({ user, reminders, error, onLogout, onRefresh, onClearFired, onTestNotification, pushStatus, pushFailReason, onRetryPush, onAdd, onUpdate, onDelete }) {
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [openNotesId, setOpenNotesId] = useState(null);
  const [notesDraft, setNotesDraft] = useState({});

  const handleSave = async (payload) => {
    if (editing) {
      await onUpdate(editing.id, payload);
      setEditing(null);
    } else {
      await onAdd(payload);
      setShowForm(false);
    }
  };

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <h1 style={styles.title}>Karas — تنبيهات</h1>
        <div style={{ display: 'flex', gap: 8 }}>
          <button style={styles.btn} onClick={onRefresh}>تحديث</button>
          <button style={styles.btn} onClick={onLogout}>خروج</button>
        </div>
      </header>
      <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16 }}>
        مرحباً، {user?.name || user?.email}. التنبيهات تظهر مكتوبة ويُقرأ نصها بصوت افتراضي عند وقت التذكير.
        جميع التنبيهات تبقى في القائمة ولا تُحذف تلقائياً؛ يمكنك حذف أي تنبيه يدوياً بزر «حذف».
        لو لم يظهر تنبيه: اسمح بالإشعارات، أو اضغط «تحديث» بعد وقت التنبيه. لو استمرت المشكلة اضغط «مسح سجل التنبيهات» ثم حدّث.
        <span style={{ display: 'block', marginTop: 6, fontSize: 11, opacity: 0.7 }}>نسخة واجهة: 2</span>
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
    </div>
  );
}
