/** أصوات التطبيق - رسائل، اتصالات، تنبيهات */

let ringAudio = null;

function getAudioContext() {
  if (typeof window === 'undefined') return null;
  return new (window.AudioContext || window.webkitAudioContext)();
}

function playTone(freq, duration, type = 'sine', volume = 0.2) {
  try {
    const ctx = getAudioContext();
    if (!ctx) return;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.type = type;
    osc.frequency.setValueAtTime(freq, ctx.currentTime);
    gain.gain.setValueAtTime(volume, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + duration);
    osc.start(ctx.currentTime);
    osc.stop(ctx.currentTime + duration);
  } catch (_) {}
}

export function playSent() {
  playTone(800, 0.08, 'sine', 0.15);
  setTimeout(() => playTone(1000, 0.06, 'sine', 0.12), 60);
}

export function playReceived() {
  playTone(600, 0.1, 'sine', 0.2);
  setTimeout(() => playTone(900, 0.08, 'sine', 0.15), 80);
}

export function playTyping() {
  playTone(400, 0.04, 'sine', 0.08);
}

let ringInterval = null;

export function playCallRing() {
  stopCallRing();
  const ctx = getAudioContext();
  if (!ctx) return;
  const playOne = () => {
    playTone(800, 0.3, 'sine', 0.25);
    setTimeout(() => playTone(1000, 0.3, 'sine', 0.2), 200);
  };
  playOne();
  ringInterval = setInterval(playOne, 1500);
}

export function stopCallRing() {
  if (ringInterval) {
    clearInterval(ringInterval);
    ringInterval = null;
  }
  if (ringAudio) {
    try { ringAudio.pause(); ringAudio.currentTime = 0; } catch (_) {}
    ringAudio = null;
  }
}

export function playNotification() {
  playReceived();
}
