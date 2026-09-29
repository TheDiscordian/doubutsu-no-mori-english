/* Current private-cartridge checks called by the Python differential test. */
import { readFileSync } from 'node:fs';
import assert from 'node:assert/strict';
import { composeSelection, resolveSelection, n64Checksum } from '../experimental/imports/composer.mjs';
import { sha256 } from '../web/core.mjs';

const fixture = JSON.parse(readFileSync(process.argv[2]));
const base = new Uint8Array(readFileSync(fixture.base)), stable = new Uint8Array(readFileSync(fixture.stable));
const results = [];
if (fixture.plan.selection_masks) {
  const malformed = structuredClone(fixture.plan);
  malformed.selection_masks[0].members[1].mask = malformed.selection_masks[0].members[0].mask;
  assert.throws(() => resolveSelection(malformed, []), /mask/i);
  const missing = structuredClone(fixture.plan);
  delete missing.selection_masks;
  assert.throws(() => resolveSelection(missing, []), /selection field/i);
  const forged = structuredClone(fixture.plan);
  forged.selection_masks[0].members[0].id = 'GAFE01-r0/item/251E';
  assert.throws(() => resolveSelection(forged, []), /masked selection/i);
}
if (fixture.plan.behaviours?.length) {
  const setting = fixture.plan.behaviours[0].id;
  for (const invalid of [{ unknown: 'N64' }, { [setting]: 'Unknown' }, { [setting]: 1 }, null, []]) {
    assert.throws(() => resolveSelection(fixture.plan, [], invalid), /behaviour/i);
  }
}
for (const row of fixture.cases) {
  const resolution = resolveSelection(fixture.plan, row.requested, row.behaviours);
  for (const key of ['requested', 'enabled', 'required', 'dependency_reasons', 'profile_hex']) {
    assert.deepEqual(resolution[key], row.selection[key], `${row.name}: ${key}`);
  }
  const source = resolution.enabled.length || resolution.behaviours_changed ? base : stable;
  const { output, receipt } = await composeSelection(source, fixture.plan, row.requested, row.behaviours);
  assert.equal(receipt.output_sha256, row.sha256, row.name);
  assert.equal(receipt.profile_sha256, row.selection.profile_sha256, row.name);
  if (row.selection.behaviours !== undefined) {
    assert.deepEqual(receipt.behaviours, row.selection.behaviours, row.name);
    assert.equal(receipt.behaviours_changed, row.selection.behaviours_changed, row.name);
  }
  if (row.selection.surface_profile_hex !== undefined) {
    assert.equal(resolution.surface_profile_hex, row.selection.surface_profile_hex, row.name);
    assert.equal(receipt.surface_profile_hex, row.selection.surface_profile_hex, row.name);
    assert.equal(receipt.surface_profile_sha256, row.selection.surface_profile_sha256, row.name);
    if (row.requested.length) assert.equal(receipt.save_compatibility, fixture.plan.save_compatibility);
  }
  if (row.selection.creature_profile_hex !== undefined) {
    assert.equal(resolution.creature_profile_hex, row.selection.creature_profile_hex, row.name);
    assert.equal(receipt.creature_profile_hex, row.selection.creature_profile_hex, row.name);
    assert.equal(receipt.creature_profile_sha256, row.selection.creature_profile_sha256, row.name);
  }
  if (row.selection.carried_mask !== undefined) {
    assert.equal(resolution.carried_mask, row.selection.carried_mask, row.name);
    assert.equal(receipt.carried_mask, row.selection.carried_mask, row.name);
  }
  assert.equal(Buffer.from(output.subarray(0x10, 0x18)).toString('hex'), Buffer.from(n64Checksum(output)).toString('hex'));
  const restored = output.slice();
  for (const write of receipt.writes) restored.set(Buffer.from(write.before, 'hex'), write.offset);
  assert.equal(await sha256(restored), await sha256(source), `${row.name}: only declared fields changed`);
  results.push({ name: row.name, output_sha256: receipt.output_sha256, enabled: receipt.enabled.length });
}
assert.equal(await sha256(base), fixture.plan.base_sha256);
assert.equal(await sha256(stable), fixture.plan.stable_sha256);
console.log(JSON.stringify({ passed: results }));
