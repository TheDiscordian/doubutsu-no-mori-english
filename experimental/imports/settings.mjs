import { resolveSelection } from './composer.mjs';

export const SETTINGS_FORMAT = 'AFV3-SHARED-SETTINGS-1';
export const MAX_SETTINGS_BYTES = 256 * 1024;

// These are build choices only: no game bytes, save data, or file names.
export function exportSettings(plan, planHash, requested, behaviours) {
  const selection = resolveSelection(plan, requested, behaviours);
  return {
    format: SETTINGS_FORMAT, donor: plan.donor, scope: plan.scope,
    runtime_abi: plan.runtime_abi, base_sha256: plan.base_sha256,
    plan_sha256: planHash, requested: selection.requested,
    behaviours: Object.fromEntries((plan.behaviours || [])
      .filter(row => !row.pipeline_unavailable).map(row => [row.id, selection.behaviours[row.id]])),
  };
}

export function importSettings(plan, planHash, value) {
  const fail = message => { throw new Error(message); };
  if (!value || typeof value !== 'object' || Array.isArray(value) ||
      ![SETTINGS_FORMAT, 'AFV3-BROWSER-SELECTION-1'].includes(value.format))
    fail('Choose a V3 settings file or a downloaded browser selection profile.');
  if (value.plan_sha256 !== planHash || value.scope !== plan.scope ||
      (value.format === SETTINGS_FORMAT && (value.donor !== plan.donor ||
        value.runtime_abi !== plan.runtime_abi || value.base_sha256 !== plan.base_sha256)))
    fail('These settings belong to a different V3 catalogue or build. Both friends need the same patcher version; no choices have changed.');
  if (!value.behaviours || typeof value.behaviours !== 'object' || Array.isArray(value.behaviours))
    fail('The settings file has no valid behaviour choices.');
  const definitions = new Map((plan.behaviours || []).map(row => [row.id, row]));
  const visible = [...definitions.values()].filter(row => !row.pipeline_unavailable);
  if (visible.some(row => !Object.hasOwn(value.behaviours, row.id)) ||
      Object.entries(value.behaviours).some(([id, setting]) => !definitions.has(id) ||
        (definitions.get(id).pipeline_unavailable && setting !== definitions.get(id).default)))
    fail('The settings file has missing or unavailable behaviour choices. No choices have changed.');
  const behaviours = Object.fromEntries(visible.map(row => [row.id, value.behaviours[row.id]]));
  // Resolve before the UI changes anything. Unknown IDs and invalid values fail
  // rather than silently dropping a friend's imports or replacing a setting.
  const selection = resolveSelection(plan, value.requested, behaviours);
  return { requested: selection.requested, behaviours };
}
