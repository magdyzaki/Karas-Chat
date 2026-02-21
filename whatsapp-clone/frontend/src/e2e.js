/**
 * تشفير end-to-end باستخدام Web Crypto API
 * ECDH P-256 + AES-GCM
 */

const E2E_KEYS = 'chat_e2e_keys';

async function generateKeyPair() {
  const pair = await crypto.subtle.generateKey(
    { name: 'ECDH', namedCurve: 'P-256' },
    true,
    ['deriveKey']
  );
  return pair;
}

async function exportPublicKey(keyPair) {
  const exported = await crypto.subtle.exportKey('spki', keyPair.publicKey);
  return btoa(String.fromCharCode(...new Uint8Array(exported)));
}

async function importPublicKey(base64) {
  const bin = Uint8Array.from(atob(base64), (c) => c.charCodeAt(0));
  return crypto.subtle.importKey(
    'spki',
    bin,
    { name: 'ECDH', namedCurve: 'P-256' },
    false,
    []
  );
}

async function exportPrivateKey(keyPair) {
  const exported = await crypto.subtle.exportKey('jwk', keyPair.privateKey);
  return JSON.stringify(exported);
}

async function importPrivateKey(jwkStr) {
  const jwk = JSON.parse(jwkStr);
  return crypto.subtle.importKey(
    'jwk',
    jwk,
    { name: 'ECDH', namedCurve: 'P-256' },
    true,
    ['deriveKey']
  );
}

async function deriveAesKey(privateKey, publicKey) {
  return crypto.subtle.deriveKey(
    { name: 'ECDH', public: publicKey },
    privateKey,
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt', 'decrypt']
  );
}

export async function initE2EKeys() {
  try {
    let stored = localStorage.getItem(E2E_KEYS);
    if (stored) {
      const { publicKey } = JSON.parse(stored);
      if (publicKey) return { publicKey, hasKeys: true };
    }
    const pair = await generateKeyPair();
    const publicKey = await exportPublicKey(pair);
    const privateKey = await exportPrivateKey(pair);
    localStorage.setItem(E2E_KEYS, JSON.stringify({ publicKey, privateKey }));
    return { publicKey, hasKeys: true };
  } catch (e) {
    console.error('E2E init error:', e);
    return { publicKey: null, hasKeys: false };
  }
}

export async function getMyPublicKey() {
  const stored = localStorage.getItem(E2E_KEYS);
  if (!stored) return null;
  const { publicKey } = JSON.parse(stored);
  return publicKey || null;
}

export async function encryptForUser(plaintext, theirPublicKeyBase64) {
  const stored = localStorage.getItem(E2E_KEYS);
  if (!stored) throw new Error('لا توجد مفاتيح E2E');
  const { privateKey: privJwk } = JSON.parse(stored);
  const myPrivate = await importPrivateKey(privJwk);
  const theirPublic = await importPublicKey(theirPublicKeyBase64);
  const aesKey = await deriveAesKey(myPrivate, theirPublic);
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const encoded = new TextEncoder().encode(plaintext);
  const cipher = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, aesKey, encoded);
  return {
    content: btoa(String.fromCharCode(...new Uint8Array(cipher))),
    iv: btoa(String.fromCharCode(...iv))
  };
}

export async function decryptFromUser(ciphertextBase64, ivBase64, theirPublicKeyBase64) {
  const stored = localStorage.getItem(E2E_KEYS);
  if (!stored) return null;
  const { privateKey: privJwk } = JSON.parse(stored);
  const myPrivate = await importPrivateKey(privJwk);
  const theirPublic = await importPublicKey(theirPublicKeyBase64);
  const aesKey = await deriveAesKey(myPrivate, theirPublic);
  const iv = Uint8Array.from(atob(ivBase64), (c) => c.charCodeAt(0));
  const cipher = Uint8Array.from(atob(ciphertextBase64), (c) => c.charCodeAt(0));
  try {
    const decrypted = await crypto.subtle.decrypt({ name: 'AES-GCM', iv }, aesKey, cipher);
    return new TextDecoder().decode(decrypted);
  } catch (_) {
    return null;
  }
}
