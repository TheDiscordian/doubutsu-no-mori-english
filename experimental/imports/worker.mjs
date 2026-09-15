/* Private development worker; no served V2 page imports this module. */
import { buildRom, sha256, validateManifest } from '../../web/core.mjs';
import { composeSelection, resolveSelection } from './composer.mjs';

async function read(url, limit, exact = false) {
  const response = await fetch(url, { credentials: 'omit', redirect: 'error', cache: 'no-store' });
  if (!response.ok) throw new Error('Experimental import data is unavailable.');
  const reader = response.body.getReader(), result = new Uint8Array(limit);
  let at = 0;
  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      if (value.length > limit - at) throw new Error('Experimental data exceeds its expected size.');
      result.set(value, at); at += value.length;
    }
    if (exact && at !== limit) throw new Error('Experimental data is incomplete.');
  } finally { await reader.cancel().catch(() => {}); reader.releaseLock(); }
  return result.slice(0, at);
}
const json = raw => JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(raw));
let running = false;
self.onmessage = async ({ data }) => {
  if (running) { self.postMessage({ type: 'error', message: 'An import build is already running.' }); return; }
  running = true;
  try {
    const root = new URL('../../data/', import.meta.url);
    const bundle = json(await read(new URL('manifest.json', root), 128 * 1024));
    if (bundle.format !== 'AFV3-BROWSER-BUNDLE-1' || bundle.experimental !== true || bundle.web_patcher_enabled !== false ||
        bundle.plan?.file !== 'composition.json' || !Number.isSafeInteger(bundle.plan.size) ||
        bundle.plan.size < 1 || bundle.plan.size > 4 * 1024 * 1024) throw new Error('Unsupported experimental bundle.');
    const raw = await read(new URL('composition.json', root), bundle.plan.size, true);
    if (await sha256(raw) !== bundle.plan.sha256) throw new Error('Import plan checksum mismatch.');
    const plan = json(raw), selection = resolveSelection(plan, data.requested);
    const kind = selection.enabled.length ? 'v3' : 'v2';
    const manifest = validateManifest(bundle[kind]);
    if (manifest.public_release !== false || manifest.output_sha256 !== (kind === 'v2' ? plan.stable_sha256 : plan.base_sha256) ||
        manifest.output_size !== (kind === 'v2' ? plan.stable_size : plan.base_size)) throw new Error('Import plan and reconstruction recipe disagree.');
    const progress = (value, message) => self.postMessage({ type: 'progress', value: Math.floor(value * .9), message });
    const built = await buildRom(data.n64, data.gamecube, manifest,
      recipe => read(new URL(`${kind}/patch.afwp.gz`, root), recipe.size, true), progress);
    self.postMessage({ type: 'progress', value: 92, message: 'Applying your selected imports…' });
    const { output, receipt } = await composeSelection(built.output, plan, data.requested);
    receipt.reconstruction = built.receipt; receipt.plan_sha256 = bundle.plan.sha256;
    self.postMessage({ type: 'done', buffer: output.buffer, receipt }, [output.buffer]);
  } catch (error) {
    self.postMessage({ type: 'error', message: error.message || 'Import composition failed. Your files have not been changed.' });
  } finally { running = false; }
};
