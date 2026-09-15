/* Shared bounded metadata reads for the private interface and module worker. */
import { sha256, validateManifest } from '../../web/core.mjs';
import { validatePlan } from './composer.mjs';

export const dataRoot = new URL('../../data/', import.meta.url);
export async function readBounded(url, limit, exact = false) {
  if (!Number.isSafeInteger(limit) || limit < 1 || limit > 64 * 1024 * 1024) throw new Error('Invalid download limit.');
  const response = await fetch(url, { credentials: 'omit', redirect: 'error', cache: 'no-store' });
  if (!response.ok) throw new Error('Experimental import data is unavailable.');
  const reader = response.body.getReader(), result = new Uint8Array(limit);
  let at = 0;
  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      if (value.length > limit - at) throw new Error('Experimental data exceeds its expected size.');
      result.set(value, at); at += value.length;
    }
    if (exact && at !== limit) throw new Error('Experimental data is incomplete.');
  } finally { await reader.cancel().catch(() => {}); reader.releaseLock(); }
  return result.slice(0, at);
}
const json = raw => JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(raw));
async function document(descriptor, name) {
  if (descriptor?.file !== name || !Number.isSafeInteger(descriptor.size) ||
      descriptor.size < 1 || descriptor.size > 4 * 1024 * 1024 ||
      !/^[0-9a-f]{64}$/.test(descriptor.sha256)) throw new Error('Invalid import metadata descriptor.');
  const raw = await readBounded(new URL(name, dataRoot), descriptor.size, true);
  if (await sha256(raw) !== descriptor.sha256) throw new Error(`${name === 'composition.json' ? 'Import plan' : 'Review catalogue'} checksum mismatch.`);
  return json(raw);
}
export async function loadBundle() {
  const bundle = json(await readBounded(new URL('manifest.json', dataRoot), 128 * 1024));
  if (bundle.format !== 'AFV3-BROWSER-BUNDLE-1' || bundle.experimental !== true || bundle.web_patcher_enabled !== false) {
    throw new Error('Unsupported experimental bundle.');
  }
  const plan = await document(bundle.plan, 'composition.json');
  validatePlan(plan);
  for (const kind of ['v2', 'v3']) {
    if (!bundle[kind]) throw new Error('This development export has no reconstruction recipes.');
    const m = validateManifest(bundle[kind]);
    if (m.public_release !== false || m.output_sha256 !== (kind === 'v2' ? plan.stable_sha256 : plan.base_sha256) ||
        m.output_size !== (kind === 'v2' ? plan.stable_size : plan.base_size)) {
      throw new Error('Import plan and reconstruction recipe disagree.');
    }
  }
  if (bundle.v2.source_sha256 !== bundle.v3.source_sha256 || bundle.v2.source_size !== bundle.v3.source_size ||
      JSON.stringify(bundle.v2.resources) !== JSON.stringify(bundle.v3.resources)) throw new Error('The two recipes require different source games.');
  return { bundle, plan };
}
export async function loadReview(bundle, plan) {
  const review = await document(bundle.review, 'review.json');
  if (review.format !== 'AFV3-BROWSER-REVIEW-1' || review.base_sha256 !== plan.base_sha256 ||
      !Array.isArray(review.unavailable) || review.unavailable.length > 4096) throw new Error('Invalid review catalogue.');
  const seen = new Set(plan.options.map(row => row.id));
  for (const row of review.unavailable) {
    if (typeof row.id !== 'string' || !/^GAFE01-r0\/item\/[0-9A-F]{4}$/.test(row.id) || seen.has(row.id) ||
        row.kind !== 'furniture' || row.selectable !== false || typeof row.name !== 'string' ||
        !row.name.length || row.name.length > 128 || typeof row.reason !== 'string' ||
        !row.reason.length || row.reason.length > 2048) throw new Error('Invalid unavailable import record.');
    seen.add(row.id);
  }
  return review;
}
