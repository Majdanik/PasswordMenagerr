// Client-side vault encryption: PBKDF2 (derive) + AES-GCM (encrypt/decrypt).
// The server only ever sees/stores an opaque base64 blob - it never
// participates in encryption or decryption.

const PBKDF2_ITERATIONS = 310000; // OWASP-recommended floor for PBKDF2-SHA256 (2023+)
const IV_LENGTH_BYTES = 12; // standard/recommended AES-GCM IV length

function bytesToBase64(bytes) {
  let binary = "";
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

function base64ToBytes(base64) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

/**
 * Derive a per-operation AES-256-GCM key from the user's PIN + Fernet key
 * and their per-account KDF salt (from GET /vault/salt).
 * Not cached anywhere - recompute on every encrypt/decrypt call.
 */
export async function deriveVaultKey(pin, fernetKey, saltBase64) {
  const passphrase = `${pin}:${fernetKey}`;
  const passphraseBytes = new TextEncoder().encode(passphrase);
  const saltBytes = base64ToBytes(saltBase64);

  const keyMaterial = await crypto.subtle.importKey(
    "raw",
    passphraseBytes,
    "PBKDF2",
    false,
    ["deriveKey"]
  );

  return crypto.subtle.deriveKey(
    {
      name: "PBKDF2",
      salt: saltBytes,
      iterations: PBKDF2_ITERATIONS,
      hash: "SHA-256",
    },
    keyMaterial,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt", "decrypt"]
  );
}

/**
 * Encrypt plaintext with the given AES-GCM vault key.
 * Returns base64(iv || ciphertext+tag) - a single opaque string, safe to
 * store as-is in PasswordEntry.password.
 */
export async function encryptText(plainText, vaultKey) {
  const iv = crypto.getRandomValues(new Uint8Array(IV_LENGTH_BYTES));
  const plainBytes = new TextEncoder().encode(plainText);
  const ciphertext = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, vaultKey, plainBytes);

  const combined = new Uint8Array(iv.length + ciphertext.byteLength);
  combined.set(iv, 0);
  combined.set(new Uint8Array(ciphertext), iv.length);
  return bytesToBase64(combined);
}

/**
 * Decrypt a base64(iv || ciphertext+tag) blob with the given AES-GCM vault key.
 * Throws if the key/PIN is wrong (AES-GCM tag check fails) - callers should
 * catch and show a generic "wrong PIN/key" message; the browser gives no
 * finer-grained reason than a generic OperationError.
 */
export async function decryptText(blobBase64, vaultKey) {
  const combined = base64ToBytes(blobBase64);
  const iv = combined.slice(0, IV_LENGTH_BYTES);
  const ciphertext = combined.slice(IV_LENGTH_BYTES);
  const plainBuf = await crypto.subtle.decrypt({ name: "AES-GCM", iv }, vaultKey, ciphertext);
  return new TextDecoder().decode(plainBuf);
}
