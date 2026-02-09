import { useState, useEffect, useCallback, useRef } from 'react';
import { requestNotificationPermission, showReminderNotification, subscribeToPush } from './notifications';
import * as api from './api';
import Login from './Login';
import RemindersList from './RemindersList';

const POLL_MS = 60 * 1000; // كل دقيقة جلب من السيرفر
const CHECK_INTERVAL_MS = 2 * 1000; // كل 2 ثانية (موبايل يبطّئ الفواصل فنجعلها قصيرة)

function App() {
  const [user, setUser] = useState(null);
  const [reminders, setReminders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [lastFired, setLastFired] = useState(null); // تنبيه ظهر الآن (داخل الصفحة لو الإشعار مرفوض)
  const [firedIds, setFiredIds] = useState(() => {
    try {
      return new Set(JSON.parse(localStorage.getItem('reminders_fired') || '[]'));
    } catch (_) {
      return new Set();
    }
  });
  const remindersRef = useRef(reminders);
  const firedIdsRef = useRef(firedIds);
  remindersRef.current = reminders;
  firedIdsRef.current = firedIds;

  const token = typeof localStorage !== 'undefined' ? localStorage.getItem('reminders_token') : null;
  const savedUser = typeof localStorage !== 'undefined' ? localStorage.getItem('reminders_user') : null;

  useEffect(() => {
    if (savedUser && token) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (_) {
        localStorage.removeItem('reminders_user');
        localStorage.removeItem('reminders_token');
      }
    }
    setLoading(false);
  }, [token, savedUser]);

  const fetchReminders = useCallback(async () => {
    if (!token) return;
    try {
      const list = await api.getReminders();
      setReminders(list);
      setError('');
    } catch (e) {
      setError(e.message || 'خطأ في التحميل');
      if (e.message && e.message.includes('انتهت الجلسة')) {
        localStorage.removeItem('reminders_token');
        localStorage.removeItem('reminders_user');
        setUser(null);
      }
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (!user) return;
    setLoading(true);
    fetchReminders();
  }, [user, fetchReminders]);

  // الاشتراك في Push مرة واحدة بعد الدخول (حتى يعمل التنبيه مع الشاشة مطفية)
  useEffect(() => {
    if (!user || !token) return;
    subscribeToPush(api.getVapidPublic, api.subscribePush);
  }, [user, token]);

  // التحقق من مواعيد التنبيهات وإطلاق الإشعار + TTS (عند كل تحديث للقائمة أو السجل)
  useEffect(() => {
    if (!reminders.length) return;
    const nowMs = Date.now();
    const toFire = [];
    reminders.forEach((r) => {
      const id = Number(r.id);
      if (firedIds.has(id)) return;
      const remindAtMs = new Date(r.remind_at).getTime();
      if (Number.isNaN(remindAtMs)) return;
      if (remindAtMs <= nowMs) toFire.push(r);
    });
    if (toFire.length === 0) return;
    toFire.forEach((r) => {
      showReminderNotification(r.title, r.body || '');
      setLastFired({ title: r.title, body: r.body || '' });
    });
    setFiredIds((prev) => {
      const next = new Set(prev);
      toFire.forEach((r) => next.add(Number(r.id)));
      try {
        localStorage.setItem('reminders_fired', JSON.stringify([...next]));
      } catch (_) {}
      return next;
    });
  }, [reminders, firedIds]);

  // جلب التنبيهات دورياً للمزامنة
  useEffect(() => {
    if (!user) return;
    const t = setInterval(fetchReminders, POLL_MS);
    return () => clearInterval(t);
  }, [user, fetchReminders]);

  // عند وجود تنبيهات: جلب كل 10 ثوانٍ حتى لا نفوت موعد التنبيه (المتصفح قد يبطّئ setInterval على الموبايل)
  useEffect(() => {
    if (!user || !reminders.length) return;
    const t = setInterval(fetchReminders, 10 * 1000);
    return () => clearInterval(t);
  }, [user, reminders.length, fetchReminders]);

  // عند العودة للصفحة: جلب التنبيهات فوراً (لإطلاق أي تنبيه فات وقته)
  useEffect(() => {
    if (!user) return;
    const onVisible = () => {
      if (document.visibilityState === 'visible') fetchReminders();
    };
    document.addEventListener('visibilitychange', onVisible);
    return () => document.removeEventListener('visibilitychange', onVisible);
  }, [user, fetchReminders]);

  // التحقق كل بضع ثوانٍ من المواعيد وإطلاق التنبيه تلقائياً
  useEffect(() => {
    if (!user || !reminders.length) return;
    const checkAndFire = () => {
      const list = remindersRef.current;
      const fired = firedIdsRef.current;
      const nowMs = Date.now();
      const toFire = [];
      list.forEach((r) => {
        const id = Number(r.id);
        if (fired.has(id)) return;
        const remindAt = new Date(r.remind_at).getTime();
        if (Number.isNaN(remindAt) || remindAt > nowMs) return;
        toFire.push(r);
      });
      if (toFire.length === 0) return;
      toFire.forEach((r) => {
        showReminderNotification(r.title, r.body || '');
        setLastFired({ title: r.title, body: r.body || '' });
      });
      setFiredIds((prev) => {
        const next = new Set(prev);
        toFire.forEach((r) => next.add(Number(r.id)));
        try {
          localStorage.setItem('reminders_fired', JSON.stringify([...next]));
        } catch (_) {}
        return next;
      });
      firedIdsRef.current = new Set(firedIdsRef.current);
      toFire.forEach((r) => firedIdsRef.current.add(Number(r.id)));
    };
    checkAndFire();
    const t = setInterval(checkAndFire, CHECK_INTERVAL_MS);
    return () => clearInterval(t);
  }, [user, reminders]);

  // إخفاء تنبيه الصفحة بعد 10 ثوانٍ
  useEffect(() => {
    if (!lastFired) return;
    const t = setTimeout(() => setLastFired(null), 10 * 1000);
    return () => clearTimeout(t);
  }, [lastFired]);

  const handleLogin = (data) => {
    localStorage.setItem('reminders_token', data.token);
    localStorage.setItem('reminders_user', JSON.stringify(data.user));
    setUser(data.user);
    requestNotificationPermission();
  };

  const handleLogout = () => {
    localStorage.removeItem('reminders_token');
    localStorage.removeItem('reminders_user');
    localStorage.removeItem('reminders_fired');
    setUser(null);
    setReminders([]);
    setFiredIds(new Set());
  };

  const handleAddReminder = async (payload) => {
    const added = await api.addReminder(payload);
    setReminders((prev) => [...prev, added].sort((a, b) => new Date(a.remind_at) - new Date(b.remind_at)));
  };

  const handleUpdateReminder = async (id, payload) => {
    const updated = await api.updateReminder(id, payload);
    setReminders((prev) =>
      prev.map((r) => (r.id === updated.id ? updated : r)).sort((a, b) => new Date(a.remind_at) - new Date(b.remind_at))
    );
  };

  const handleDeleteReminder = async (id) => {
    await api.deleteReminder(id);
    setReminders((prev) => prev.filter((r) => r.id !== id));
    setFiredIds((prev) => {
      const next = new Set(prev);
      next.delete(id);
      localStorage.setItem('reminders_fired', JSON.stringify([...next]));
      return next;
    });
  };

  if (loading && !user) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <p>جاري التحميل...</p>
      </div>
    );
  }

  if (!user) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <>
      {lastFired && (
        <div
          style={{
            position: 'fixed',
            top: 12,
            left: 12,
            right: 12,
            zIndex: 9999,
            background: 'var(--primary)',
            color: '#fff',
            padding: '14px 18px',
            borderRadius: 12,
            boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
            textAlign: 'center'
          }}
        >
          <strong>تنبيه:</strong> {lastFired.title}
          {lastFired.body ? ` — ${lastFired.body}` : ''}
        </div>
      )}
      <RemindersList
        user={user}
        reminders={reminders}
        error={error}
        onLogout={handleLogout}
        onRefresh={fetchReminders}
        onClearFired={() => {
          localStorage.removeItem('reminders_fired');
          setFiredIds(new Set());
        }}
        onTestNotification={async (firstReminder) => {
          if (!firstReminder) return;
          await requestNotificationPermission();
          showReminderNotification(firstReminder.title, firstReminder.body || '');
          setLastFired({ title: firstReminder.title, body: firstReminder.body || '' });
        }}
        onAdd={handleAddReminder}
        onUpdate={handleUpdateReminder}
        onDelete={handleDeleteReminder}
      />
    </>
  );
}

export default App;
