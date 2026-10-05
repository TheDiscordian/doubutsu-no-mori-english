import { rejectArchive } from '../../web/core.mjs';
import { loadBundle, loadReview } from './bundle.mjs';
import { resolveSelection } from './composer.mjs';
import { exportSettings, importSettings, MAX_SETTINGS_BYTES } from './settings.mjs';

const $ = id => document.getElementById(id);
const inputs = [$('n64'), $('gamecube')];
const requested = new Set(), cards = new Map();
const behaviours = {};
const kinds = { villager: 'Villager', furniture: 'Furniture', clothing: 'Clothing', equipment: 'Equipment', floor: 'Floor', wall: 'Wallpaper', fish: 'Fish', insect: 'Insect', diary: 'Diary', carried: 'Carried item' };
const choiceCopy = {
  'fish-population': { name: 'Which fish appear', N64: 'Keep the original N64 appearance rules, with your selected added species mixed in.', GameCube: 'Use GameCube appearance rules for all fish, including how the season, time, weather, and town environment affect their chances.' },
  'fish-movement': { name: 'Fish swimming', N64: 'Use N64 swimming, waiting, and escape behaviour for river, pond, and ocean fish.', GameCube: 'Use GameCube swimming, waiting, and escape behaviour for river, pond, and ocean fish.' },
  'insect-population': { name: 'How many insects appear', N64: 'Up to two wild insects at once, using the original N64 appearance rules.', GameCube: 'Up to eight wild insects at once. Species are chosen using GameCube rules for the season, time, and location, and insects can appear in groups.' },
  'holiday-calendar': { name: 'Holiday dates', N64: 'Shared celebrations follow the Japanese N64 dates.', GameCube: 'Shared celebrations follow the English GameCube dates.', note: 'Celebrations exclusive to either game keep their own dates.' },
  'paper-quantities': { name: 'Stationery', N64: 'Buy and receive one sheet at a time.', GameCube: 'Buy and receive packs of four sheets. Packs can be split or combined; writing a letter uses one sheet.' },
  'starting-diary': { name: 'Start with a diary', N64: 'Keep the original N64 starting house, without a diary.', GameCube: 'Place a college-rule diary on the orange box inside each starting house.', note: 'Only affects newly created houses. Existing houses are unchanged.' },
};
let loaded, selection, worker, generation = 0, romURL, receiptURL;
const status = message => { $('status').textContent = message; };
const behaviourControls = new Map();
const decorationControls = new Map();
const featureControls = new Map(), featureImports = new Set();
function fileError() {
  try { for (const input of inputs) if (input.files[0]) rejectArchive(input.files[0]); }
  catch (error) { return error.message; }
  return null;
}
function ready() {
  $('build').disabled = !loaded || Boolean(worker) || !inputs.every(input => input.files[0]) ||
    Boolean(fileError());
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
function invalidate(message) {
  stop(); clearDownloads(); $('error').hidden = true;
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
  let visible = 0, neighbours = 0;
  for (const { row, card } of cards.values()) {
    card.hidden = Boolean(row.dependency_only) || !matches(row);
    if (!card.hidden) { if (row.kind === 'villager') neighbours++; else visible++; }
  }
  const offered = [...cards.values()].filter(({ row }) => !row.dependency_only && row.kind !== 'villager').length;
  $('visible-count').textContent = `${visible} of ${offered} items`;
  $('no-results').hidden = Boolean(visible);
  $('no-villagers').hidden = Boolean(neighbours);
  $('select-visible').disabled = !visible; $('clear-visible').disabled = !visible;
  $('select-villagers').disabled = !neighbours; $('clear-villagers').disabled = !neighbours;
}
function renderSelection() {
  const reasonName = key => loaded.plan.features?.find(row => row.id === key)?.name ||
    loaded.plan.options.find(row => row.id === key)?.name || choiceCopy[key]?.name || key;
  selection = resolveSelection(loaded.plan, [...requested], behaviours);
  const custom = Boolean(selection.requested.length || selection.enabled.length || selection.behaviours_changed);
  const enabled = new Set(selection.enabled), required = new Set(selection.required);
  for (const [id, { checkbox, note }] of featureControls) {
    const parents = selection.feature_dependency_reasons?.[id] || [];
    checkbox.checked = selection.enabled_features.includes(id);
    checkbox.disabled = Boolean(parents.length);
    note.textContent = parents.length ? `Required to obtain ${parents.map(reasonName).join(', ')}` : '';
    note.hidden = !parents.length;
  }
  const stockMode = loaded.plan.behaviours?.find(row => row.id === 'new-year-stock')?.values[behaviours['new-year-stock']];
  for (const [key, { checkbox, bit, importId }] of decorationControls) {
    checkbox.checked = importId ? enabled.has(importId) : !(stockMode & bit);
    checkbox.disabled = importId ? required.has(importId) : false;
  }
  const residents = [...cards.values()].filter(({ row }) => row.kind === 'villager');
  $('villager-count').textContent = `${residents.filter(({ row }) => enabled.has(row.id)).length} selected · ${residents.length} available`;
  const items = [...cards.values()].filter(({ row }) => row.kind !== 'villager' && !row.dependency_only);
  $('item-count').textContent = `${items.filter(({ row }) => enabled.has(row.id)).length} selected · ${items.length} available`;
  for (const [id, { checkbox, card, note }] of cards) {
    checkbox.checked = enabled.has(id); checkbox.disabled = required.has(id) || cards.get(id).row.dependency_only === true;
    card.dataset.selected = String(enabled.has(id)); card.dataset.required = String(required.has(id));
    const parents = selection.dependency_reasons[id] || [];
    note.textContent = parents.length ? `Required by ${parents.map(reasonName).join(', ')}` : '';
    note.hidden = !parents.length;
  }
  $('selection-heading').textContent = selection.enabled.length ? `${selection.enabled.length} imports included` : 'No imports selected';
  const chosenImports = selection.requested.filter(id => enabled.has(id)).length;
  $('selection-summary').textContent = selection.enabled.length ?
    `${chosenImports} chosen by you · ${selection.required.length} added as requirements` :
    custom ? 'No added items or villagers. Your build uses your chosen town settings.' :
    'Your build includes the English translation, with no added items or villagers.';
  $('dependencies').hidden = !selection.required.length;
  $('dependency-list').replaceChildren(...selection.required.map(id => {
    const li = document.createElement('li');
    li.textContent = `${reasonName(id)} — required by ${selection.dependency_reasons[id].map(reasonName).join(', ')}`;
    return li;
  }));
  $('build').textContent = custom ? 'Build with selected options' : 'Build translation only';
  ready();
}
function changeSelection(change) {
  const before = [...requested].sort().join('\n'); change();
  if (before !== [...requested].sort().join('\n')) {
    invalidate('Selections changed. Review the included requirements before building.'); renderSelection();
  }
}
function addChoices(plan) {
  // Keep the full technical save-format record in profiles, not page copy.
  let decorationChoice;
  for (const row of plan.behaviours || []) {
    if (row.pipeline_unavailable) continue;
    if (row.id === 'new-year-stock') {
      decorationChoice = row;
      continue;
    }
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
      invalidate('Town settings changed. Build again to apply your choices.'); renderSelection();
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
  addFeatureChoices(plan);
  if (decorationChoice) addDecorationChoices(decorationChoice);
  $('behaviour-controls').hidden = !plan.behaviours?.length;
  for (const row of [...plan.options].sort((a, b) => a.kind.localeCompare(b.kind) || a.name.localeCompare(b.name))) {
    // Quest items are controlled by their town setting, not catalogue cards.
    if (featureImports.has(row.id)) continue;
    const card = document.createElement('label'), checkbox = document.createElement('input');
    const text = document.createElement('span'), name = document.createElement('strong'), detail = document.createElement('small');
    const note = document.createElement('small');
    card.className = 'option'; card.dataset.id = row.id;
    checkbox.type = 'checkbox'; checkbox.setAttribute('aria-label', row.name);
    note.className = 'requirement'; note.id = `requirement-${cards.size}`; checkbox.setAttribute('aria-describedby', note.id);
    name.textContent = row.name; detail.textContent = kinds[row.kind];
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
}

function addFeatureChoices(plan) {
  for (const row of plan.features || []) {
    for (const id of row.required_imports) featureImports.add(id);
    const card = document.createElement('div'); card.className = 'behaviour-option feature-setting';
    const label = document.createElement('label'), checkbox = document.createElement('input');
    checkbox.id = 'enable-'+row.id.slice('feature/'.length); checkbox.type = 'checkbox';
    const title = document.createElement('strong'); title.textContent = 'Enable '+row.name;
    const description = document.createElement('p'); description.id = checkbox.id+'-description';
    description.textContent = row.description;
    checkbox.setAttribute('aria-describedby', description.id);
    const note = document.createElement('p'); note.className = 'dependency-note'; note.hidden = true;
    checkbox.setAttribute('aria-describedby', description.id+' '+checkbox.id+'-requirement');
    note.id = checkbox.id+'-requirement';
    label.append(title, checkbox); card.append(label, description, note);
    $('behaviour-options').append(card);
    featureControls.set(row.id, { checkbox, note });
    checkbox.addEventListener('change', () => changeSelection(() => {
      if (checkbox.checked) requested.add(row.id); else requested.delete(row.id);
    }));
  }
}

function addDecorationChoices(row) {
  const card = document.createElement('fieldset'); card.className = 'behaviour-option decoration-settings';
  card.id = 'new-year-stock';
  const title = document.createElement('legend'); title.textContent = 'New Year decorations';
  const explanation = document.createElement('p');
  explanation.textContent = 'Nook’s shop sells New Year items from December 26–31. He normally stocks two items, but those items differ between the original N64 game and the English GameCube release. Choose which items are available below; two are randomly selected each day during that period.';
  const value = document.createElement('input'); value.type = 'hidden'; value.value = row.default;
  behaviours[row.id] = row.default; behaviourControls.set(row.id, value);
  const actions = document.createElement('div'); actions.className = 'actions';
  const grid = document.createElement('div'); grid.className = 'decoration-grid';
  const definitions = [
    { key: 'kadomatsu', name: 'Kadomatsu', bit: 1, detail: 'N64' },
    { key: 'kagamimochi', name: 'Kagamimochi', bit: 2, detail: 'N64' },
    { key: 'festive-candle', name: 'Festive candle', importId: 'GAFE01-r0/item/3298', detail: 'GameCube import' },
    { key: 'festive-flag', name: 'Festive flag', importId: 'GAFE01-r0/item/327C', detail: 'GameCube import' },
  ];
  const commit = (mask, changeImports) => {
    const before = [...requested].sort().join('\n') + behaviours[row.id];
    changeImports();
    value.value = Object.keys(row.values).find(key => row.values[key] === mask);
    behaviours[row.id] = value.value;
    if (before !== [...requested].sort().join('\n') + behaviours[row.id]) {
      invalidate('New Year decorations changed.'); renderSelection();
    }
  };
  for (const selected of [true, false]) {
    const button = document.createElement('button'); button.type = 'button';
    button.id = selected ? 'select-decorations' : 'clear-decorations';
    button.textContent = selected ? 'Select all four' : 'Clear all four';
    button.addEventListener('click', () => commit(selected ? 0 : 3, () => {
      for (const entry of definitions) if (entry.importId) {
        if (selected) requested.add(entry.importId); else requested.delete(entry.importId);
      }
    }));
    actions.append(button);
  }
  for (const entry of definitions) {
    const label = document.createElement('label'), checkbox = document.createElement('input');
    checkbox.type = 'checkbox'; checkbox.id = `stock-${entry.key}`;
    const text = document.createElement('span'), name = document.createElement('strong'), detail = document.createElement('small');
    name.textContent = entry.name; detail.textContent = entry.detail; text.append(name, detail); label.append(checkbox, text);
    decorationControls.set(entry.key, { ...entry, checkbox }); grid.append(label);
    checkbox.addEventListener('change', () => {
      const mask = row.values[behaviours[row.id]];
      commit(entry.importId ? mask : checkbox.checked ? mask & ~entry.bit : mask | entry.bit, () => {
        if (entry.importId) { if (checkbox.checked) requested.add(entry.importId); else requested.delete(entry.importId); }
      });
    });
  }
  card.append(title, explanation, actions, grid, value); $('behaviour-options').append(card);
}
for (const [name, dialogId] of [['villagers', 'villager-dialog'], ['items', 'item-dialog']]) {
  const dialog = $(dialogId);
  $(`open-${name}`).addEventListener('click', () => dialog.showModal());
  $(`close-${name}`).addEventListener('click', () => dialog.close());
  dialog.addEventListener('close', () => $(`open-${name}`).focus());
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const box = dialog.getBoundingClientRect();
    if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) dialog.close();
  });
}
for (const input of inputs) input.addEventListener('change', () => {
  const native = input.id === 'n64';
  $(native ? 'n64-name' : 'gc-name').textContent = input.files[0]?.name || 'No file chosen';
  $(native ? 'n64-field' : 'gc-field').classList.toggle('selected', Boolean(input.files[0]));
  invalidate('Game files changed. Build again to verify this pair of inputs.');
  if (fileError()) error(fileError());
});
$('search').addEventListener('input', filter); $('villager-search').addEventListener('input', filter); $('kind').addEventListener('change', filter);
for (const [button, include, visible, kind] of [['select-visible', true, true, 'items'], ['clear-visible', false, true, 'items'],
  ['select-villagers', true, true, 'villager'], ['clear-villagers', false, true, 'villager'],
  ['select-items', true, false, 'items'], ['clear-items', false, false, 'items'],
  ['select-all', true, false, 'all'], ['clear-all', false, false, 'all']]) {
  $(button).addEventListener('click', () => changeSelection(() => {
    if (kind === 'all') for (const id of featureControls.keys()) {
      if (include) requested.add(id); else requested.delete(id);
    }
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
    invalidate('Shared settings loaded. Review your choices before building.');
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
  const custom = Boolean(selection.requested.length || selection.enabled.length || selection.behaviours_changed);
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
    const current = await loadBundle();
    await loadReview(current.bundle, current.plan);
    loaded = current; addChoices(current.plan); $('selection-controls').disabled = false;
    renderSelection(); filter(); status('Choose both original game files. Imports are optional.');
  } catch (problem) { loaded = null; error(problem.message || 'The import catalogue could not be loaded.'); }
}
init();
