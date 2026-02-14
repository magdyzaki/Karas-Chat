import { useState, useEffect, useRef } from 'react';

export default function CallModal({ isVoice, callerName, onAnswer, onReject, onHangup, isOutgoing }) {
  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.85)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', zIndex: 200 }}>
      <div style={{ textAlign: 'center', color: '#fff', marginBottom: 24 }}>
        <p style={{ fontSize: 18, margin: '0 0 8px' }}>{isOutgoing ? 'جاري الاتصال...' : 'مكالمة واردة'}</p>
        <p style={{ fontSize: 14, opacity: 0.9 }}>{callerName || 'شخص'}</p>
        <p style={{ fontSize: 12, opacity: 0.7 }}>{isVoice ? 'مكالمة صوتية' : 'مكالمة فيديو'}</p>
      </div>
      <div style={{ display: 'flex', gap: 16 }}>
        {!isOutgoing && (
          <>
            <button type="button" onClick={onAnswer} style={{ padding: 16, borderRadius: '50%', background: '#22c55e', border: 'none', color: '#fff', cursor: 'pointer', fontSize: 24 }} title="رد">📞</button>
            <button type="button" onClick={onReject} style={{ padding: 16, borderRadius: '50%', background: '#ef4444', border: 'none', color: '#fff', cursor: 'pointer', fontSize: 24 }} title="رفض">📵</button>
          </>
        )}
        {isOutgoing && (
          <button type="button" onClick={onHangup} style={{ padding: 16, borderRadius: '50%', background: '#ef4444', border: 'none', color: '#fff', cursor: 'pointer', fontSize: 24 }} title="إلغاء">📵</button>
        )}
      </div>
    </div>
  );
}
