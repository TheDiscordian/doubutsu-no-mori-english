# Identical native dialogue records

## Candidate contract

The native message bank repeats complete records in several contexts. An
untranslated record may reuse a mechanically validated English candidate only
when its entire Japanese source, including every command argument and line
break, equals the donor's source. Similar wording, matching message numbers,
or matching opcode sequences alone are insufficient.

The candidate pass verifies the donor's source hash, complete GameCube reference
hash, adapted reference content, normal command policy, and expansion bounds.
If multiple eligible donors share that native record, their complete adapted
English output must agree. Different outputs are recorded in
`message-alias-conflicts.jsonl` and withheld for individual review. Agreement on
visible words alone is insufficient; presentation and command bytes must agree.

Original drafts, reviewed multi-record sequences, individually approved identity
and controller records, and explicit overrides are excluded from automatic
transfer. This prevents copying a sequence permission or button-specific
approval onto an unapproved target. Only the existing presentation/reference
policies are eligible, and every accepted target is validated independently.

The result keeps its candidate-not-reviewed status and exact donor reference
provenance. It adds the complete native-equivalent donor list and records the
specific deterministic donor used. It does not establish actor-specific review
or source reachability. The pass is single-stage; new aliases do not become
donors during the same generation.

## Accounting and tests

Every accepted alias must correspond to exactly one previously rejected record.
Remove that record from the remaining report and update the same manifest,
layout-warning, command-policy, and accepted/rejected counters used by ordinary
candidates. Conflicts stay in the remaining report with their original reason
as well as their explicit alias-conflict report.

Portable tests cover complete output retention, changed native records, stale
source/reference/payloads, duplicates, conflicting English, drafts, overrides,
and sequence exclusions. The native scenario generator loads every alias through
`8009E558`, checks its full record header/content and adjacent guards, and
restores its emulator checkpoint. Generated reference-bearing fixtures remain
under ignored `build/`. Actual actor traversal and final text review remain.
