import { useState, useEffect, useRef } from 'react';
import * as api from './api';

const styles = {
  room: { flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', borderRight: '1px solid var(--border)' },
  header: { padding: 12, borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 12 },
  backBtn: { padding: '6px 12px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', cursor: 'pointer' },
  messages: { flex: 1, overflow: 'auto', padding: 16, display: 'flex', flexDirection: 'column', gap: 8 },
  msg: { maxWidth: '80%', padding: '10px 14px', borderRadius: 12, alignSelf: 'flex-start', wordBreak: 'break-word' },
  msgOwn: { alignSelf: 'flex-end', background: 'var(--primary)', color: '#fff' },
  msgOther: { background: 'var(--surface)', border: '1px solid var(--border)' },
  msgMeta: { fontSize: 11, opacity: 0.8, marginTop: 4 },
  form: { padding: 12, borderTop: '1px solid var(--border)', display: 'flex', gap: 8, alignItems: 'flex-end' },
  input: { flex: 1, padding: '10px 14px', border: '1px solid var(--border)', borderRadius: 8, background: 'var(--bg)', color: 'var(--text)', fontSize: 15, minHeight: 44 },
  sendBtn: { padding: '10px 20px', border: 'none', borderRadius: 8, background: 'var(--primary)', color: '#fff', cursor: 'pointer', fontSize: 15 },
  fileBtn: { padding: '10px 14px', border: '1px solid var(--border)', borderRadius: 8, background: 'var(--surface)', color: 'var(--text)', cursor: 'pointer' },
  img: { maxWidth: '100%', maxHeight: 200, borderRadius: 8, marginTop: 4 },
  link: { color: 'var(--primary)', wordBreak: 'break-all' }
};

export default function ChatRoom({ conversation, socket, currentUserId, onBack }) {
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(true);
  const [fileError, setFileError] = useState('');
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (!conversation?.id) return;
    setLoading(true);
    api.getMessages(conversation.id).then((list) => {
      setMessages((prev) => {
        const temps = prev.filter((m) => m.id && String(m.id).startsWith('temp-'));
        return temps.length ? [...list, ...temps] : list;
      });
      setLoading(false);
    }).catch(() => {
      setLoading(false);
      setMessages((prev) => prev.filter((m) => m.id && String(m.id).startsWith('temp-'))); // إبقاء المؤقتة فقط
    });
    if (socket) {
      socket.emit('join_conversation', conversation.id);
      const onNew = (msg) => {
        if (msg.conversation_id !== conversation.id) return;
        setMessages((prev) => {
          const withoutTemp = prev.filter((m) => !(m.id && String(m.id).startsWith('temp-') && m.content === msg.content && m.sender_id === msg.sender_id && m.type === msg.type));
          return [...withoutTemp, msg];
        });
      };
      socket.on('new_message', onNew);
      return () => {
        socket.off('new_message', onNew);
        socket.emit('leave_conversation', conversation.id);
      };
    }
  }, [conversation?.id, socket]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = (type = 'text', content, file_name = null) => {
    if (!content && type === 'text') return;
    const tempId = 'temp-' + Date.now();
    if (type === 'text') {
      const tempMsg = { id: tempId, content, sender_id: currentUserId, type: 'text', created_at: new Date().toISOString(), sender: null };
      setMessages((prev) => [...prev, tempMsg]);
      setText('');
    } else {
      const tempMsg = { id: tempId, content, sender_id: currentUserId, type, file_name: file_name || null, created_at: new Date().toISOString(), sender: null };
      setMessages((prev) => [...prev, tempMsg]);
    }
    if (socket) socket.emit('send_message', { conversationId: conversation.id, type, content, file_name });
  };

  const handleFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileError('');
    try {
      const { url, filename } = await api.uploadFile(file);
      const fullUrl = api.uploadsUrl(url);
      const type = (file.type || '').startsWith('image/') ? 'image' : 'file';
      sendMessage(type, fullUrl, filename);
    } catch (err) {
      setFileError(err.message || 'فشل رفع الملف');
    }
    e.target.value = '';
  };

  if (!conversation) return null;

  return (
    <div style={styles.room}>
      <div style={styles.header}>
        <button type="button" style={styles.backBtn} onClick={onBack}>← رجوع</button>
        <span style={{ fontWeight: 600 }}>{conversation.label || conversation.name || 'محادثة'}</span>
      </div>
      <div style={styles.messages}>
        {loading && <p style={{ color: 'var(--text-muted)' }}>جاري التحميل...</p>}
        {messages.map((m) => {
          const isOwn = m.sender_id === currentUserId;
          return (
            <div key={m.id} style={{ ...styles.msg, ...(isOwn ? styles.msgOwn : styles.msgOther) }}>
              {!isOwn && m.sender && <div style={{ fontSize: 12, opacity: 0.9 }}>{m.sender.name || m.sender.email || m.sender.phone}</div>}
              {m.type === 'text' && <div>{m.content}</div>}
              {m.type === 'image' && <img src={m.content} alt="" style={styles.img} />}
              {m.type === 'file' && <a href={m.content} target="_blank" rel="noopener noreferrer" style={styles.link}>{m.file_name || 'ملف'}</a>}
              <div style={styles.msgMeta}>{new Date(m.created_at).toLocaleString('ar-EG')}</div>
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>
      {fileError && <p style={{ padding: 8, margin: 0, fontSize: 13, color: '#f85149', background: 'rgba(248,81,73,0.1)' }}>{fileError}</p>}
      <form
        style={styles.form}
        onSubmit={(e) => { e.preventDefault(); sendMessage('text', text.trim()); }}
      >
        <input type="file" ref={fileInputRef} onChange={handleFile} accept="image/*,*" style={{ display: 'none' }} />
        <button type="button" style={styles.fileBtn} onClick={() => fileInputRef.current?.click()}>📎</button>
        <input type="text" placeholder="اكتب رسالة..." value={text} onChange={(e) => setText(e.target.value)} style={styles.input} />
        <button type="submit" style={styles.sendBtn}>إرسال</button>
      </form>
    </div>
  );
}
