import test from 'node:test';
import assert from 'node:assert/strict';
import { sha256 } from '../web/core.mjs';
import { validatePlan, resolveSelection, composeSelection, crc32, n64Checksum } from '../experimental/imports/composer.mjs';
import { loadReview } from '../experimental/imports/bundle.mjs';
import { exportSettings, importSettings } from '../experimental/imports/settings.mjs';

const hex = data => Buffer.from(data).toString('hex');
const id = (kind, number) => `GAFE01-r0/${kind}/${number}`;
const A = id('item', '3100'), B = id('item', '3104'), C = id('villager', '00D8');
const fromHex = s => Buffer.from(s, 'hex');
const clone = structuredClone;

async function behaviourFixture() {
  const result = await fixture();
  const { source, plan } = result;
  source.fill(0, 0x102240, 0x102244);
  source.set(fromHex('10600005'), 0x103080);
  const v = new DataView(source.buffer);
  v.setUint32(0x102200, crc32(source.subarray(0x103000, 0x103100)));
  v.setUint32(0x200, crc32(source.subarray(0x102000, 0x102300)));
  source.set(n64Checksum(source), 0x10);
  plan.crc32[0].before = hex(source.subarray(0x102200, 0x102204));
  plan.crc32[1].before = hex(source.subarray(0x200, 0x204));
  plan.header.before = hex(source.subarray(0x10, 0x18));
  plan.base_sha256 = await sha256(source);
  plan.scope = 'v3-pipeline';
  plan.options[1].kind = 'clothing';
  plan.options[1].dependency_only = true;
  plan.options[1].reason = 'Required only by a selected villager or house setting.';
  plan.behaviours = [{ id: 'starting-diary', name: 'Start with a diary',
    scope: 'New houses', description: 'Diaries start inside houses.',
    default: 'N64', values: { N64: 0, GameCube: 1 },
    offset: 0x102240, before: '00000000', required_imports: [B],
    patches: [{ offset: 0x103080, before: '10600005', after: '00000000' }] }];
  return result;
}

test('feature choices enable required items, never the other way around', async () => {
  const { source, plan } = await fixture();
  plan.scope = 'v3-pipeline';
  plan.features = [{id:'feature/wisp', name:'Wisp', description:'Enable Wisp and his quest items.', required_imports:[A]},
    {id:'feature/cedar-trees', name:'Cedar trees', description:'Enable cedar trees and saplings.', required_imports:[B]}];
  const wisp = resolveSelection(plan, ['feature/wisp']);
  assert.deepEqual(wisp.requested, ['feature/wisp']);
  assert.deepEqual(wisp.enabled, [A]);
  assert.deepEqual(wisp.required, [A]);
  assert.deepEqual(wisp.dependency_reasons[A], ['feature/wisp']);
  assert.deepEqual(resolveSelection(plan, []).enabled, []);
  assert.throws(() => resolveSelection(plan, [A]), /standalone/);
  assert.throws(() => resolveSelection(plan, [C]), /disabled feature/);
  assert.deepEqual(resolveSelection(plan, [C,'feature/cedar-trees']).enabled, [B,C]);
  const settings = exportSettings(plan, 'a'.repeat(64), ['feature/wisp'], {});
  assert.deepEqual(importSettings(plan, 'a'.repeat(64), settings).requested, ['feature/wisp']);
  const built = await composeSelection(source, plan, ['feature/wisp']);
  assert.deepEqual(built.receipt.required, [A]);
  for (const mutate of [p=>p.features[0].required_imports.push(A),
    p=>p.features[1].required_imports.push(A), p=>p.features[0].required_imports.push('unknown'),
    p=>p.features[0].id='not-a-feature']) {
    const bad=clone(plan); mutate(bad); assert.throws(()=>validatePlan(bad));
  }
});

