/* Experimental, unserved selection engine. Item rules are generated, not maintained here. */
import { sha256 } from '../../web/core.mjs';

const MAX = 64 * 1024 * 1024;
const fail = message => { throw new Error(message); };
const require = (ok, message) => { if (!ok) fail(message); };
const view = bytes => new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
const hex = bytes => [...bytes].map(n => n.toString(16).padStart(2, '0')).join('');
const bytes = value => Uint8Array.from(value.match(/../g) || [], n => parseInt(n, 16));
function integer(n, low, high) {
  require(Number.isSafeInteger(n) && n >= low && n <= high, 'Invalid composition integer.');
}
function array(value, min, max) {
  require(Array.isArray(value), 'Invalid composition list.'); integer(value.length, min, max);
}
function hash(value) { require(typeof value === 'string' && /^[0-9a-f]{64}$/.test(value), 'Invalid composition hash.'); }
function hexSize(value, min, max) {
  require(typeof value === 'string' && /^(?:[0-9a-f]{2})+$/.test(value), 'Invalid composition bytes.');
  integer(value.length / 2, min, max); return value.length / 2;
}
function equal(a, b) { return a.length === b.length && a.every((value, i) => value === b[i]); }

export function validatePlan(plan) {
  require(plan?.format === 'AFV3-BROWSER-COMPOSITION-1' && plan.donor === 'GAFE01-r0' &&
    plan.experimental === true && plan.web_patcher_enabled === false, 'Unsupported experimental import plan.');
  integer(plan.runtime_abi, 1, 65535);
  const pipeline = plan.scope === 'v3-pipeline';
  require(plan.scope === undefined || pipeline, 'Unsupported import scope.');
  integer(plan.base_size, 0x101000, MAX); integer(plan.stable_size, 0x101000, MAX);
  for (const key of ['base_sha256', 'stable_sha256', 'base_report_sha256']) hash(plan[key]);
  const surfaces = plan.surface_profile_hex !== undefined;
  if (surfaces) hexSize(plan.surface_profile_hex, 64, 64);
  const creatures = plan.creature_profile_hex !== undefined;
  if (creatures) hexSize(plan.creature_profile_hex, 4, 4);
  if (plan.save_compatibility !== undefined) require(typeof plan.save_compatibility === 'string' &&
    plan.save_compatibility.length > 0 && plan.save_compatibility.length <= 2048, 'Invalid save compatibility warning.');
  array(plan.options, 1, 2048); array(plan.tables, 1, 16); array(plan.crc32, 1, 16);
  const options = new Map(), regions = [];
  const field = (row, min, max) => {
    const size = hexSize(row?.before, min, max);
    integer(row.offset, 0, plan.base_size - size);
    regions.push([row.offset, row.offset + size]); return size;
  };
  for (const option of plan.options) {
    require(typeof option.id === 'string' && /^GAFE01-r0\/(item|villager)\/[0-9A-F]{4}$/.test(option.id) &&
      !options.has(option.id), 'Invalid or repeated import identity.');
    require(['furniture', 'clothing', 'equipment', 'villager', 'floor', 'wall', 'fish', 'insect', 'diary', 'carried'].includes(option.kind) &&
      option.id.includes(option.kind === 'villager' ? '/villager/' : '/item/'), 'Invalid import kind.');
    require(typeof option.name === 'string' && option.name.length > 0 && option.name.length <= 128,
      'Invalid import name.');
    if (option.dependency_only !== undefined) require(pipeline && option.dependency_only === true &&
      option.kind === 'clothing' && typeof option.reason === 'string' && option.reason.length > 0,
      'Invalid villager resource dependency.');
    array(option.dependencies, 0, 2048); array(option.disable, option.kind === 'carried' ? 0 : 1, 16);
    hexSize(option.profile_hex, 192, 192);
    if (surfaces) hexSize(option.surface_profile_hex, 64, 64);
    if (creatures) hexSize(option.creature_profile_hex, 4, 4);
    const isCreature = ['fish', 'insect'].includes(option.kind);
    require(isCreature ? creatures && bytes(option.creature_profile_hex).some(n => n) :
      !creatures || !bytes(option.creature_profile_hex).some(n => n), 'Wrong-category creature profile.');
    const isSurface = ['floor', 'wall'].includes(option.kind);
    const isCarried = option.kind === 'carried';
    if (isCarried) {
      integer(option.carried_mask, 1, 127);
      require(!(option.carried_mask & (option.carried_mask - 1)) && !option.disable.length,
        'Invalid carried-family identity.');
    } else require(option.carried_mask === undefined, 'Wrong-category carried identity.');
    require(isCarried ? !bytes(option.profile_hex).some(n => n) &&
      (!surfaces || !bytes(option.surface_profile_hex).some(n => n)) :
      isSurface ? surfaces && bytes(option.surface_profile_hex).some(n => n) && !bytes(option.profile_hex).some(n => n) :
      bytes(option.profile_hex).some(n => n) && (!surfaces || !bytes(option.surface_profile_hex).some(n => n)),
      'Import has an empty or wrong-category save profile.');
    for (const row of option.disable) {
      const size = field(row, 1, 4); hexSize(row.after, size, size);
    }
    options.set(option.id, option);
  }
  const features = new Map(), featureItems = new Set();
  if (plan.features !== undefined) array(plan.features, 1, 32);
  for (const row of plan.features || []) {
    require(pipeline && typeof row.id === 'string' && /^feature\/[a-z][a-z0-9-]{0,63}$/.test(row.id) &&
      !features.has(row.id), 'Invalid or repeated feature choice.');
    for (const key of ['name', 'description']) require(typeof row[key] === 'string' && row[key].length > 0 && row[key].length <= 1024,
      'Invalid feature description.');
    array(row.required_imports, 0, 2048);
    if (row.required_by_imports !== undefined) {
      array(row.required_by_imports, 1, 2048);
      require(row.required_imports.length === 0 && new Set(row.required_by_imports).size === row.required_by_imports.length &&
        row.required_by_imports.every(id => options.has(id)), 'Invalid item-to-feature requirements.');
    }
    if (row.disable !== undefined) {
      array(row.disable, 1, 32);
      for (const patch of row.disable) {
        const size = field(patch, 4, 65536); hexSize(patch.after, size, size);
      }
    }
    require(row.required_imports.length > 0 || row.disable?.length > 0, 'Feature has no items or runtime controls.');
    for (const id of row.required_imports) {
      require(options.has(id) && !options.get(id).dependency_only && !featureItems.has(id), 'Missing or repeated feature item.');
      featureItems.add(id);
    }
    features.set(row.id, row);
  }
  const pending = new Set();
  const pendingRows = new Map();
  if (plan.pending_options !== undefined) {
    array(plan.pending_options, 1, 2048); hash(plan.all_selected_sha256);
    for (const row of plan.pending_options) {
      require(typeof row.id === 'string' && /^GAFE01-r0\/item\/[0-9A-F]{4}$/.test(row.id) &&
        !options.has(row.id) && !pending.has(row.id) && row.selectable === false &&
        (pipeline ? ['furniture', 'clothing', 'equipment', 'floor', 'wall', 'diary', 'carried'].includes(row.kind) :
          row.kind === 'diary') && typeof row.name === 'string' && row.name.length > 0 && row.name.length <= 128 &&
        typeof row.reason === 'string' && row.reason.length > 0 && row.reason.length <= 1024,
        'Invalid or selectable pending import.');
      array(row.disable, pipeline && row.kind === 'carried' ? 0 : 1, 16);
      if (row.profile_hex !== undefined) {
        require(pipeline, 'Unexpected pending saved identity.');
        hexSize(row.profile_hex, 192, 192);
        if (surfaces) hexSize(row.surface_profile_hex, 64, 64);
        if (creatures) {
          hexSize(row.creature_profile_hex, 4, 4);
          require(!bytes(row.creature_profile_hex).some(n => n), 'Deferred creature identity.');
        }
        if (row.kind === 'carried') {
          integer(row.carried_mask, 1, 127);
          require(!(row.carried_mask & (row.carried_mask - 1)) && !row.disable.length,
            'Invalid deferred carried identity.');
        }
      }
      for (const patch of row.disable) {
        const size = field(patch, 1, 4); hexSize(patch.after, size, size);
      }
      pending.add(row.id);
      pendingRows.set(row.id, row);
    }
  } else if (plan.all_selected_sha256 !== undefined) hash(plan.all_selected_sha256);
  // A cyclic dependency is a malformed catalogue, not an excuse to loop or to
  // silently treat a set of broken options as self-sufficient.
  const visiting = new Set(), visited = new Set();
  function visit(id) {
    require(options.has(id) && !visiting.has(id), 'Missing or cyclic import dependency.');
    if (visited.has(id)) return;
    visiting.add(id);
    const deps = options.get(id).dependencies;
    require(new Set(deps).size === deps.length, 'Repeated import dependency.');
    for (const child of deps) visit(child);
    visiting.delete(id); visited.add(id);
  }
  for (const id of options.keys()) visit(id);
  // Acquisition can require two item choices together. Declare that group
  // explicitly rather than accepting a cycle in resource dependencies.
  if (plan.import_groups !== undefined) array(plan.import_groups, 1, 32);
  const linkedIds = new Set(), linkedMembers = new Set();
  for (const group of plan.import_groups || []) {
    require(typeof group.id === 'string' && /^[a-z][a-z0-9-]{0,63}$/.test(group.id) &&
      !linkedIds.has(group.id), 'Invalid or repeated mutual import group.');
    linkedIds.add(group.id); array(group.members, 2, 2048);
    for (const id of group.members) {
      require(options.has(id) && !options.get(id).dependency_only && !linkedMembers.has(id),
        'Missing, repeated, or unavailable mutual import member.');
      linkedMembers.add(id);
    }
  }
  field(plan.profile, 192, 192);
  const fullProfile = new Uint8Array(192);
  const installed = [...options.values(), ...pendingRows.values()].filter(row => row.profile_hex !== undefined);
  for (const option of installed) {
    bytes(option.profile_hex).forEach((n, i) => {
      require(!(fullProfile[i] & n), 'Two import options own the same saved identity.');
      fullProfile[i] |= n;
    });
  }
  require(hex(fullProfile) === plan.profile.before, 'Incomplete installed save profile.');
  if (surfaces) {
    const fullSurface = new Uint8Array(64);
    for (const option of installed) bytes(option.surface_profile_hex).forEach((n, i) => {
      require(!(fullSurface[i] & n), 'Two surface options own the same saved identity.'); fullSurface[i] |= n;
    });
    require(hex(fullSurface) === plan.surface_profile_hex, 'Incomplete installed surface profile.');
  }
  if (creatures) {
    const fullCreature = new Uint8Array(4);
    for (const option of installed) bytes(option.creature_profile_hex).forEach((n, i) => {
      require(!(fullCreature[i] & n), 'Two creature options own the same saved identity.'); fullCreature[i] |= n;
    });
    require(hex(fullCreature) === plan.creature_profile_hex, 'Incomplete installed creature profile.');
    require(fullCreature[2] < 2 && fullCreature[3] === 0, 'Invalid creature saved identity range.');
  }
  for (const table of plan.tables) {
    integer(table.width, 1, 16); array(table.rows, 1, 2048); array(table.counts, 0, 16);
    const capacity = table.capacity ?? table.rows.length; integer(capacity, table.rows.length, 2048);
    field(table, capacity * table.width, capacity * table.width);
    const seen = new Set();
    for (const row of table.rows) {
      require((options.has(row.id) || pending.has(row.id)) && !seen.has(row.id), 'Unknown or repeated catalogue member.');
      seen.add(row.id); hexSize(row.hex, table.width, table.width);
    }
    require(table.rows.map(row => row.hex).join('') + '00'.repeat((capacity - table.rows.length) * table.width) ===
      table.before, 'Changed catalogue ordering.');
    for (const count of table.counts) {
      field(count, 4, 4); integer(count.base, 0, 0xffffffff - table.rows.length);
      require(parseInt(count.before, 16) === count.base + table.rows.length, 'Changed catalogue count.');
    }
  }
  const behaviourIds = new Set();
  if (plan.behaviours !== undefined) array(plan.behaviours, 1, 32);
  for (const row of plan.behaviours || []) {
    require(typeof row.id === 'string' && /^[a-z][a-z0-9-]{0,63}$/.test(row.id) && !behaviourIds.has(row.id),
      'Invalid or repeated behaviour setting.');
    behaviourIds.add(row.id);
    if (row.pipeline_unavailable !== undefined) require(pipeline && row.pipeline_unavailable === true &&
      ['holiday-calendar', 'tournament-measurements', 'birthday-presentation'].includes(row.id),
      'Invalid unavailable behaviour setting.');
    for (const key of ['name', 'scope', 'description']) require(typeof row[key] === 'string' &&
      row[key].length > 0 && row[key].length < 1024, 'Invalid behaviour description.');
    const decorationChoice = row.id === 'new-year-stock' && row.default === 'both' && row.values &&
      Object.keys(row.values).length === 4 && row.values.both === 0 && row.values.kadomatsu === 2 &&
      row.values.kagamimochi === 1 && row.values.neither === 3;
    require(row.id === 'new-year-stock' ? decorationChoice : (row.values && Object.keys(row.values).length === 2 && row.values.N64 === 0 && row.values.GameCube === 1 &&
      row.default === 'N64'), 'Unsupported behaviour choices.');
    field(row, 4, 4); require(row.before === '00000000', 'Changed behaviour default.');
    if (row.patches !== undefined) {
      array(row.patches, 1, 16);
      for (const patch of row.patches) { field(patch, 4, 1024); hexSize(patch.after, patch.before.length / 2, patch.before.length / 2); }
    }
    if (row.required_imports !== undefined) {
      array(row.required_imports, 1, 16);
      require(new Set(row.required_imports).size === row.required_imports.length && row.required_imports.every(id => options.has(id)), 'Unavailable behaviour import dependency.');
    }
  }
  const groupIds = new Set();
  const carriedBits = new Set();
  for (const option of options.values()) if (option.kind === 'carried') {
    require(!carriedBits.has(option.carried_mask), 'Duplicate carried-family identity.');
    carriedBits.add(option.carried_mask);
  }
  if (plan.selection_masks !== undefined) array(plan.selection_masks, 1, 32);
  const maskOwners = new Set();
  for (const row of plan.selection_masks || []) {
    field(row, 4, 4); array(row.members, 1, 32);
    let full = 0; const members = new Set();
    for (const member of row.members) {
      require((options.get(member.id) || pendingRows.get(member.id))?.kind === 'carried' && !members.has(member.id),
        'Unknown or duplicate masked selection.');
      integer(member.mask, 1, 0x7fffffff);
      require(!(full & member.mask), 'Overlapping selection mask bits.');
      full |= member.mask; members.add(member.id); maskOwners.add(member.id);
    }
    require(parseInt(row.before, 16) === full, 'Changed complete selection mask.');
  }
  for (const option of installed) if (option.kind === 'carried')
    require(maskOwners.has(option.id), 'Carried option has no installed selection field.');
  if (plan.runtime_groups !== undefined) array(plan.runtime_groups, 1, 32);
  for (const group of plan.runtime_groups || []) {
    require(typeof group.id === 'string' && /^[a-z][a-z0-9-]{0,63}$/.test(group.id) && !groupIds.has(group.id),
      'Invalid or repeated runtime group.');
    groupIds.add(group.id);
    require(pipeline ? typeof group.forced_disabled === 'boolean' &&
      (group.forced_disabled || ['diary-holidays', 'carried-quest'].includes(group.id)) : group.forced_disabled === undefined,
      'Invalid feature activation scope.');
    array(group.any_imports, 0, 2048); array(group.any_behaviours, 0, 32); array(group.fields, 1, 64);
    if (group.any_features !== undefined) array(group.any_features, 1, 32);
    require((group.any_features || []).every(id => features.has(id)) &&
      new Set(group.any_features || []).size === (group.any_features || []).length, 'Unknown or repeated runtime feature.');
    require(group.any_imports.length + group.any_behaviours.length + (group.any_features || []).length > 0 &&
      new Set(group.any_imports).size === group.any_imports.length &&
      group.any_imports.every(id => options.has(id) || pending.has(id)),
      'Unknown or repeated runtime dependency.');
    for (const condition of group.any_behaviours) {
      const setting = (plan.behaviours || []).find(row => row.id === condition.id);
      require(setting && Object.hasOwn(setting.values, condition.value) && condition.value !== setting.default,
        'Unavailable runtime behaviour dependency.');
    }
    for (const row of group.fields) {
      field(row, 4, 4); integer(row.enabled, 0, 0xffffffff); integer(row.disabled, 0, 0xffffffff);
      require(parseInt(row.before, 16) === row.enabled && row.enabled !== row.disabled,
        'Changed shared runtime activation.');
    }
  }
  for (const row of plan.crc32) {
    field(row, 4, 4); integer(row.length, 1, MAX);
    integer(row.start, 0, plan.base_size - row.length);
    require(row.offset + 4 <= row.start || row.offset >= row.start + row.length, 'Self-referential resource checksum.');
  }
  // A later checksum cannot change data already covered by an earlier one.
  for (const [i, row] of plan.crc32.entries()) for (const later of plan.crc32.slice(i + 1)) {
    require(later.offset + 4 <= row.start || later.offset >= row.start + row.length,
      'Resource checksums are in the wrong dependency order.');
  }
  field(plan.header, 8, 8); require(plan.header.offset === 0x10, 'Invalid N64 checksum destination.');
  for (const row of plan.crc32) require(row.start >= 0x18, 'Resource checksum includes the later cartridge checksum.');
  regions.sort((a, b) => a[0] - b[0]);
  for (let i = 1; i < regions.length; i++) require(regions[i][0] >= regions[i - 1][1], 'Overlapping composition fields.');
  return options;
}

