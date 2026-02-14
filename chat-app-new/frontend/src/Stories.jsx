import { useState, useEffect, useRef } from 'react';
import * as api from './api';

export default function Stories({ feed = [], currentUserId, onCreateStory, onRefresh }) {
  const [viewing, setViewing] = useState(null);
  const [storyIndex, setStoryIndex] = useState(0);
  const [userIndex, setUserIndex] = useState(0);
  const timeoutRef = useRef(null);

  const allUsers = [{ userId: currentUserId, user: { name: 'قصصي' }, stories: [] }, ...feed];
  const usersWithStories = allUsers.filter((u) => u.stories && u.stories.length > 0);
  const myStories = usersWithStories.find((u) => Number(u.userId) === Number(currentUserId));

  useEffect(() => {
    if (!viewing) return;
    const s = viewing.stories[storyIndex];
    if (!s) return;
    const isVideo = s.type === 'video';
    const dur = isVideo ? 15000 : 5000;
    timeoutRef.current = setTimeout(() => {
      if (storyIndex < viewing.stories.length - 1) setStoryIndex((i) => i + 1);
      else if (userIndex < usersWithStories.length - 1) {
        const next = usersWithStories[userIndex + 1];
        setViewing(next);
        setStoryIndex(0);
        setUserIndex((i) => i + 1);
      } else setViewing(null);
    }, dur);
    return () => clearTimeout(timeoutRef.current);
  }, [viewing, storyIndex, userIndex, usersWithStories.length]);

  const openStory = (userData, idx) => {
    setViewing(userData);
    setStoryIndex(idx);
    setUserIndex(usersWithStories.findIndex((u) => u.userId === userData.userId));
  };

  const closeViewer = () => {
    setViewing(null);
    onRefresh?.();
  };

  return (
    <>
      <div style={{ padding: '10px 12px', borderBottom: '1px solid var(--border)', display: 'flex', gap: 12, overflowX: 'auto', flexShrink: 0 }}>
        <button
          type="button"
          onClick={onCreateStory}
          style={{
            flexShrink: 0,
            width: 56,
            height: 56,
            borderRadius: '50%',
            border: '2px dashed var(--border)',
            background: 'var(--bg)',
            color: 'var(--text)',
            cursor: 'pointer',
            fontSize: 24,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
          title="قصة جديدة"
        >
          +
        </button>
        {usersWithStories.map((u) => (
          <button
            key={u.userId}
            type="button"
            onClick={() => openStory(u, 0)}
            style={{
              flexShrink: 0,
              width: 56,
              height: 56,
              borderRadius: '50%',
              border: '2px solid var(--primary)',
              padding: 2,
              background: 'var(--surface)',
              cursor: 'pointer'
            }}
          >
            <div
              style={{
                width: '100%',
                height: '100%',
                borderRadius: '50%',
                overflow: 'hidden',
                background: 'var(--bg)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 20
              }}
            >
              👤
            </div>
          </button>
        ))}
      </div>
      {viewing && (
        <div
          style={{ position: 'fixed', inset: 0, background: '#000', zIndex: 200, display: 'flex', flexDirection: 'column' }}
          onClick={(e) => e.target === e.currentTarget && closeViewer()}
        >
          <div style={{ padding: 16, display: 'flex', gap: 4 }}>
            {viewing.stories.map((_, i) => (
              <div
                key={i}
                style={{
                  flex: 1,
                  height: 3,
                  background: i < storyIndex ? '#fff' : i === storyIndex ? 'rgba(255,255,255,0.5)' : 'rgba(255,255,255,0.2)',
                  borderRadius: 2
                }}
              />
            ))}
          </div>
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
            {viewing.stories[storyIndex] && (() => {
              const s = viewing.stories[storyIndex];
              if (s.type === 'image') return <img src={(s.content || '').startsWith('http') ? s.content : api.uploadsUrl(s.content)} alt="" style={{ maxWidth: '100%', maxHeight: '80vh', objectFit: 'contain' }} />;
              if (s.type === 'video') return <video src={(s.content || '').startsWith('http') ? s.content : api.uploadsUrl(s.content)} controls autoPlay playsInline style={{ maxWidth: '100%', maxHeight: '80vh' }} />;
              return <div style={{ fontSize: 24, color: '#fff', textAlign: 'center', padding: 20 }}>{s.content}</div>;
            })()}
          </div>
          <div style={{ padding: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ color: '#fff', fontSize: 14 }}>{viewing.user?.name || 'قصة'}</span>
            <button type="button" onClick={closeViewer} style={{ background: 'none', border: 'none', color: '#fff', fontSize: 24, cursor: 'pointer' }}>×</button>
          </div>
        </div>
      )}
    </>
  );
}