test('native New Year decorations are independent checked stock flags, not platform modes', async () => {
  const { source, plan } = await behaviourFixture();
  const row = plan.behaviours[0];
  delete row.required_imports; delete row.patches;
  Object.assign(row, { id: 'new-year-stock', name: 'New Year decorations',
    default: 'both', values: { both: 0, kadomatsu: 2, kagamimochi: 1, neither: 3 } });
  for (const [setting, bits] of Object.entries(row.values)) {
    const choices = { 'new-year-stock': setting };
    const built = await composeSelection(source, plan, [A], choices);
    assert.equal(new DataView(built.output.buffer).getUint32(row.offset), bits);
    assert.equal(built.receipt.behaviours['new-year-stock'], setting);
    const shared = exportSettings(plan, '3'.repeat(64), [A], choices);
    assert.deepEqual(importSettings(plan, '3'.repeat(64), shared).behaviours, choices);
  }
  assert.throws(() => resolveSelection(plan, [], { 'new-year-stock': 'GameCube' }), /Unsupported behaviour value/);
  const bad = clone(plan); bad.behaviours[0].values.kadomatsu = 1;
  assert.throws(() => validatePlan(bad), /Unsupported behaviour choices/);
});

test('behaviour dependencies and checked conditional patches change only the selected alternative', async () => {
  const { source, plan } = await behaviourFixture();
  const n64 = await composeSelection(source, plan, [A]);
  assert.equal(hex(n64.output.subarray(0x103080, 0x103084)), '10600005');
  assert.deepEqual(n64.receipt.enabled, [A]);
  const gc = await composeSelection(source, plan, [], { 'starting-diary': 'GameCube' });
  assert.deepEqual(gc.receipt.requested, []);
  assert.deepEqual(gc.receipt.required, [B]);
  assert.deepEqual(gc.receipt.dependency_reasons[B], ['starting-diary']);
  assert.equal(hex(gc.output.subarray(0x103080, 0x103084)), '00000000');
  assert.equal(hex(source.subarray(0x103080, 0x103084)), '10600005');
  assert.deepEqual(gc.output.subarray(0x10, 0x18), n64Checksum(gc.output));
  assert.equal(new DataView(gc.output.buffer).getUint32(0x102200), crc32(gc.output.subarray(0x103000, 0x103100)));
  assert.throws(() => resolveSelection(plan, [B]), /standalone/);
  for (const mutate of [
    p => p.behaviours[0].required_imports.push(B),
    p => p.behaviours[0].required_imports.push('missing'),
    p => p.behaviours[0].patches[0].offset = p.profile.offset,
    p => p.behaviours[0].patches[0].after = '00',
  ]) {
    const changed = clone(plan); mutate(changed); assert.throws(() => validatePlan(changed));
  }
  const changed = clone(plan); changed.behaviours[0].patches[0].before = '00000000';
  await assert.rejects(composeSelection(source, changed, [A]), /Changed composition field/);
});

test('shareable settings and build receipts round-trip choices without trusting saved enabled bits', async () => {
  const { plan } = await behaviourFixture();
  const planHash = 'a'.repeat(64), choices = { 'starting-diary': 'GameCube' };
  const shared = exportSettings(plan, planHash, [C, A, C], choices);
  assert.deepEqual(shared.requested, [A, C]);
  assert.deepEqual(importSettings(plan, planHash, clone(shared)), { requested: [A, C], behaviours: choices });
  assert.equal('enabled' in shared, false);
  const receipt = { ...shared, format: 'AFV3-BROWSER-SELECTION-1', enabled: ['unknown'], profile_hex: 'bad' };
  assert.deepEqual(importSettings(plan, planHash, receipt), { requested: [A, C], behaviours: choices });
  for (const mutate of [
    p => p.format = 'other', p => p.plan_sha256 = 'b'.repeat(64),
    p => p.base_sha256 = 'b'.repeat(64), p => p.runtime_abi++, p => p.donor = 'other',
    p => p.requested = ['unknown'], p => p.requested = [B],
    p => p.behaviours = {}, p => p.behaviours['starting-diary'] = 'Unknown',
    p => p.behaviours.other = 'N64', p => p.behaviours = null,
  ]) { const changed = clone(shared); mutate(changed); assert.throws(() => importSettings(plan, planHash, changed)); }
  assert.throws(() => importSettings(plan, planHash, null));
});

