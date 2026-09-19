import { rejectArchive } from '../../web/core.mjs';
import { loadBundle, loadReview } from './bundle.mjs';
import { resolveSelection } from './composer.mjs';

const $ = id => document.getElementById(id);
const inputs = [$('n64'), $('gamecube')];
const requested = new Set(), cards = new Map(), reviews = [];
const kinds = { villager: 'Villager', furniture: 'Furniture', clothing: 'Clothing', equipment: 'Equipment' };
let loaded, selection, worker, generation = 0, romURL, receiptURL;
const status = message => { $('status').textContent = message; };
function fileError() {
  try { for (const input of inputs) if (input.files[0]) rejectArchive(input.files[0]); }
  catch (error) { return error.message; }
  return null;
}
function ready() {
  $('build').disabled = !loaded || Boolean(worker) || !inputs.every(input => input.files[0]) ||
    Boolean(fileError()) || (Boolean(selection?.enabled.length) && !$('save-ack').checked);
}
function clearDownloads() {
  for (const url of [romURL, receiptURL]) if (url) URL.revokeObjectURL(url);
  romURL = receiptURL = null;
  $('download').removeAttribute('href'); $('receipt').removeAttribute('href');
  $('output-sha').textContent = ''; $('success').hidden = true;
}
function stop() {
  generation++; worker?.terminate(); worker = null;
  $('working').hidden = true; $('patcher').setAttribute('aria-busy', 'false'); ready();
}
function invalidate(message, resetAcknowledgement = false) {
  stop(); clearDownloads(); $('error').hidden = true;
  if (resetAcknowledgement) $('save-ack').checked = false;
  ready(); status(message);
  const invalid = fileError();
  if (invalid) { $('error').textContent = invalid; $('error').hidden = false; }
}
function error(message) {
  stop(); clearDownloads(); $('error').textContent = message; $('error').hidden = false;
  status('Your original files have not been changed.');
}
function matches(row) {
  const query = $('search').value.trim().toLocaleLowerCase(), kind = $('kind').value;
  return (kind === 'all' || row.kind === kind) && `${row.name} ${row.id}`.toLocaleLowerCase().includes(query);
}
function filter() {
  let visible = 0, pending = 0;
  for (const { row, card } of cards.values()) { card.hidden = !matches(row); if (!card.hidden) visible++; }
  for (const { row, card } of reviews) { card.hidden = !matches(row); if (!card.hidden) pending++; }
  $('visible-count').textContent = `${visible} of ${cards.size} installed development choices shown`;
  $('review-count').textContent = `(${pending} shown)`;
  $('no-results').hidden = Boolean(visible); $('no-review-results').hidden = Boolean(pending);
  $('select-visible').disabled = !visible; $('clear-visible').disabled = !visible;
}
function renderSelection() {
  selection = resolveSelection(loaded.plan, [...requested]);
  const enabled = new Set(selection.enabled), required = new Set(selection.required);
  for (const [id, { checkbox, card, note }] of cards) {
    checkbox.checked = enabled.has(id); checkbox.disabled = required.has(id);
    card.dataset.selected = String(enabled.has(id)); card.dataset.required = String(required.has(id));
    const parents = selection.dependency_reasons[id] || [];
    note.textContent = parents.length ? `Required by ${parents.map(key => cards.get(key).row.name).join(', ')}` : '';
    note.hidden = !parents.length;
  }
  $('selection-heading').textContent = selection.enabled.length ? `${selection.enabled.length} imports included` : 'No imports selected';
  $('selection-summary').textContent = selection.enabled.length ?
    `${selection.requested.length} chosen by you · ${selection.required.length} added as requirements` :
    'Your build will be the unchanged V2 English translation.';
  $('dependencies').hidden = !selection.required.length;
  $('dependency-list').replaceChildren(...selection.required.map(id => {
    const li = document.createElement('li');
    li.textContent = `${cards.get(id).row.name} — required by ${selection.dependency_reasons[id].map(key => cards.get(key).row.name).join(', ')}`;
    return li;
  }));
  $('save-warning').hidden = !selection.enabled.length; $('baseline-note').hidden = Boolean(selection.enabled.length);
  $('build').textContent = selection.enabled.length ? 'Build with selected imports' : 'Build translation only';
  ready();
}
function changeSelection(change) {
  const before = [...requested].sort().join('\n'); change();
  if (before !== [...requested].sort().join('\n')) {
    invalidate('Selections changed. Review the included requirements before building.', true); renderSelection();
  }
}
function addChoices(plan, review) {
  for (const row of [...plan.options].sort((a, b) => a.kind.localeCompare(b.kind) || a.name.localeCompare(b.name))) {
    const card = document.createElement('label'), checkbox = document.createElement('input');
    const text = document.createElement('span'), name = document.createElement('strong'), detail = document.createElement('small');
    const note = document.createElement('small');
    card.className = 'option'; card.dataset.id = row.id;
    checkbox.type = 'checkbox'; checkbox.setAttribute('aria-label', row.name);
    note.className = 'requirement'; note.id = `requirement-${cards.size}`; checkbox.setAttribute('aria-describedby', note.id);
    name.textContent = row.name; detail.textContent = `${kinds[row.kind]} · ${row.id.split('/').at(-1)}`;
    text.append(name, detail, note); card.append(checkbox, text); $('options').append(card);
    cards.set(row.id, { row, card, checkbox, note });
    checkbox.addEventListener('change', () => changeSelection(() => {
      if (checkbox.checked) requested.add(row.id); else requested.delete(row.id);
    }));
  }
  for (const row of [...review.unavailable].sort((a, b) => a.name.localeCompare(b.name))) {
    const card = document.createElement('article'), name = document.createElement('strong'), reason = document.createElement('p');
    card.className = 'unavailable'; card.dataset.id = row.id;
    name.textContent = `${row.name} · ${row.id.split('/').at(-1)}`; reason.textContent = row.reason;
    card.append(name, reason); $('unavailable').append(card); reviews.push({ row, card });
  }
}
for (const input of inputs) input.addEventListener('change', () => {
  invalidate('Game files changed. Build again to verify this pair of inputs.', true);
  if (fileError()) error(fileError());
});
$('save-ack').addEventListener('change', () => invalidate('Save handling updated. Your selections have not changed.'));
$('search').addEventListener('input', filter); $('kind').addEventListener('change', filter);
for (const [button, include, visible] of [['select-visible', true, true], ['clear-visible', false, true],
  ['select-all', true, false], ['clear-all', false, false]]) {
  $(button).addEventListener('click', () => changeSelection(() => {
    for (const [id, { row }] of cards) if (!visible || matches(row)) {
      if (include) requested.add(id); else requested.delete(id);
    }
  }));
}
$('cancel').addEventListener('click', () => invalidate('Cancelled. Your original files have not been changed.'));
$('build').addEventListener('click', () => {
  ready(); if ($('build').disabled) return;
  clearDownloads(); $('error').hidden = true;
  const job = ++generation, chosen = [...selection.requested];
  try { worker = new Worker(new URL('./worker.mjs', import.meta.url), { type: 'module' }); }
  catch { error('This browser could not start the patcher. Use a current browser over localhost or HTTPS.'); return; }
  $('working').hidden = false; $('progress').value = 0; $('patcher').setAttribute('aria-busy', 'true');
  ready(); status('Checking your games and selected imports…');
  worker.onmessage = ({ data }) => {
    if (job !== generation) return;
    if (data.type === 'progress') { $('progress').value = data.value; status(data.message); }
    else if (data.type === 'error') error(data.message);
    else if (data.type === 'done') {
      if (!(data.buffer instanceof ArrayBuffer) || data.receipt?.plan_sha256 !== loaded.bundle.plan.sha256 ||
          JSON.stringify(data.receipt.requested) !== JSON.stringify(chosen) || !/^[0-9a-f]{64}$/.test(data.receipt.output_sha256)) {
        error('The returned build does not match your selected profile. No download was created.'); return;
      }
      stop();
      try {
        romURL = URL.createObjectURL(new Blob([data.buffer], { type: 'application/octet-stream' }));
        receiptURL = URL.createObjectURL(new Blob([JSON.stringify(data.receipt, null, 2) + '\n'], { type: 'application/json' }));
        $('download').href = romURL; $('receipt').href = receiptURL;
        $('download').download = chosen.length ? `Animal Crossing N64 - V3 ${data.receipt.output_sha256.slice(0, 8)}.z64` : 'Animal Crossing N64 - English.z64';
        $('receipt').download = `Animal Crossing N64 - ${data.receipt.output_sha256.slice(0, 8)} profile.json`;
        $('output-sha').textContent = data.receipt.output_sha256; $('success').hidden = false;
        status('Build complete. Download the ROM and keep its selection profile.'); $('success-heading').focus({ preventScroll: true });
      } catch { error('The browser could not create the downloads. No input files were changed.'); }
    }
  };
  worker.onerror = () => { if (job === generation) error('The patcher stopped unexpectedly. No input files were changed.'); };
  worker.postMessage({ requested: chosen, plan_sha256: loaded.bundle.plan.sha256, n64: inputs[0].files[0], gamecube: inputs[1].files[0] });
});
window.addEventListener('pagehide', () => { stop(); clearDownloads(); });

async function init() {
  try {
    if (!window.isSecureContext || !crypto.subtle || !window.Worker || !window.DecompressionStream) {
      throw new Error('Use a current browser on localhost or HTTPS for local file verification.');
    }
    const current = await loadBundle(), review = await loadReview(current.bundle, current.plan);
    loaded = current; addChoices(current.plan, review); $('selection-controls').disabled = false;
    renderSelection(); filter(); status('Choose both original game files. Imports are optional.');
  } catch (problem) { loaded = null; error(problem.message || 'The import catalogue could not be loaded.'); }
}
init();
