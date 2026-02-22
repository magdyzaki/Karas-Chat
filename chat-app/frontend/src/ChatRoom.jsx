import { useState, useEffect, useRef, useMemo } from 'react';
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
  input: { flex: 1, padding: '10px 14px', border: '1px solid var(--border)', borderRadius: 8, background: 'var(--bg)', color: 'var(--text)', fontSize: 15, minHeight: 44, textAlign: 'right' },
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
  const [optimisticVersion, setOptimisticVersion] = useState(0);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const optimisticRef = useRef([]);

  useEffect(() => {
    if (!conversation?.id) return;
    optimisticRef.current = [];
    setLoading(true);
    api.getMessages(conversation.id).then((list) => {
      const safeList = Array.isArray(list) ? list : [];
      setMessages(safeList);
      setLoading(false);
    }).catch(() => {
      setLoading(false);
    });
    if (socket) {
      socket.emit('join_conversation', conversation.id);
      const onNew = (msg) => {
        if (msg.conversation_id !== conversation.id) return;
        optimisticRef.current = optimisticRef.current.filter(
          (o) => !(o.content === msg.content && o.sender_id === msg.sender_id && o.type === msg.type)
        );
        setOptimisticVersion((v) => v + 1);
        setMessages((prev) => [...prev, msg]);
      };
      socket.on('new_message', onNew);
      return () => {
        socket.off('new_message', onNew);
        socket.emit('leave_conversation', conversation.id);
      };
    }
  }, [conversation?.id, socket]);

  const displayMessages = useMemo(() => {
    const fromServer = messages || [];
    const pending = optimisticRef.current || [];
    const serverIds = new Set(fromServer.map((m) => m.id));
    const extra = pending.filter((p) => !serverIds.has(p.id));
    return [...fromServer, ...extra].sort((a, b) => new Date(a.created_at || 0) - new Date(b.created_at || 0));
  }, [messages, optimisticVersion]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [displayMessages]);

  const sendMessage = (type = 'text', content, file_name = null) => {
    if (!content && type === 'text') return;
    const tempId = 'temp-' + Date.now();
    const tempMsg = {
      id: tempId,
      content,
      sender_id: currentUserId,
      type: type === 'text' ? 'text' : type,
      file_name: file_name || null,
      created_at: new Date().toISOString(),
      sender: null
    };
    optimisticRef.current = [...optimisticRef.current, tempMsg];
    setOptimisticVersion((v) => v + 1);
    if (type === 'text') setText('');
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
    <div className="chat-room-inner" style={styles.room}>
      <div style={styles.header}>
        <button type="button" style={styles.backBtn} onClick={onBack}>← رجوع</button>
        <span style={{ fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1, minWidth: 0 }}>{conversation.label || conversation.name || 'محادثة'}</span>
      </div>
      <div className="chat-msg-area" style={styles.messages}>
        {loading && <p style={{ color: 'var(--text-muted)' }}>جاري التحميل...</p>}
        {displayMessages.map((m) => {
          const isOwn = Number(m.sender_id) === Number(currentUserId);
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
        className="chat-form-row"
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