test('deferred equipment and carried reviews match the checked plan exactly', async () => {
  const pending = ['equipment', 'carried'].map((kind, i) => ({ id: id('item', `253${i}`),
    name: `Deferred ${kind}`, kind, selectable: false, reason: 'Acquisition is not installed.' }));
  const plan = { base_sha256: '0'.repeat(64), scope: 'v3-pipeline', options: [], pending_options: pending };
  const originalFetch = globalThis.fetch;
  async function review(rows) {
    const raw = new TextEncoder().encode(JSON.stringify({ format: 'AFV3-BROWSER-REVIEW-1',
      base_sha256: plan.base_sha256, unavailable: rows }));
    globalThis.fetch = async () => new Response(raw);
    return loadReview({ review: { file: 'review.json', size: raw.length, sha256: await sha256(raw) } }, plan);
  }
  try {
    assert.deepEqual((await review(pending)).unavailable, pending);
    await assert.rejects(review(pending.slice(1)), /missing from the review/);
    for (const field of ['id', 'name', 'kind', 'selectable', 'reason']) {
      const changed = clone(pending);
      changed[0][field] = field === 'selectable' ? true : 'changed';
      await assert.rejects(review(changed), /Invalid unavailable/);
    }
  } finally { globalThis.fetch = originalFetch; }
});

async function fixture() {
  const source = Uint8Array.from({ length: 0x104000 }, (_, i) => (i * 31 + (i >>> 5)) & 255);
  const v = new DataView(source.buffer);
  const field = (offset, size) => ({ offset, before: hex(source.subarray(offset, offset + size)) });
  const profile = new Uint8Array(192);
  const options = [A, B, C].map((key, i) => {
    const mask = new Uint8Array(192); mask[32 + i] = 1 << i; profile[32 + i] |= mask[32 + i];
    v.setUint32(0x103000 + i * 4, 1);
    return { id: key, name: `Example ${i}`, kind: i < 2 ? 'furniture' : 'villager',
      dependencies: i === 2 ? [B] : [], profile_hex: hex(mask),
      disable: [{ ...field(0x103000 + i * 4, 4), after: '00000000' }] };
  });
  source.set(profile, 0x102000);
  source.set(fromHex('0102000001030001'), 0x102100); v.setUint32(0x102110, 0x24050004);
  const tables = [{ ...field(0x102100, 8), width: 4, rows: [{ id: A, hex: '01020000' }, { id: B, hex: '01030001' }],
    counts: [{ ...field(0x102110, 4), base: 0x24050002 }] }];
  v.setUint32(0x102200, crc32(source.subarray(0x103000, 0x103100)));
  v.setUint32(0x200, crc32(source.subarray(0x102000, 0x102300)));
  const crcs = [{ ...field(0x102200, 4), start: 0x103000, length: 0x100 },
    { ...field(0x200, 4), start: 0x102000, length: 0x300 }];
  source.set(n64Checksum(source), 0x10);
  const stable = source.slice(); stable[0x103000] = 0xaa;
  const plan = { format: 'AFV3-BROWSER-COMPOSITION-1', donor: 'GAFE01-r0', runtime_abi: 93,
    base_sha256: await sha256(source), base_size: source.length, stable_sha256: await sha256(stable),
    stable_size: stable.length, base_report_sha256: '0'.repeat(64), experimental: true, web_patcher_enabled: false,
    options, profile: field(0x102000, 192), tables, crc32: crcs, header: field(0x10, 8) };
  return { source, stable, plan };
}

test('standard CRC32, bounded CIC checksum, and view offsets', () => {
  assert.equal(crc32(new TextEncoder().encode('123456789')), 0xcbf43926);
  assert.equal(crc32(new Uint8Array()), 0);
  assert.throws(() => n64Checksum(new Uint8Array(20)), /too short/);
  const b = Uint8Array.from({ length: 0x102100 }, (_, i) => i * 23);
  assert.deepEqual(n64Checksum(b.subarray(100)), n64Checksum(b.slice(100)));
});

test('dependencies, reasons, duplicates, removal, and order independence', async () => {
  const { plan } = await fixture();
  const result = resolveSelection(plan, [C]);
  assert.deepEqual(result.enabled, [B, C]); assert.deepEqual(result.required, [B]);
  assert.deepEqual(result.dependency_reasons, { [B]: [C] });
  assert.deepEqual(resolveSelection(plan, [C, A, C]), resolveSelection(plan, [A, C]));
  assert.deepEqual(resolveSelection(plan, []).enabled, []);
  assert.deepEqual(resolveSelection(plan, [A]).required, []);
  assert.throws(() => resolveSelection(plan, ['unknown']), /Unknown/);
  assert.throws(() => resolveSelection(plan, 'all'), /list/);
});

