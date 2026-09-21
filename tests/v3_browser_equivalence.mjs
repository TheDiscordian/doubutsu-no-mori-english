/* Current private-cartridge checks called by the Python differential test. */
import { readFileSync } from 'node:fs';
import assert from 'node:assert/strict';
import { composeSelection, resolveSelection, n64Checksum } from '../experimental/imports/composer.mjs';
import { sha256 } from '../web/core.mjs';

const fixture = JSON.parse(readFileSync(process.argv[2]));
const base = new Uint8Array(readFileSync(fixture.base)), stable = new Uint8Array(readFileSync(fixture.stable));
const results = [];
for (const row of fixture.cases) {
  const resolution = resolveSelection(fixture.plan, row.requested);
  for (const key of ['requested', 'enabled', 'required', 'dependency_reasons', 'profile_hex']) {
    assert.deepEqual(resolution[key], row.selection[key], `${row.name}: ${key}`);
  }
  const source = row.requested.length ? base : stable;
  const { output, receipt } = await composeSelection(source, fixture.plan, row.requested);
  assert.equal(receipt.output_sha256, row.sha256, row.name);
  assert.equal(receipt.profile_sha256, row.selection.profile_sha256, row.name);
  if (row.selection.surface_profile_hex !== undefined) {
    assert.equal(resolution.surface_profile_hex, row.selection.surface_profile_hex, row.name);
    assert.equal(receipt.surface_profile_hex, row.selection.surface_profile_hex, row.name);
    assert.equal(receipt.surface_profile_sha256, row.selection.surface_profile_sha256, row.name);
    if (row.requested.length) assert.equal(receipt.save_compatibility, fixture.plan.save_compatibility);
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
