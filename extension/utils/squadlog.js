// Talks to the squad-log app's capture API (POST /api/learning) instead of
// writing a data.json to GitHub. Auth is whatever squad-log session cookie
// already exists in this browser — the extension never sends who the user
// is, so a capture always lands on the account that's actually logged in.

// Accented subtypes from schema.js -> our ASCII learning_items.type values.
const TYPE_MAP = {
  'artigo': 'artigo',
  'notícia': 'noticia',
  'livro': 'livro',
  'curso': 'curso',
  'treinamento': 'treinamento',
  'vídeo': 'video',
  'projeto': 'projeto',
};

function mapType(subtype) {
  return TYPE_MAP[subtype] || 'outro';
}

function normalizeUrl(url) {
  return url.replace(/\/+$/, '');
}

export async function whoami(baseUrl) {
  const res = await fetch(`${normalizeUrl(baseUrl)}/api/whoami`, { credentials: 'include' });
  if (res.status === 401 || res.status === 303) return null;
  if (!res.ok) throw new Error(`squad-log ${res.status}`);
  return res.json();
}

export async function pushEntry(baseUrl, entry) {
  const body = {
    title: entry.title,
    type: mapType(entry.subtype || entry.type),
    description: entry.notes || entry.description || entry.pitch || '',
    link: entry.url || '',
    consumed_at: entry.dates?.consumed || entry.dates?.captured || new Date().toISOString().split('T')[0],
  };
  const res = await fetch(`${normalizeUrl(baseUrl)}/api/learning`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `squad-log ${res.status}`);
  }
  return res.json();
}