export function resolveSelection(plan, requested, behaviours = {}) {
  const options = validatePlan(plan);
  require(behaviours !== null && typeof behaviours === 'object' && !Array.isArray(behaviours), 'Invalid behaviour settings.');
  array(requested, 0, 4096);
  const features = new Map((plan.features || []).map(row => [row.id, row]));
  const featureItems = new Map((plan.features || []).flatMap(row => row.required_imports.map(id => [id, row.id])));
  require(requested.every(id => typeof id === 'string' && (features.has(id) ||
    options.has(id) && !options.get(id).dependency_only && !featureItems.has(id))),
    'Unknown or unimplemented standalone import.');
  const chosen = [...new Set(requested)].sort(), enabled = new Set(chosen.filter(id => !features.has(id))), reasons = new Map(), pending = [...enabled];
  for (const key of chosen) if (features.has(key)) for (const id of features.get(key).required_imports) {
    if (!reasons.has(id)) reasons.set(id, new Set()); reasons.get(id).add(key);
    if (!enabled.has(id)) { enabled.add(id); pending.push(id); }
  }
  for (const row of plan.behaviours || []) if ((behaviours[row.id] || row.default) === 'GameCube') {
    for (const id of row.required_imports || []) {
      if (!reasons.has(id)) reasons.set(id, new Set()); reasons.get(id).add(row.id);
      if (!enabled.has(id)) { enabled.add(id); pending.push(id); }
    }
  }
  const peers = new Map();
  for (const group of plan.import_groups || []) for (const id of group.members)
    peers.set(id, group.members.filter(child => child !== id));
  while (pending.length) {
    const id = pending.pop();
    for (const dependency of new Set([...options.get(id).dependencies, ...(peers.get(id) || [])])) {
      if (!reasons.has(dependency)) reasons.set(dependency, new Set());
      reasons.get(dependency).add(id);
      if (!enabled.has(dependency)) { enabled.add(dependency); pending.push(dependency); }
    }
  }
  require([...enabled].every(id => !featureItems.has(id) || chosen.includes(featureItems.get(id))), 'An item requires a disabled feature.');
  const featureReasons = Object.fromEntries([...features.values()].map(row =>
    [row.id, (row.required_by_imports || []).filter(id => enabled.has(id)).sort()])
    .filter(([, ids]) => ids.length).sort(([a], [b]) => a < b ? -1 : 1));
  const enabledFeatures = [...new Set([...chosen.filter(id => features.has(id)), ...Object.keys(featureReasons)])].sort();
  const profile = new Uint8Array(192);
  const surfaceProfile = new Uint8Array(64);
  const creatureProfile = new Uint8Array(4);
  for (const id of enabled) bytes(options.get(id).profile_hex).forEach((n, i) => { profile[i] |= n; });
  if (plan.surface_profile_hex !== undefined) for (const id of enabled)
    bytes(options.get(id).surface_profile_hex).forEach((n, i) => { surfaceProfile[i] |= n; });
  if (plan.creature_profile_hex !== undefined) for (const id of enabled)
    bytes(options.get(id).creature_profile_hex).forEach((n, i) => { creatureProfile[i] |= n; });
  require(behaviours !== null && typeof behaviours === 'object' && !Array.isArray(behaviours), 'Invalid behaviour settings.');
  const definitions = new Map((plan.behaviours || []).map(row => [row.id, row]));
  require(Object.keys(behaviours).every(id => definitions.has(id)), 'Unknown or unavailable behaviour setting.');
  require(Object.keys(behaviours).every(id => !definitions.get(id).pipeline_unavailable), 'Behaviour setting is unavailable in this V3 profile.');
  const resolved = {}, rows = [...definitions.values()].sort((a, b) => a.id < b.id ? -1 : 1);
  for (const row of rows) {
    const value = Object.hasOwn(behaviours, row.id) ? behaviours[row.id] : row.default;
    require(typeof value === 'string' && Object.hasOwn(row.values, value), 'Unsupported behaviour value.');
    resolved[row.id] = value;
  }
  return { requested: chosen, enabled: [...enabled].sort(), required: [...enabled].filter(id => !chosen.includes(id)).sort(),
    ...(features.size ? { enabled_features: enabledFeatures, feature_dependency_reasons: featureReasons } : {}),
    ...(plan.scope === undefined ? {} : { scope: plan.scope }),
    dependency_reasons: Object.fromEntries([...reasons].sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0)
      .map(([key, parents]) => [key, [...parents].sort()])), profile_hex: hex(profile),
    ...(plan.surface_profile_hex === undefined ? {} : { surface_profile_hex: hex(surfaceProfile) }),
    ...(plan.creature_profile_hex === undefined ? {} : { creature_profile_hex: hex(creatureProfile) }),
    ...(plan.selection_masks === undefined ? {} : { carried_mask:
      [...enabled].reduce((mask, id) => mask | (options.get(id).carried_mask || 0), 0) }),
    ...(plan.behaviours === undefined ? {} : { behaviours: resolved,
      behaviours_changed: rows.some(row => resolved[row.id] !== row.default) }) };
}

