import test from 'node:test';
import assert from 'node:assert/strict';
import { gzipSync } from 'node:zlib';
import { GameCubeDisc, normaliseN64, decodeYaz0, applyRecipe, sha256,
  validateManifest, rejectArchive, decompressRecipe, buildRom } from '../web/core.mjs';

const encode = s => new TextEncoder().encode(s);
const donor = encode('Welcome to the neighbourhood!');
function isoImage() {
  const data = new Uint8Array(0x5000), v = new DataView(data.buffer);
  data.set(encode('GAFE01')); v.setUint32(0x1c, 0xc2339f3d);
  v.setUint32(0x424, 0x1000); v.setUint32(0x428, 128);
  v.setUint32(0x1000, 0x01000000); v.setUint32(0x1008, 3);
  v.setUint32(0x100c, 0x01000001); v.setUint32(0x1014, 3);
  v.setUint32(0x1018, 8); v.setUint32(0x101c, 0x3000); v.setUint32(0x1020, donor.length);
  data.set(encode('\0forest\0english.bin\0'), 0x1024); data.set(donor, 0x3000);
  return data;
}
function cisoImage(data) {
  const blocks = [0, 1, 3], out = new Uint8Array(0x8000 + blocks.length * 0x1000);
  out.set(encode('CISO')); new DataView(out.buffer).setUint32(4, 0x1000, true);
  blocks.forEach((index, i) => { out[8 + index] = 1; out.set(data.subarray(index * 0x1000, (index + 1) * 0x1000), 0x8000 + i * 0x1000); });
  return out;
}
function recipe(commands = [[16, 4, 0, 0], [64, donor.length, 1, 0]], literals = encode('TEST')) {
  const out = new Uint8Array(16 + commands.length * 16 + literals.length), v = new DataView(out.buffer);
  out.set(encode('AFWP0001')); v.setUint32(8, commands.length, true); v.setUint32(12, literals.length, true);
  commands.forEach((row, i) => row.forEach((n, j) => v.setUint32(16 + 16 * i + j * 4, n, true)));
  out.set(literals, 16 + commands.length * 16); return out;
}
const source = new Uint8Array(64);
source.set([0x80, 0x37, 0x12, 0x40]);
async function setup() {
  const r = recipe(), compressed = gzipSync(r), output = applyRecipe(source, [donor], r, 96);
  const m = { format: 1, build: 'test', source_size: source.length, source_sha256: await sha256(source),
    output_size: 96, output_sha256: await sha256(output), output_name: 'Animal Forest English V2.z64',
    disc_id: 'GAFE01', disc_revision: 0,
    resources: [{ path: 'forest/english.bin', size: donor.length, sha256: await sha256(donor),
      decode: 'raw', decoded_size: donor.length, decoded_sha256: await sha256(donor) }],
    recipe: { file: 'patch.afwp.gz', size: compressed.length, sha256: await sha256(compressed),
      decoded_size: r.length, decoded_sha256: await sha256(r) } };
  return { m, r, compressed, output };
}

