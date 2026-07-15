export async function getQueue() {
  const { queue = [] } = await chrome.storage.local.get('queue');
  return queue;
}

export async function addToQueue(entry) {
  const queue = await getQueue();
  queue.push(entry);
  await chrome.storage.local.set({ queue });
  return queue;
}

export async function removeFromQueue(id) {
  const queue = await getQueue();
  const updated = queue.filter(e => e.id !== id);
  await chrome.storage.local.set({ queue: updated });
  return updated;
}

export async function updateInQueue(entry) {
  const queue = await getQueue();
  const idx = queue.findIndex(e => e.id === entry.id);
  if (idx !== -1) queue[idx] = entry;
  await chrome.storage.local.set({ queue });
  return queue;
}

export async function clearQueue() {
  await chrome.storage.local.set({ queue: [] });
}

const DEFAULTS = {
  aiProvider: 'claude',
  claudeKey: '',
  openaiKey: '',
  squadlogUrl: '',
};

export async function getSettings() {
  const { settings = {} } = await chrome.storage.sync.get('settings');
  return { ...DEFAULTS, ...settings };
}

export async function saveSettings(settings) {
  await chrome.storage.sync.set({ settings });
}
