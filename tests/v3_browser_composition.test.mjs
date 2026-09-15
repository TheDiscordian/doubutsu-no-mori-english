import test from 'node:test';
import assert from 'node:assert/strict';
import { sha256 } from '../web/core.mjs';
import { validatePlan, resolveSelection, composeSelection, crc32, n64Checksum } from '../experimental/imports/composer.mjs';

const hex = data => Buffer.from(data).toString('hex');
const id = (kind, number) => `GAFE01-r0/${kind}/${number}`;
const A = id('item', '3100'), B = id('item', '3104'), C = id('villager', '00D8');
const fromHex = s => Buffer.from(s, 'hex');
const clone = structuredClone;

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