test('all three N64 byte orders normalise without modifying the input', () => {
  for (const order of [[0,1,2,3], [1,0,3,2], [3,2,1,0]]) {
    const swapped = Uint8Array.from(source, (_, i) => source[(i & ~3) + order[i % 4]]);
    const original = swapped.slice();
    assert.deepEqual(normaliseN64(swapped), source); assert.deepEqual(swapped, original);
  }
  assert.throws(() => normaliseN64(new Uint8Array(64)), /recognised/);
});
test('actual donor spans and literals produce the specified output', () => {
  const out = applyRecipe(source, [donor], recipe(), 96);
  assert.deepEqual(out.subarray(0, 16), source.subarray(0, 16));
  assert.equal(new TextDecoder().decode(out.subarray(16,20)), 'TEST');
  assert.deepEqual(out.subarray(64, 64 + donor.length), donor);
});
test('overlaps, bad indexes, out-of-bounds offsets, and unused literals fail', () => {
  for (const commands of [ [[64, 4, 0, 0], [65, 4, 1, 0]], [[64, 2, 2, 0]],
    [[95, 8, 1, 0]], [[64, 8, 1, 0xffffffff]], [[64, 0, 0, 0]], [[64, 4, 0, 1]], [[64, 1, 1, 0]] ]) {
    assert.throws(() => applyRecipe(source, [donor], recipe(commands), 96));
  }
  const bad = recipe(); new DataView(bad.buffer).setUint32(8, 0xffffffff, true);
  assert.throws(() => applyRecipe(source, [donor], bad, 96));
  assert.throws(() => applyRecipe(source, [donor], recipe().subarray(0, 30), 96));
  assert.throws(() => applyRecipe(source, [donor], recipe(), 0xffffffff));
});
test('ISO and sparse CISO resolve the same nested file and empty block', async () => {
  const raw = isoImage();
  for (const [data, name] of [[raw, 'disc.iso'], [cisoImage(raw), 'disc.ciso']]) {
    const disc = await new GameCubeDisc(new File([data], name)).open();
    assert.deepEqual((await disc.files()).get('forest/english.bin'), { offset: 0x3000, size: donor.length });
    assert.deepEqual(await disc.read(0x3000, donor.length), donor);
    assert.deepEqual(await disc.read(0x2000, 12), new Uint8Array(12));
  }
});
test('disc reads are sliced, not whole-file allocations', async () => {
  const raw = isoImage(), slices = [];
  const file = { name: 'disc.iso', size: 1459978240,
    slice: (at, end) => { slices.push(end-at); return new Blob([raw.subarray(at,end)]); },
    arrayBuffer: () => { throw new Error('Whole-disc reads are forbidden'); } };
  const disc = await new GameCubeDisc(file).open(); await disc.files();
  assert.ok(Math.max(...slices) < 0x2000);
});
test('wrong region, CISO map corruption, and FST traversal are rejected', async () => {
  const wrong = isoImage(); wrong[3] = 0x4a;
  await assert.rejects(new GameCubeDisc(new File([wrong], 'wrong.iso')).open(), /different game/);
  const sparse = cisoImage(isoImage()); sparse[8] = 2;
  await assert.rejects(new GameCubeDisc(new File([sparse], 'bad.ciso')).open(), /block map/);
  const fst = isoImage(); fst.set(encode('../bad\0'), 0x1025);
  const disc = await new GameCubeDisc(new File([fst], 'bad.iso')).open();
  await assert.rejects(disc.files(), /Unsafe/);
});
test('Yaz0 overlapping copies work and invalid copies are rejected', () => {
  const raw = new Uint8Array(22); raw.set(encode('Yaz0'));
  new DataView(raw.buffer).setUint32(4, 6); raw.set([0xe0, 65, 66, 67, 0x10, 2], 16);
  assert.deepEqual(decodeYaz0(raw, 6), encode('ABCABC'));
  const bad = raw.slice(); bad[21] = 8;
  assert.throws(() => decodeYaz0(bad, 6), /back-reference/);
  assert.throws(() => decodeYaz0(raw, 0xffffffff), /output size/);
  assert.throws(() => decodeYaz0(raw.subarray(0, 19), 6), /Truncated/);
});
test('gzip is bounded and verifies complete decoded length', async () => {
  const { r, compressed } = await setup();
  assert.deepEqual(await decompressRecipe(compressed, r.length), r);
  await assert.rejects(decompressRecipe(compressed, r.length - 1), /Cannot decode/);
  await assert.rejects(decompressRecipe(compressed.subarray(0,10), r.length), /Cannot decode/);
});
test('archives and unsafe manifests are rejected', async () => {
  for (const name of ['game.7z', 'GAME.ZIP', 'disc.rvz', 'disc.gcz']) assert.throws(() => rejectArchive({ name }));
  const { m } = await setup(); assert.equal(validateManifest(m), m);
  for (const patch of [{ recipe: { ...m.recipe, file: 'https://example.com/upload' } },
    { output_size: 0xffffffff }, { source_sha256: 'bad' },
    { resources: [{ ...m.resources[0], path: '../../bad' }] }]) assert.throws(() => validateManifest({ ...m, ...patch }));
});
test('whole pipeline uses both originals and verifies the final checksum', async () => {
  const { m, compressed, output } = await setup(); const events = [];
  const result = await buildRom(new File([source], 'game.z64'), new File([cisoImage(isoImage())], 'disc.ciso'),
    m, async () => compressed, value => events.push(value));
  assert.deepEqual(result.output, output); assert.equal(events.at(-1), 100);
  assert.equal(result.receipt.output_sha256, m.output_sha256);
});
test('bad donor, bad patch, and bad target checksum never return a ROM', async () => {
  const { m, compressed } = await setup();
  const run = (disc, manifest = m, patch = compressed) => buildRom(new File([source], 'game.z64'),
    new File([disc], 'disc.iso'), manifest, async () => patch);
  const bad = isoImage(); bad[0x3000] ^= 1;
  await assert.rejects(run(bad), /donor checksum/);
  const wrongPatch = Uint8Array.from(compressed); wrongPatch[8] ^= 1;
  await assert.rejects(run(isoImage(), m, wrongPatch), /Patch checksum/);
  await assert.rejects(run(isoImage(), { ...m, output_sha256: '0'.repeat(64) }), /finished ROM failed/);
});