const crcTable = Uint32Array.from({ length: 256 }, (_, index) => {
  let value = index;
  for (let bit = 0; bit < 8; bit++) value = value & 1 ? (value >>> 1) ^ 0xedb88320 : value >>> 1;
  return value >>> 0;
});
export function crc32(data) {
  let value = 0xffffffff;
  for (const byte of data) value = (value >>> 8) ^ crcTable[(value ^ byte) & 255];
  return (value ^ 0xffffffff) >>> 0;
}

export function n64Checksum(data) {
  require(data instanceof Uint8Array && data.length >= 0x101000, 'ROM too short for CIC checksum.');
  let t1 = 0xf8ca4ddc, t2 = t1, t3 = t1, t4 = t1, t5 = t1, t6 = t1;
  const input = view(data);
  for (let at = 0x1000; at < 0x101000; at += 4) {
    const d = input.getUint32(at), total = (t6 + d) >>> 0;
    if (total < t6) t4 = (t4 + 1) >>> 0;
    t6 = total; t3 = (t3 ^ d) >>> 0;
    const shift = d & 31, r = ((d << shift) | (d >>> ((32 - shift) & 31))) >>> 0;
    t5 = (t5 + r) >>> 0;
    t2 = (t2 ^ (t2 > d ? r : t6 ^ d)) >>> 0;
    t1 = (t1 + ((t5 ^ d) >>> 0)) >>> 0;
  }
  const result = new Uint8Array(8);
  view(result).setUint32(0, (t6 ^ t4 ^ t3) >>> 0); view(result).setUint32(4, (t5 ^ t2 ^ t1) >>> 0);
  return result;
}

