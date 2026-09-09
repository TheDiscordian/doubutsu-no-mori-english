# Rendering diagnostic translation

The four complete original translations `0005`, `000F`, `0010`, and `0011`
cover note patterns, colour/offset tests, scale tests, and sound/speech samples.
The [specification](../../specs/RENDERING_DIAGNOSTICS.md) preserves every command,
argument, newline, page, intentional scale extreme, and numbered colour span.
The English labels and adapted syllable/speech samples retain the tests' purpose.
All four source hashes and ordered command streams pass; no Japanese remains.
The stored lengths are 330, 389, 835, and 584 bytes, with expanded bounds
346, 405, 851, and 750. No message-buffer or runtime change is needed.

`build/rendering-diagnostics-candidates` retains all 13,763 preceding edits and
adds these four complete records. `bash tools/build_rendering_diagnostics_pilot.sh`
builds the complete ROM using the unchanged design-name resources, creator,
seasonal notice integration, and all previous capabilities. The complete ROM
retains every earlier edit and changes only message data, message offsets, and
the DMA table's physical addresses. The original-ROM UPS reconstruction passes.
The combined accounting test adds only the four installed records and gives no
credit to the pending `0004` draft; its source denominator remains 751,002.
Four source/pending-draft/ROM/accounting tests pass. No source test executes the
diagnostic music/state commands or claims audible presentation.

The native batch `build/smoke-rendering-diagnostics-01` passes all four actual
message-loader calls and fourteen assertions in 29 result records. Every
complete payload/header and adjacent guard matches, stack and checkpoint are
restored, Flash/Pak files remain blank, audio/screenshots stay disabled, and
shutdown is graceful. Its frozen source-bound plan/result test passes without
replaying the completed batch. This proves complete loading, not extreme-scale
drawing, audible presentation, state-changing diagnostic execution, gameplay,
or original hardware.

## Artifacts

| Artifact | SHA-256 |
| --- | --- |
| Complete ROM, 33,554,432 bytes | `ad6e625deb50a681a8d70492ca30d50776e40061c3ceb9b8ac8093fab74f1acb` |
| UPS, 4,493,347 bytes | `e78036e70f03513b57ea4062824e81607aa11b13b30451ad801d5129ddc04251` |
| Candidates | `327deede48346f89df8d89f5a605e7c68940a18a8b4840c16251afae5dab81db` |
| Native scenario | `51715bcddf14953b8fc0fab3423af8bbb8f065566c2ff9a73671023e1506eb19` |
| Native results | `db5f6d82a97cba9232ae9fc698a90e823a71dddb4dba31e95a6b329245a3d774` |
| Restored checkpoint | `d88d10d4b05d0ba3ab52ef420b77c88c81d9146b963839342b297d353e171965` |

Logs use the `build/rendering-diagnostics-` prefix: `final-tests.log`,
`evidence-tests.log`, `native.log`, `build.log`, and `candidates.log`.

## Required continuation

The still-pending `0004` diagnostic contains multiple dynamic fields and embedded
letter text. Its complete English draft is stored in
`translations/pending-diagnostic-sequence.json`, deliberately outside the default
candidate files until sequence integration. All 62 commands match the source,
with no Japanese remaining. It occupies 961 bytes but has an expanded bound of
1,581; the ordinary validator correctly rejects single-record installation.
The encoded draft hash is
`529a97e4cb7429444d483e0a6eacb0e38f7db22818bfa40b5ee2f3446c164eba`.

The existing wait/newline/clear separator at `[416,421)` precedes the current
date/time test. Splitting there gives conservative bounds of 713 and 886 after
adding one native continuation. No text or extra pause must be lost. Preserve
the enabled cancellation state and dynamic fields across that boundary.
The alternate existing separators `[344,349)` and `[459,464)` also fit, but leave
less balanced bounds (581/1,018 and 966/633 respectively).

No continuation slot is approved yet. Candidate reserves `2D32..2D34` have no
native message-script targets or matching arithmetic/logical/comparison
immediates in the pinned code scan. They do have aligned data hits: `2D32`
includes `ovl_Npc_Mamedanuki`, `2D33` includes `ovl_Npc`, and `2D34` has hits only
in `ovl_famicom_emu` (`8083B8D6`) and its relocation data (`8085928A`). Classify
those references or select another proven reserve before authorising a slot.
Do not treat the absence of direct calls as proof about computed callers.

Remaining general strings, letters, accented names, complete name callers,
review, save/gameplay, patch-only release, and image/keyboard work continue.
