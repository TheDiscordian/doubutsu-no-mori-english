import { rejectArchive } from '../../web/core.mjs';
import { loadBundle, loadReview } from './bundle.mjs';
import { resolveSelection } from './composer.mjs';
import { exportSettings, importSettings, MAX_SETTINGS_BYTES } from './settings.mjs';

const $ = id => document.getElementById(id);
const inputs = [$('n64'), $('gamecube')];
const requested = new Set(), cards = new Map(), reviews = [];
const behaviours = {};
const kinds = { villager: 'Villager', furniture: 'Furniture', clothing: 'Clothing', equipment: 'Equipment', floor: 'Floor', wall: 'Wallpaper', fish: 'Fish', insect: 'Insect', diary: 'Diary', carried: 'Carried item' };
const choiceCopy = {
  'fish-population': { name: 'Which fish appear', N64: 'Keep the original N64 appearance rules, with your selected added species mixed in.', GameCube: 'Use GameCube appearance rules for all fish, including how the season, time, weather, and town environment affect their chances.' },
  'coastal-fish-movement': { name: 'Ocean fish swimming', N64: 'Use the original N64 swimming, waiting, and fleeing routines.', GameCube: 'Use GameCube swimming patterns, pauses, and shoreline avoidance.', note: 'Applies to every ocean fish, original and imported. River and pond fish are not changed by this setting.' },
  'insect-population': { name: 'How many insects appear', N64: 'Up to two wild insects at once, using the original N64 appearance rules.', GameCube: 'Up to eight wild insects at once. Species are chosen using GameCube rules for the season, time, and location, and insects can appear in groups.', note: 'Applies to original and imported insects. Releasing an insect still works in either mode.' },
  'holiday-calendar': { name: 'Holiday dates', N64: 'Shared celebrations follow the Japanese N64 dates.', GameCube: 'Shared celebrations follow the English GameCube dates.', note: 'This changes dates, not which holidays you import. Celebrations exclusive to either game keep their own dates.' },
  'paper-quantities': { name: 'Stationery', N64: 'Buy and receive one sheet at a time.', GameCube: 'Buy and receive packs of four sheets. Packs can be split or combined; writing a letter uses one sheet.' },
  'late-december-stock': { name: 'Nook’s December 26–31 stock', N64: 'Offer both the original New Year items and your selected festive candle and flag. Each seasonal selection has an equal chance of using either pair.', GameCube: 'Use your selected festive candle and flag instead of the original pair. If you leave either import off, its original N64 item stays available.', note: 'Only December 26–31 stock changes. This setting does nothing if neither festive item is selected.' },
  'starting-diary': { name: 'Start with a diary', N64: 'Keep the original N64 starting house, without a diary.', GameCube: 'Place a college-rule diary on the orange box (the cardboard box) inside each starting house. Both imports are included automatically.', note: 'Applies when starting houses are created. Existing houses and player inventories are not changed.' },
};
let loaded, selection, worker, generation = 0, romURL, receiptURL;
const status = message => { $('status').textContent = message; };
const behaviourControls = new Map();
function fileError() {
  try { for (const input of inputs) if (input.files[0]) rejectArchive(input.files[0]); }
  catch (error) { return error.message; }
  return null;
}
function ready() {
  $('build').disabled = !loaded || Boolean(worker) || !inputs.every(input => input.files[0]) ||
    Boolean(fileError()) || (Boolean(selection?.enabled.length || selection?.behaviours_changed) && !$('save-ack').checked);
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
  const query = $(row.kind === 'villager' ? 'villager-search' : 'search').value.trim().toLocaleLowerCase();
  const kind = row.kind === 'villager' ? 'all' : $('kind').value;
  return (kind === 'all' || row.kind === kind) && `${row.name} ${row.id}`.toLocaleLowerCase().includes(query);
}
function filter() {
  let visible = 0, neighbours = 0, pending = 0;
  for (const { row, card } of cards.values()) {
    card.hidden = Boolean(row.dependency_only) || !matches(row);
    if (!card.hidden) { if (row.kind === 'villager') neighbours++; else visible++; }
  }
  for (const { row, card } of reviews) { card.hidden = !matches(row); if (!card.hidden) pending++; }
  const offered = [...cards.values()].filter(({ row }) => !row.dependency_only && row.kind !== 'villager').length;
  const residents = [...cards.values()].filter(({ row }) => row.kind === 'villager').length;
  $('visible-count').textContent = `${visible} of ${offered} items`;
  $('villager-count').textContent = `${neighbours} of ${residents} villagers`;
  $('review-count').textContent = `(${pending} shown)`;
  $('no-results').hidden = Boolean(visible); $('no-review-results').hidden = Boolean(pending);
  $('no-villagers').hidden = Boolean(neighbours);
  $('select-visible').disabled = !visible; $('clear-visible').disabled = !visible;
  $('select-villagers').disabled = !neighbours; $('clear-villagers').disabled = !neighbours;
}
function renderSelection() {
  const reasonName = key => cards.get(key)?.row.name || choiceCopy[key]?.name || key;
  selection = resolveSelection(loaded.plan, [...requested], behaviours);
  const custom = Boolean(selection.enabled.length || selection.behaviours_changed);
  const enabled = new Set(selection.enabled), required = new Set(selection.required);
  for (const [id, { checkbox, card, note }] of cards) {
    checkbox.checked = enabled.has(id); checkbox.disabled = required.has(id) || cards.get(id).row.dependency_only === true;
    card.dataset.selected = String(enabled.has(id)); card.dataset.required = String(required.has(id));
    const parents = selection.dependency_reasons[id] || [];
    note.textContent = parents.length ? `Required by ${parents.map(reasonName).join(', ')}` : '';
    note.hidden = !parents.length;
  }
  $('selection-heading').textContent = selection.enabled.length ? `${selection.enabled.length} imports included` : 'No imports selected';
  $('selection-summary').textContent = selection.enabled.length ?
    `${selection.requested.length} chosen by you · ${selection.required.length} added as requirements` :
    selection.behaviours_changed ? 'No added items or villagers. Your build uses the selected V3 behaviour settings.' :
    'Your build will be the unchanged V2 English translation.';
  $('dependencies').hidden = !selection.required.length;
  $('dependency-list').replaceChildren(...selection.required.map(id => {
    const li = document.createElement('li');
    li.textContent = `${cards.get(id).row.name} — required by ${selection.dependency_reasons[id].map(reasonName).join(', ')}`;
    return li;
  }));
  $('save-warning').hidden = !custom; $('baseline-note').hidden = custom;
  $('build').textContent = custom ? 'Build with selected options' : 'Build translation only';
  ready();
}
function changeSelection(change) {
  const before = [...requested].sort().join('\n'); change();
  if (before !== [...requested].sort().join('\n')) {
    invalidate('Selections changed. Review the included requirements before building.', true); renderSelection();
  }
}
function addChoices(plan, review) {
  // Keep the full technical save-format record in profiles, not page copy.
  for (const row of plan.behaviours || []) {
    if (row.pipeline_unavailable) continue;
    const label = document.createElement('label'), select = document.createElement('select');
    const caption = document.createElement('strong'), description = document.createElement('p');
    const copy = choiceCopy[row.id];
    caption.textContent = copy?.name || row.name; description.textContent = copy?.note || row.description;
    description.id = `behaviour-description-${row.id}`; select.setAttribute('aria-describedby', description.id);
    for (const value of Object.keys(row.values)) {
      const option = document.createElement('option'); option.value = value; option.textContent = value;
      select.append(option);
    }
    select.value = row.default; behaviours[row.id] = row.default;
    behaviourControls.set(row.id, select);
    select.addEventListener('change', () => {
      behaviours[row.id] = select.value;
      invalidate('Behaviour settings changed. Review the save warning before building.', true); renderSelection();
    });
    const card = document.createElement('div'); card.className = 'behaviour-option';
    label.append(caption, select); card.append(label);
    if (copy) {
      const comparison = document.createElement('dl');
      for (const value of ['N64', 'GameCube']) {
        const term = document.createElement('dt'), detail = document.createElement('dd');
        term.textContent = value; detail.textContent = copy[value]; comparison.append(term, detail);
      }
      comparison.id = description.id; description.removeAttribute('id'); card.append(comparison);
      if (copy.note) card.append(description);
    } else card.append(description);
    $('behaviour-options').append(card);
  }
  $('behaviour-controls').hidden = !plan.behaviours?.length;
  $('behaviour-note').textContent = 'Keep your behaviour settings with your save. A save made with four-sheet stationery packs needs the same setting when you load it again. Back up your save before changing settings.';
  for (const row of [...plan.options].sort((a, b) => a.kind.localeCompare(b.kind) || a.name.localeCompare(b.name))) {
    const card = document.createElement('label'), checkbox = document.createElement('input');
    const text = document.createElement('span'), name = document.createElement('strong'), detail = document.createElement('small');
    const note = document.createElement('small');
    card.className = 'option'; card.dataset.id = row.id;
    checkbox.type = 'checkbox'; checkbox.setAttribute('aria-label', row.name);
    note.className = 'requirement'; note.id = `requirement-${cards.size}`; checkbox.setAttribute('aria-describedby', note.id);
    name.textContent = row.name; detail.textContent = `${kinds[row.kind]} · ${row.id.split('/').at(-1)}`;
    if (row.native_artwork_variant) detail.textContent += ' · GameCube appearance; N64 version retained';
    text.append(name, detail, note); card.append(checkbox, text);
    $(row.kind === 'villager' ? 'villager-options' : 'options').append(card);
    cards.set(row.id, { row, card, checkbox, note });
    if (row.dependency_only) {
      card.hidden = true;
      checkbox.disabled = true;
      continue;
    }
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
  const native = input.id === 'n64';
  $(native ? 'n64-name' : 'gc-name').textContent = input.files[0]?.name || 'No file chosen';
  $(native ? 'n64-field' : 'gc-field').classList.toggle('selected', Boolean(input.files[0]));
  invalidate('Game files changed. Build again to verify this pair of inputs.', true);
  if (fileError()) error(fileError());
});
$('save-ack').addEventListener('change', () => invalidate('Save handling updated. Your selections have not changed.'));
$('search').addEventListener('input', filter); $('villager-search').addEventListener('input', filter); $('kind').addEventListener('change', filter);
for (const [button, include, visible, kind] of [['select-visible', true, true, 'items'], ['clear-visible', false, true, 'items'],
  ['select-villagers', true, true, 'villager'], ['clear-villagers', false, true, 'villager'],
  ['select-items', true, false, 'items'], ['clear-items', false, false, 'items'],
  ['select-all', true, false, 'all'], ['clear-all', false, false, 'all']]) {
  $(button).addEventListener('click', () => changeSelection(() => {
    for (const [id, { row }] of cards) if (!row.dependency_only &&
      (kind === 'all' || (kind === 'villager' ? row.kind === 'villager' : row.kind !== 'villager')) &&
      (!visible || matches(row))) {
      if (include) requested.add(id); else requested.delete(id);
    }
  }));
}
$('cancel').addEventListener('click', () => invalidate('Cancelled. Your original files have not been changed.'));
$('settings-export').addEventListener('click', () => {
  if (!loaded) return;
  const settings = exportSettings(loaded.plan, loaded.bundle.plan.sha256, [...requested], behaviours);
  const url = URL.createObjectURL(new Blob([JSON.stringify(settings, null, 2) + '\n'], { type: 'application/json' }));
  const link = document.createElement('a'); link.href = url;
  link.download = 'Animal Crossing N64 - V3 settings.json'; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 0);
  $('settings-status').textContent = 'Settings exported. Share this file, not your ROM or save.';
});
$('settings-import').addEventListener('change', async event => {
  const file = event.target.files[0]; event.target.value = '';
  if (!file || !loaded) return;
  try {
    if (file.size > MAX_SETTINGS_BYTES) throw new Error('This settings file is too large. Choose the exported JSON settings file, not a game or save.');
    const current = loaded;
    const incoming = importSettings(current.plan, current.bundle.plan.sha256, JSON.parse(await file.text()));
    if (loaded !== current) throw new Error('The catalogue changed while reading settings. Import the file again.');
    requested.clear(); for (const id of incoming.requested) requested.add(id);
    for (const [id, value] of Object.entries(incoming.behaviours)) {
      behaviours[id] = value; behaviourControls.get(id).value = value;
    }
    invalidate('Shared settings loaded. Review your imports and the save warning before building.', true);
    renderSelection();
    $('settings-status').textContent = 'Settings imported. Included requirements have been recalculated; your game files have not changed.';
  } catch (problem) {
    $('settings-status').textContent = problem instanceof SyntaxError ?
      'This file is not valid JSON. No choices have changed.' : problem.message;
  }
});
$('build').addEventListener('click', () => {
  ready(); if ($('build').disabled) return;
  clearDownloads(); $('error').hidden = true;
  const job = ++generation, chosen = [...selection.requested], chosenBehaviours = { ...selection.behaviours };
  // Resolved receipts include frozen V4 defaults, but those are not user
  // settings. Send only the visible controls and compare the full receipt below.
  const chosenSettings = { ...behaviours };
  const custom = Boolean(selection.enabled.length || selection.behaviours_changed);
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
      if (JSON.stringify(data.receipt.behaviours || {}) !== JSON.stringify(chosenBehaviours)) {
        error('The returned behaviour settings do not match your choices. No download was created.'); return;
      }
      stop();
      try {
        romURL = URL.createObjectURL(new Blob([data.buffer], { type: 'application/octet-stream' }));
        receiptURL = URL.createObjectURL(new Blob([JSON.stringify(data.receipt, null, 2) + '\n'], { type: 'application/json' }));
        $('download').href = romURL; $('receipt').href = receiptURL;
        $('download').download = custom ? `Animal Crossing N64 - V3 ${data.receipt.output_sha256.slice(0, 8)}.z64` : 'Animal Crossing N64 - English.z64';
        $('receipt').download = `Animal Crossing N64 - ${data.receipt.output_sha256.slice(0, 8)} profile.json`;
        $('output-sha').textContent = data.receipt.output_sha256; $('success').hidden = false;
        status('Build complete. Download the ROM and keep its selection profile.'); $('success-heading').focus({ preventScroll: true });
      } catch { error('The browser could not create the downloads. No input files were changed.'); }
    }
  };
  worker.onerror = () => { if (job === generation) error('The patcher stopped unexpectedly. No input files were changed.'); };
  worker.postMessage({ requested: chosen, behaviours: chosenSettings, plan_sha256: loaded.bundle.plan.sha256, n64: inputs[0].files[0], gamecube: inputs[1].files[0] });
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
