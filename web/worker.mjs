import { buildRom } from './core.mjs';

self.onmessage = async ({ data }) => {
  try {
    const { output, receipt } = await buildRom(data.n64, data.gamecube, data.manifest,
      async recipe => {
        const url = new URL('./release/' + recipe.file, import.meta.url);
        const response = await fetch(url, { cache: 'no-store', credentials: 'omit', redirect: 'error' });
        if (!response.ok) throw new Error('The patch is unavailable. Reload the page and try again.');
        const reader = response.body.getReader();
        const result = new Uint8Array(recipe.size);
        let at = 0;
        try {
          for (;;) {
            const { value, done } = await reader.read();
            if (done) break;
            if (at + value.length > result.length) throw new Error('The patch download exceeds its expected size.');
            result.set(value, at); at += value.length;
          }
          if (at !== result.length) throw new Error('The patch download is incomplete.');
        } finally { await reader.cancel().catch(() => {}); reader.releaseLock(); }
        return result;
      }, (value, message) => self.postMessage({ type: 'progress', value, message }));
    self.postMessage({ type: 'done', buffer: output.buffer, receipt }, [output.buffer]);
  } catch (error) {
    self.postMessage({ type: 'error', message: error.message || 'Patching failed. Your input files have not been changed.' });
  }
};
