/* Private development worker; no served V2 page imports this module. */
import { buildRom } from '../../web/core.mjs';
import { composeSelection, resolveSelection } from './composer.mjs';
import { loadBundle, readBounded, dataRoot } from './bundle.mjs';
let running = false;
self.onmessage = async ({ data }) => {
  if (running) { self.postMessage({ type: 'error', message: 'An import build is already running.' }); return; }
  running = true;
  try {
    const { bundle, plan } = await loadBundle();
    if (data.plan_sha256 !== bundle.plan.sha256) throw new Error('The import catalogue changed. Reload the page before building.');
    const selection = resolveSelection(plan, data.requested);
    const kind = selection.enabled.length ? 'v3' : 'v2';
    const manifest = bundle[kind];
    const progress = (value, message) => self.postMessage({ type: 'progress', value: Math.floor(value * .9), message });
    const built = await buildRom(data.n64, data.gamecube, manifest,
      recipe => readBounded(new URL(`${kind}/patch.afwp.gz`, dataRoot), recipe.size, true), progress);
    self.postMessage({ type: 'progress', value: 92, message: 'Applying your selected imports…' });
    const { output, receipt } = await composeSelection(built.output, plan, data.requested);
    receipt.reconstruction = built.receipt; receipt.plan_sha256 = bundle.plan.sha256;
    self.postMessage({ type: 'done', buffer: output.buffer, receipt }, [output.buffer]);
  } catch (error) {
    self.postMessage({ type: 'error', message: error.message || 'Import composition failed. Your files have not been changed.' });
  } finally { running = false; }
};
