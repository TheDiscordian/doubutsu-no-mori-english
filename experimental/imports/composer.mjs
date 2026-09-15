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
  integer(plan.base_size, 0x101000, MAX); integer(plan.stable_size, 0x101000, MAX);
  for (const key of ['base_sha256', 'stable_sha256', 'base_report_sha256']) hash(plan[key]);
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
    require(['furniture', 'clothing', 'villager'].includes(option.kind) &&
      option.id.includes(option.kind === 'villager' ? '/villager/' : '/item/'), 'Invalid import kind.');
    require(typeof option.name === 'string' && option.name.length > 0 && option.name.length <= 128,
      'Invalid import name.');
    array(option.dependencies, 0, 2048); array(option.disable, 1, 16);
    hexSize(option.profile_hex, 192, 192);
    require(bytes(option.profile_hex).some(n => n), 'Import has an empty save profile.');
    for (const row of option.disable) {
      const size = field(row, 1, 4); hexSize(row.after, size, size);
    }
    options.set(option.id, option);
  }
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
  field(plan.profile, 192, 192);
  const fullProfile = new Uint8Array(192);
  for (const option of options.values()) {
    bytes(option.profile_hex).forEach((n, i) => {
      require(!(fullProfile[i] & n), 'Two import options own the same saved identity.');
      fullProfile[i] |= n;
    });
  }
  require(hex(fullProfile) === plan.profile.before, 'Incomplete installed save profile.');
  for (const table of plan.tables) {
    integer(table.width, 1, 16); array(table.rows, 1, 2048); array(table.counts, 1, 16);
    field(table, table.rows.length * table.width, table.rows.length * table.width);
    const seen = new Set();
    for (const row of table.rows) {
      require(options.has(row.id) && !seen.has(row.id), 'Unknown or repeated catalogue member.');
      seen.add(row.id); hexSize(row.hex, table.width, table.width);
    }
    require(table.rows.map(row => row.hex).join('') === table.before, 'Changed catalogue ordering.');
    for (const count of table.counts) {
      field(count, 4, 4); integer(count.base, 0, 0xffffffff - table.rows.length);
      require(parseInt(count.before, 16) === count.base + table.rows.length, 'Changed catalogue count.');
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

export function resolveSelection(plan, requested) {
  const options = validatePlan(plan);
  array(requested, 0, 4096);
  require(requested.every(id => typeof id === 'string' && options.has(id)), 'Unknown or unimplemented import.');
  const chosen = [...new Set(requested)].sort(), enabled = new Set(chosen), reasons = new Map(), pending = [...chosen];
  while (pending.length) {
    const id = pending.pop();
    for (const dependency of options.get(id).dependencies) {
      if (!reasons.has(dependency)) reasons.set(dependency, new Set());
      reasons.get(dependency).add(id);
      if (!enabled.has(dependency)) { enabled.add(dependency); pending.push(dependency); }
    }
  }
  const profile = new Uint8Array(192);
  for (const id of enabled) bytes(options.get(id).profile_hex).forEach((n, i) => { profile[i] |= n; });
  return { requested: chosen, enabled: [...enabled].sort(), required: [...enabled].filter(id => !chosen.includes(id)).sort(),
    dependency_reasons: Object.fromEntries([...reasons].sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0)
      .map(([key, parents]) => [key, [...parents].sort()])), profile_hex: hex(profile) };
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

export async function composeSelection(source, plan, requested) {
  // Take copies before awaiting crypto so a caller cannot change selections or
  // source data while the original build is being verified.
  plan = structuredClone(plan);
  const selection = resolveSelection(plan, [...requested]);
  require(source instanceof Uint8Array, 'Invalid composition source.');
  const empty = !selection.enabled.length;
  require(source.length === (empty ? plan.stable_size : plan.base_size), 'Wrong composition cartridge size.');
  const output = source.slice();
  require(await sha256(output) === (empty ? plan.stable_sha256 : plan.base_sha256), 'Composition base checksum mismatch.');
  const writes = [], enabled = new Set(selection.enabled);
  if (!empty) {
    // Check every declared field, including selected records that remain
    // untouched, before applying the first write to this private copy.
    const fields = [plan.profile, plan.header, ...plan.options.flatMap(row => row.disable),
      ...plan.tables.flatMap(row => [row, ...row.counts]), ...plan.crc32];
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
    for (const option of plan.options) if (!enabled.has(option.id)) {
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
  if (selection.enabled.length === plan.options.length) require(outputHash === plan.base_sha256, 'All-selected output differs from the pinned cartridge.');
  return { output, receipt: { format: 'AFV3-BROWSER-SELECTION-1', ...selection,
    profile_sha256: await sha256(bytes(selection.profile_hex)), output_sha256: outputHash,
    base_sha256: empty ? plan.stable_sha256 : plan.base_sha256, base_report_sha256: plan.base_report_sha256,
    runtime_abi: empty ? null : plan.runtime_abi, writes: writes.sort((a, b) => a.offset - b.offset),
    experimental: true, web_patcher_enabled: false, playable_handoff: false,
    save_compatibility: empty ? 'V2 baseline. Do not load V3 import saves.' :
      'Format 2: retain every import selected for your save. Removing imports is not a save migration. Do not load this save in V2 or an older build missing these imports. Ordinary cross-profile reload is unverified.' } };
}