export async function composeSelection(source, plan, requested, behaviours = {}) {
  // Take copies before awaiting crypto so a caller cannot change selections or
  // source data while the original build is being verified.
  plan = structuredClone(plan);
  const selection = resolveSelection(plan, [...requested], structuredClone(behaviours));
  require(source instanceof Uint8Array, 'Invalid composition source.');
  const empty = !selection.requested.length && !selection.enabled.length && !selection.behaviours_changed;
  require(source.length === (empty ? plan.stable_size : plan.base_size), 'Wrong composition cartridge size.');
  const output = source.slice();
  require(await sha256(output) === (empty ? plan.stable_sha256 : plan.base_sha256), 'Composition base checksum mismatch.');
  const writes = [], enabled = new Set(selection.enabled);
  if (!empty) {
    // Check every declared field, including selected records that remain
    // untouched, before applying the first write to this private copy.
    const fields = [plan.profile, plan.header, ...plan.options.flatMap(row => row.disable),
      ...(plan.features || []).flatMap(row => row.disable || []),
      ...(plan.pending_options || []).flatMap(row => row.disable),
      ...(plan.runtime_groups || []).flatMap(row => row.fields),
      ...(plan.selection_masks || []),
      ...plan.tables.flatMap(row => [row, ...row.counts]), ...plan.crc32, ...(plan.behaviours || []),
      ...(plan.behaviours || []).flatMap(row => row.patches || [])];
    for (const field of fields) {
      const before = bytes(field.before);
      require(equal(output.subarray(field.offset, field.offset + before.length), before), 'Changed composition field.');
    }
    for (const row of plan.crc32) require(crc32(output.subarray(row.start, row.start + row.length)) === parseInt(row.before, 16),
      'Changed resident resource checksum.');
    require(equal(n64Checksum(output), bytes(plan.header.before)), 'Changed source cartridge checksum.');
    function write(field, after) {
      if (hex(after) === field.before) return;
      writes.push({ offset: field.offset, before: field.before, after: hex(after) }); output.set(after, field.offset);
    }
    write(plan.profile, bytes(selection.profile_hex));
    for (const feature of plan.features || []) if (!selection.enabled_features.includes(feature.id))
      for (const patch of feature.disable || []) write(patch, bytes(patch.after));
    for (const row of plan.behaviours || []) {
      const value = new Uint8Array(4); view(value).setUint32(0, row.values[selection.behaviours[row.id]]);
      write(row, value);
      if (selection.behaviours[row.id] === 'GameCube') for (const patch of row.patches || []) write(patch, bytes(patch.after));
    }
    for (const group of plan.runtime_groups || []) {
      const active = !group.forced_disabled && (group.any_imports.some(id => enabled.has(id)) ||
        group.any_behaviours.some(row => selection.behaviours?.[row.id] === row.value) ||
        (group.any_features || []).some(id => selection.enabled_features?.includes(id)));
      for (const row of group.fields) {
        const value = new Uint8Array(4); view(value).setUint32(0, active ? row.enabled : row.disabled);
        write(row, value);
      }
    }
    for (const option of plan.options) if (!enabled.has(option.id)) {
      for (const field of option.disable) write(field, bytes(field.after));
    }
    for (const row of plan.selection_masks || []) {
      const mask = row.members.reduce((value, member) => enabled.has(member.id) ? value | member.mask : value, 0);
      const value = new Uint8Array(4); view(value).setUint32(0, mask); write(row, value);
    }
    for (const option of plan.pending_options || []) {
      for (const field of option.disable) write(field, bytes(field.after));
    }
    for (const table of plan.tables) {
      const selected = table.rows.filter(row => enabled.has(row.id));
      const packed = new Uint8Array(table.before.length / 2);
      selected.forEach((row, i) => packed.set(bytes(row.hex), i * table.width));
      write(table, packed);
      for (const count of table.counts) {
        const value = new Uint8Array(4); view(value).setUint32(0, count.base + selected.length); write(count, value);
      }
    }
    for (const row of plan.crc32) {
      const value = new Uint8Array(4); view(value).setUint32(0, crc32(output.subarray(row.start, row.start + row.length)));
      write(row, value);
    }
    write(plan.header, n64Checksum(output));
  }
  const outputHash = await sha256(output);
  const controlledItems = new Set((plan.features || []).flatMap(row => row.required_imports));
  if (selection.requested.length === plan.options.filter(row => !row.dependency_only && !controlledItems.has(row.id)).length + (plan.features || []).length && !selection.behaviours_changed)
    require(outputHash === (plan.all_selected_sha256 || plan.base_sha256),
      'All-selected output differs from the pinned supported selection.');
  return { output, receipt: { format: 'AFV3-BROWSER-SELECTION-1', ...selection,
    profile_sha256: await sha256(bytes(selection.profile_hex)), output_sha256: outputHash,
    ...(selection.surface_profile_hex === undefined ? {} : {
      surface_profile_sha256: await sha256(bytes(selection.surface_profile_hex)) }),
    ...(selection.creature_profile_hex === undefined ? {} : {
      creature_profile_sha256: await sha256(bytes(selection.creature_profile_hex)) }),
    base_sha256: empty ? plan.stable_sha256 : plan.base_sha256, base_report_sha256: plan.base_report_sha256,
    runtime_abi: empty ? null : plan.runtime_abi, writes: writes.sort((a, b) => a.offset - b.offset),
    ...(plan.behaviour_save_note ? { behaviour_save_note: plan.behaviour_save_note } : {}),
    experimental: true, web_patcher_enabled: false, playable_handoff: false,
    save_compatibility: empty ? 'V2 baseline. Do not load V3 import saves.' :
      (plan.save_compatibility || 'Retain every import selected for your save. Removing imports is not a save migration. Do not load imported saves in V2 or an older incompatible build. Ordinary cross-profile reload is unverified.') } };
}