test('mutual acquisition groups close selections without accepting dependency cycles', async () => {
  const { plan } = await fixture();
  plan.import_groups = [{ id: 'paired-acquisition', members: [B, C] }];
  for (const requested of [[B], [C], [B, C]]) {
    const selected = resolveSelection(plan, requested);
    assert.deepEqual(selected.enabled, [B, C]);
    assert.deepEqual(selected.required, [B, C].filter(id => !requested.includes(id)));
    assert.deepEqual(selected.dependency_reasons, { [B]: [C], [C]: [B] });
  }
  assert.deepEqual(resolveSelection(plan, []).enabled, []);
  assert.deepEqual(resolveSelection(plan, [A]).enabled, [A]);
  for (const groups of [
    [{ id: 'paired-acquisition', members: [B] }],
    [{ id: 'paired-acquisition', members: [B, B] }],
    [{ id: 'paired-acquisition', members: [B, 'missing'] }],
    [{ id: 'paired-acquisition', members: [B, C] }, { id: 'other', members: [A, B] }],
    [{ id: 'paired-acquisition', members: [B, C] }, { id: 'paired-acquisition', members: [A, C] }],
  ]) {
    const p = clone(plan); p.import_groups = groups;
    assert.throws(() => validatePlan(p));
  }
  const p = clone(plan); p.options[1].dependencies = [C];
  assert.throws(() => validatePlan(p), /cyclic/);
});

test('V3 retains independent built gift and spirit providers while unknown groups stay guarded', async () => {
  const { plan, source } = await fixture();
  const view = new DataView(source.buffer);
  view.setUint32(0x103200, 1);
  source.set(n64Checksum(source), 0x10);
  plan.header.before = hex(source.subarray(0x10, 0x18));
  plan.base_sha256 = await sha256(source);
  plan.all_selected_sha256 = plan.base_sha256;
  plan.scope = 'v3-pipeline';
  plan.runtime_groups = [{ id: 'diary-holidays', forced_disabled: false,
    any_imports: [A], any_behaviours: [],
    fields: [{ offset: 0x103200, before: '00000001', enabled: 1, disabled: 0 }] }];
  for (const [requested, expected] of [[[A], 1], [[B], 0]]) {
    const { output } = await composeSelection(source, plan, requested);
    assert.equal(new DataView(output.buffer).getUint32(0x103200), expected);
  }
  const invalid = clone(plan);
  invalid.runtime_groups[0].id = 'unreviewed-provider';
  assert.throws(() => validatePlan(invalid), /feature activation scope/);
  for (const groupId of ['diary-holidays', 'carried-quest', 'savings-account']) {
    plan.runtime_groups[0].id = groupId;
    validatePlan(plan);
    const { output } = await composeSelection(source, plan, [A]);
    assert.equal(new DataView(output.buffer).getUint32(0x103200), 1);
  }
  invalid.runtime_groups[0].forced_disabled = true;
  validatePlan(invalid);
  delete invalid.runtime_groups[0].forced_disabled;
  assert.throws(() => validatePlan(invalid), /feature activation scope/);
});

test('selected rows pack, disabled fields clear, checksums update, and inputs stay untouched', async () => {
  const { plan, source } = await fixture(), original = source.slice();
  const { output, receipt } = await composeSelection(source, plan, [C]);
  const v = new DataView(output.buffer);
  assert.equal(v.getUint32(0x103000), 0); assert.equal(v.getUint32(0x103004), 1);
  assert.equal(hex(output.subarray(0x102100, 0x102108)), '0103000100000000');
  assert.equal(v.getUint32(0x102110), 0x24050003);
  for (const c of plan.crc32) assert.equal(v.getUint32(c.offset), crc32(output.subarray(c.start, c.start + c.length)));
  assert.equal(hex(output.subarray(0x10, 0x18)), hex(n64Checksum(output)));
  assert.equal(hex(output.subarray(0x102000, 0x1020c0)), receipt.profile_hex);
  assert.deepEqual(source, original);
  const reversed = output.slice();
  for (const row of receipt.writes) reversed.set(fromHex(row.before), row.offset);
  assert.deepEqual(reversed, source);
});

