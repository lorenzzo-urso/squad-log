// Dev-only Chrome API mock — inert when real extension APIs exist
if (!window.chrome?.storage) {
  const ls = (k) => `__cblog_${k}`;

  window.chrome = window.chrome || {};

  window.chrome.storage = {
    local: {
      get: async (keyOrObj) => {
        const key = typeof keyOrObj === 'string' ? keyOrObj
          : Array.isArray(keyOrObj) ? keyOrObj[0]
          : Object.keys(keyOrObj)[0];
        const raw = localStorage.getItem(ls(`local_${key}`));
        const defaults = typeof keyOrObj === 'object' && !Array.isArray(keyOrObj) ? keyOrObj : {};
        return raw ? { [key]: JSON.parse(raw) } : defaults;
      },
      set: async (obj) => {
        Object.entries(obj).forEach(([k, v]) =>
          localStorage.setItem(ls(`local_${k}`), JSON.stringify(v))
        );
      },
    },
    sync: {
      get: async (keyOrObj) => {
        const key = typeof keyOrObj === 'string' ? keyOrObj
          : Array.isArray(keyOrObj) ? keyOrObj[0]
          : Object.keys(keyOrObj)[0];
        const raw = localStorage.getItem(ls(`sync_${key}`));
        const defaults = typeof keyOrObj === 'object' && !Array.isArray(keyOrObj) ? keyOrObj : {};
        return raw ? { [key]: JSON.parse(raw) } : defaults;
      },
      set: async (obj) => {
        Object.entries(obj).forEach(([k, v]) =>
          localStorage.setItem(ls(`sync_${k}`), JSON.stringify(v))
        );
      },
    },
  };

  window.chrome.tabs = {
    query: async () => [{
      id: 999,
      url: 'https://example.com/article/ai-trends-2025',
      title: 'AI Trends 2025 — Preview Mode',
    }],
    create: async ({ url }) => { console.info('[mock] chrome.tabs.create', url); window.open(url, '_blank'); },
  };

  window.chrome.permissions = {
    request: async (opts) => { console.info('[mock] chrome.permissions.request', opts); return true; },
  };

  // Simulate page scraping returning realistic data
  window.chrome.scripting = {
    executeScript: async ({ func }) => [{
      result: {
        title:        'AI Trends 2025: What to Expect',
        description:  'A comprehensive overview of AI developments expected in 2025.',
        author:       'Jane Doe',
        siteName:     'TechBlog',
        url:          'https://example.com/article/ai-trends-2025',
        detectedType: 'artigo',
        bodyText:     'Artificial intelligence continues to evolve rapidly...',
      },
    }],
  };

  window.chrome.runtime = {
    onInstalled: { addListener: () => {} },
  };

  console.info('[ContentBlog] chrome-mock active (dev mode)');
}
