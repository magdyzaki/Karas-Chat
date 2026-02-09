import { useState, useEffect, useRef } from 'react';

const styles = {
  form: { background: 'var(--surface)', borderRadius: 'var(--radius)', padding: 20, marginBottom: 20 },
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
  inputWrap: { display: 'flex', alignItems: 'stretch', gap: 8, marginBottom: 12 },
  inputFlex: { flex: 1 },
  micBtn: {
    padding: '12px 14px',
    border: '1px solid rgba(255,255,255,0.15)',
    borderRadius: 8,
    background: 'rgba(0,0,0,0.2)',
    color: 'var(--text)',
    cursor: 'pointer',
    fontSize: 18
  },
  row: { display: 'flex', gap: 12, marginBottom: 12 },
  btn: { padding: '10px 18px', borderRadius: 8, border: 'none', fontSize: 15, fontWeight: 600 },
  primary: { background: 'var(--primary)', color: '#fff' },
  secondary: { background: 'rgba(255,255,255,0.1)', color: 'var(--text)' }
};

const SpeechRecognition = typeof window !== 'undefined' && (window.SpeechRecognition || window.webkitSpeechRecognition);

function toLocalISO(d) {
  const t = new Date(d);
  const offset = t.getTimezoneOffset() * 60000;
  return new Date(t.getTime() - offset).toISOString().slice(0, 16);
}

export default function ReminderForm({ initial, onSave, onCancel }) {
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [remind_at, setRemind_at] = useState('');
  const [repeat, setRepeat] = useState('');
  const [listeningFor, setListeningFor] = useState(null);
  const recognitionRef = useRef(null);

  useEffect(() => {
    if (initial) {
      setTitle(initial.title || '');
      setBody(initial.body || '');
      setRemind_at(initial.remind_at ? toLocalISO(initial.remind_at) : '');
      setRepeat(initial.repeat || '');
    } else {
      const next = new Date();
      next.setMinutes(next.getMinutes() + 5);
      setRemind_at(toLocalISO(next));
    }
  }, [initial]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!title.trim()) return;
    // تفسير الوقت كتوقيت محلي دائماً (Safari/موبايل يفسّر "YYYY-MM-DDTHH:mm" كـ UTC فيسبب عدم إطلاق التنبيه)
    const [datePart, timePart] = (remind_at || '').split('T');
    const [y, m, d] = (datePart || '').split('-').map(Number);
    const [h, min] = (timePart || '0:0').split(':').map(Number);
    const localDate = new Date(y, m - 1, d, h, min || 0, 0, 0);
    const at = localDate.toISOString();
    onSave({ title: title.trim(), body: body.trim(), remind_at: at, repeat: repeat.trim() || null });
  };

  const startVoice = (field) => {
    if (!SpeechRecognition) return;
    if (recognitionRef.current) try { recognitionRef.current.stop(); } catch (_) {}
    const rec = new SpeechRecognition();
    rec.lang = 'ar-SA';
    rec.continuous = false;
    rec.interimResults = false;
    rec.onresult = (e) => {
      const text = (e.results[0] && e.results[0][0] && e.results[0][0].transcript) || '';
      if (field === 'title') setTitle((prev) => (prev ? prev + ' ' + text : text));
      else setBody((prev) => (prev ? prev + ' ' + text : text));
    };
    rec.onend = () => setListeningFor(null);
    rec.onerror = () => setListeningFor(null);
    recognitionRef.current = rec;
    setListeningFor(field);
    rec.start();
  };

  return (
    <form style={styles.form} onSubmit={handleSubmit}>
      <div style={styles.inputWrap}>
        <input
          type="text"
          placeholder="عنوان التنبيه"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          style={{ ...styles.input, ...styles.inputFlex, marginBottom: 0 }}
          required
        />
        {SpeechRecognition && (
          <button
            type="button"
            style={{ ...styles.micBtn, background: listeningFor === 'title' ? 'var(--primary)' : undefined }}
            onClick={() => startVoice('title')}
            title="تحدث لكتابة النص"
          >
            🎤
          </button>
        )}
      </div>
      <div style={styles.inputWrap}>
        <textarea
          placeholder="نص التنبيه (يُقرأ بصوت افتراضي عند التذكير)"
          value={body}
          onChange={(e) => setBody(e.target.value)}
          style={{ ...styles.input, ...styles.inputFlex, minHeight: 80, resize: 'vertical', marginBottom: 0 }}
          rows={3}
        />
        {SpeechRecognition && (
          <button
            type="button"
            style={{ ...styles.micBtn, background: listeningFor === 'body' ? 'var(--primary)' : undefined }}
            onClick={() => startVoice('body')}
            title="تحدث لكتابة النص"
          >
            🎤
          </button>
        )}
      </div>
      <input
        type="datetime-local"
        value={remind_at}
        onChange={(e) => setRemind_at(e.target.value)}
        style={styles.input}
        required
      />
      <label style={{ display: 'block', marginBottom: 6, fontSize: 14, color: 'var(--text-muted)' }}>التكرار</label>
      <select
        value={repeat}
        onChange={(e) => setRepeat(e.target.value)}
        style={styles.input}
      >
        <option value="">بدون تكرار</option>
        <option value="كل ساعة">كل ساعة</option>
        <option value="كل يوم">كل يوم</option>
        <option value="كل أسبوع">كل أسبوع</option>
        <option value="كل شهر">كل شهر</option>
      </select>
      <div style={styles.row}>
        <button type="submit" style={{ ...styles.btn, ...styles.primary }}>حفظ</button>
        <button type="button" style={{ ...styles.btn, ...styles.secondary }} onClick={onCancel}>إلغاء</button>
      </div>
    </form>
  );
}