test('all and empty reproduce their exact pins, without changing the supplied array', async () => {
  const { plan, source, stable } = await fixture();
  const all = await composeSelection(source, plan, [C, A]);
  assert.deepEqual(all.output, source); assert.deepEqual(all.receipt.writes, []);
  const none = await composeSelection(stable, plan, []);
  assert.deepEqual(none.output, stable); assert.deepEqual(none.receipt.writes, []);
  assert.equal(none.receipt.runtime_abi, null);
  await assert.rejects(composeSelection(source, plan, []), /checksum mismatch/);
});

test('terminated stock suffixes pack without count fields and preserve native neighbours', async () => {
  const { plan, source } = await fixture(), v = new DataView(source.buffer);
  source.set(fromHex('100010043100310400001008'), 0x103200);
  plan.tables.push({ offset: 0x103204, before: '31003104', width: 2,
    rows: [{ id: A, hex: '3100' }, { id: B, hex: '3104' }], counts: [] });
  source.set(n64Checksum(source), 0x10);
  plan.header.before = hex(source.subarray(0x10, 0x18));
  plan.base_sha256 = await sha256(source);
  for (const [requested, expected] of [[[A], '31000000'], [[B], '31040000'], [[C], '31040000']]) {
    const { output } = await composeSelection(source, plan, requested);
    assert.equal(hex(output.subarray(0x103204, 0x103208)), expected);
    assert.equal(hex(output.subarray(0x103200, 0x103204)), '10001004');
    assert.equal(hex(output.subarray(0x103208, 0x10320c)), '00001008');
  }
  const { output } = await composeSelection(source, plan, [A, C]);
  assert.deepEqual(output, source);
  assert.equal(v.getUint16(0x103208), 0);
});

test('prepared diary rows stay unavailable and are removed even by select all', async () => {
  const { plan, source } = await fixture(), v = new DataView(source.buffer), D = id('item', '2B00');
  v.setUint32(0x102108, 0x08400000); v.setUint32(0x102110, 0x24050005);
  v.setUint32(0x103010, 0x04000000);
  const field = (offset, size) => ({ offset, before: hex(source.subarray(offset, offset + size)) });
  plan.tables[0].before = hex(source.subarray(0x102100, 0x10210c));
  plan.tables[0].rows.push({ id: D, hex: '08400000' });
  plan.tables[0].counts[0].before = '24050005';
  plan.pending_options = [{ id: D, name: 'Diary', kind: 'diary', selectable: false,
    reason: 'Required gameplay is unfinished.', disable: [{ ...field(0x103010, 4), after: 'fc000000' }] }];
  const checksums = data => {
    const dv = new DataView(data.buffer);
    for (const row of plan.crc32) dv.setUint32(row.offset, crc32(data.subarray(row.start, row.start + row.length)));
    data.set(n64Checksum(data), 0x10);
  };
  checksums(source);
  for (const row of plan.crc32) row.before = field(row.offset, 4).before;
  plan.header.before = field(0x10, 8).before; plan.base_sha256 = await sha256(source);
  const expected = source.slice(), ev = new DataView(expected.buffer);
  ev.setUint32(0x102108, 0); ev.setUint32(0x102110, 0x24050004); ev.setUint32(0x103010, 0xfc000000);
  checksums(expected); plan.all_selected_sha256 = await sha256(expected);
  assert.throws(() => resolveSelection(plan, [D]), /Unknown or unimplemented/);
  const { output } = await composeSelection(source, plan, [A, B, C]);
  assert.deepEqual(output, expected);
  const bad = clone(plan); bad.pending_options[0].selectable = true;
  assert.throws(() => validatePlan(bad), /pending import/);
  bad.pending_options[0].selectable = false; bad.pending_options[0].id = A;
  assert.throws(() => validatePlan(bad), /pending import/);
  bad.pending_options[0].id = D; bad.pending_options[0].disable[0].offset = plan.options[0].disable[0].offset;
  assert.throws(() => validatePlan(bad), /Overlapping/);
});

test('missing, duplicate, and cyclic dependencies reject before composition', async () => {
  const { plan } = await fixture();
  for (const dependencies of [[A, A], ['missing'], [C]]) {
    const p = clone(plan); p.options[2].dependencies = dependencies;
    assert.throws(() => validatePlan(p), /dependency/);
  }
  const p = clone(plan); p.options[1].dependencies = [C];
  assert.throws(() => validatePlan(p), /cyclic/);
});

