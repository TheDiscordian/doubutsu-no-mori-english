import { validateManifest, rejectArchive } from './core.mjs';

const $ = id => document.getElementById(id);
const input = { n64: $('n64'), gamecube: $('gamecube') };
let manifest, worker, generation = 0, romURL, receiptURL;
const status = message => { $('status').textContent = message; };
function clearDownload() {
  if (romURL) URL.revokeObjectURL(romURL);
  if (receiptURL) URL.revokeObjectURL(receiptURL);
  romURL = receiptURL = null;
  $('download').removeAttribute('href'); $('receipt').removeAttribute('href');
  $('success').hidden = true; $('output-sha').textContent = '';
}
function stop() {
  generation++; worker?.terminate(); worker = null;
  $('working').hidden = true; $('build').hidden = false;
  $('build').disabled = !manifest || !input.n64.files.length || !input.gamecube.files.length;
  $('patcher').setAttribute('aria-busy', 'false');
}
function showError(message) {
  $('error').textContent = message; $('error').hidden = false;
  status('Your original files have not been changed.');
}
for (const [name, field] of Object.entries(input)) {
  field.addEventListener('change', () => {
    stop(); clearDownload(); $('error').hidden = true;
    const file = field.files[0], prefix = name === 'n64' ? 'n64' : 'gc';
    $(prefix + '-name').textContent = file ? file.name : 'No file chosen';
    $(prefix + '-field').classList.toggle('selected', Boolean(file));
    try { if (file) rejectArchive(file); }
    catch (error) { showError(error.message); $('build').disabled = true; return; }
    status($('build').disabled ? 'Choose both game files to begin.' : 'Both files selected. Ready when you are.');
  });
}
$('cancel').addEventListener('click', () => {
  stop(); clearDownload(); status('Cancelled. Your original files have not been changed.');
});
$('build').addEventListener('click', () => {
  if (!manifest || !input.n64.files[0] || !input.gamecube.files[0] || worker) return;
  clearDownload(); $('error').hidden = true; $('build').disabled = true;
  $('working').hidden = false; $('progress').value = 0;
  $('patcher').setAttribute('aria-busy', 'true');
  status('Starting your local patcher…');
  const job = ++generation;
  try { worker = new Worker(new URL('./worker.mjs', import.meta.url), { type: 'module' }); }
  catch { stop(); showError('This browser could not start the patcher. Try a current desktop browser over localhost or HTTPS.'); return; }
  worker.onmessage = ({ data }) => {
    if (job !== generation) return;
    if (data.type === 'progress') { $('progress').value = data.value; status(data.message); }
    else if (data.type === 'done') {
      stop(); $('build').hidden = true;
      romURL = URL.createObjectURL(new Blob([data.buffer], { type: 'application/octet-stream' }));
      receiptURL = URL.createObjectURL(new Blob([JSON.stringify(data.receipt, null, 2) + '\n'], { type: 'application/json' }));
      $('download').href = romURL; $('download').download = manifest.output_name;
      $('receipt').href = receiptURL; $('output-sha').textContent = data.receipt.output_sha256;
      $('success').hidden = false; status('Verified. Download your new ROM below.');
      $('success-heading').focus({ preventScroll: true });
    } else if (data.type === 'error') { stop(); clearDownload(); showError(data.message); }
  };
  worker.onerror = () => { if (job === generation) { stop(); clearDownload(); showError('The patcher stopped unexpectedly. Try a current desktop browser with enough free memory.'); } };
  worker.postMessage({ n64: input.n64.files[0], gamecube: input.gamecube.files[0], manifest });
});
window.addEventListener('beforeunload', () => { stop(); clearDownload(); });

async function init() {
  try {
    if (!window.isSecureContext || !crypto.subtle || !window.Worker || !window.DecompressionStream) {
      throw new Error('Use a current Chrome, Edge, Firefox, or Safari browser. Open this page on localhost or HTTPS so local checksum verification is available.');
    }
    const response = await fetch(new URL('./release/manifest.json', import.meta.url), { cache: 'no-store', credentials: 'omit', redirect: 'error' });
    if (!response.ok) throw new Error('Release information is unavailable. Reload the page and try again.');
    manifest = validateManifest(await response.json());
    stop(); status('Choose both game files to begin.');
  } catch (error) { manifest = null; stop(); showError(error.message); }
}
init();