test('overlap, bounds, malformed hex, duplicate profiles, and stale table counts reject', async () => {
  const { plan } = await fixture();
  const mutate = [
    p => { p.options[1].disable[0].offset = p.options[0].disable[0].offset; },
    p => { p.profile.offset = p.base_size; },
    p => { p.options[0].disable[0].before = '000'; },
    p => { p.options[0].disable[0].after = 'ff'; },
    p => { p.options[1].profile_hex = p.options[0].profile_hex; },
    p => { p.tables[0].rows[1].id = 'missing'; },
    p => { p.tables[0].counts[0].base++; },
    p => { p.tables[0].rows.reverse(); },
    p => { p.header.offset = 0x18; },
    p => { p.base_size = NaN; },
    p => { p.web_patcher_enabled = true; },
  ];
  for (const change of mutate) { const p = clone(plan); change(p); assert.throws(() => validatePlan(p)); }
});

test('checksum self-reference and backwards dependencies reject', async () => {
  const { plan } = await fixture();
  const p = clone(plan); p.crc32.reverse();
  assert.throws(() => validatePlan(p), /dependency order/);
  const q = clone(plan); q.crc32[0].start = q.crc32[0].offset;
  assert.throws(() => validatePlan(q), /Self-referential/);
});

test('source and declared-field corruption reject even for a selected untouched record', async () => {
  const { plan, source } = await fixture();
  const damaged = source.slice(); damaged[100] ^= 1;
  await assert.rejects(composeSelection(damaged, plan, [A]), /checksum mismatch/);
  const p = clone(plan); p.options[0].disable[0].before = '00000002';
  await assert.rejects(composeSelection(source, p, [A]), /Changed composition field/);
  assert.equal(await sha256(source), plan.base_sha256);
});

test('caller changes during asynchronous verification do not alter the captured build', async () => {
  const { plan, source } = await fixture();
  const requested = [C], pending = composeSelection(source, plan, requested);
  requested.push(A); source.fill(0); plan.options.length = 0;
  const built = await pending;
  assert.deepEqual(built.receipt.requested, [C]);
  assert.notEqual(built.receipt.output_sha256, await sha256(source));
});

test('surface profiles stay independent and padded catalogue capacity is checked', async () => {
  const { plan, source } = await fixture(), v = new DataView(source.buffer);
  const bits = new Uint8Array(64); bits[9] = 4;
  plan.surface_profile_hex = hex(bits);
  for (const option of plan.options) option.surface_profile_hex = '00'.repeat(64);
  plan.options[0].kind = 'floor'; plan.options[0].surface_profile_hex = hex(bits);
  plan.options[0].profile_hex = '00'.repeat(192);
  source[plan.profile.offset + 32] = 0;
  plan.profile.before = hex(source.subarray(plan.profile.offset, plan.profile.offset + 192));
  const table = plan.tables[0]; table.capacity = 3; table.before += '00000000';
  source.fill(0, table.offset + 8, table.offset + 12);
  for (const row of plan.crc32) {
    v.setUint32(row.offset, crc32(source.subarray(row.start, row.start + row.length)));
    row.before = hex(source.subarray(row.offset, row.offset + 4));
  }
  source.set(n64Checksum(source), 0x10); plan.header.before = hex(source.subarray(0x10, 0x18));
  plan.base_sha256 = await sha256(source);
  plan.save_compatibility = 'Format-4 saves require compatible builds. Keep backups.';
  const { output, receipt } = await composeSelection(source, plan, [A]);
  assert.equal(receipt.surface_profile_hex, hex(bits));
  assert.equal(receipt.profile_hex, '00'.repeat(192));
  assert.equal(receipt.surface_profile_sha256, await sha256(bits));
  assert.equal(receipt.save_compatibility, plan.save_compatibility);
  assert.equal(hex(output.subarray(table.offset, table.offset + 12)), '010200000000000000000000');
  for (const mutate of [
    p => { p.tables[0].capacity = 2; },
    p => { p.tables[0].before = p.tables[0].before.slice(0, -2) + '01'; },
    p => { p.options[0].surface_profile_hex = '00'.repeat(64); },
    p => { p.options[1].surface_profile_hex = p.surface_profile_hex; },
    p => { p.surface_profile_hex = '00'.repeat(64); },
    p => { delete p.surface_profile_hex; },
  ]) { const changed = clone(plan); mutate(changed); assert.throws(() => validatePlan(changed)); }
});
