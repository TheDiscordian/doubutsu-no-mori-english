# Complete summer message and choice installation

## Implemented

ABI 79 appends all 253 GAFE01-r0 summer message records, including separator
records, at native IDs 11754–12006. All 11,754 existing English records remain.
The 49 referenced donor choices have stable appended IDs 462–510; all 462
existing choices remain. The converter remaps 238 message targets and 152 choice
targets without changing wording, line/page breaks, pauses, or expressions.
Twenty-three redundant article-suppression commands are removed only where the
existing checked adapter permits them. The largest expanded bound is 827 bytes,
within the existing 1,024-byte message buffer; no text is truncated.

Eight donor trade-23 requests become native trade 13. The actual donor REL's
23-entry normal trade table points both entries to the same handler `00124ADC`.
Native accepts only 1–22; its verified trade-13 entry is `80920C74`, calling
`8091F458`. This preserves the operation instead of leaving requests silently
ignored or widening an unrelated table. Other actor requests remain unchanged.
Full trade execution and selected summer rewards remain work.

The expanded 2,107,696-byte message resource uses VROM `01FA0000`, after the
complete audio-wave resource and before import storage. The native main-bank
base and both message/choice bounds change together. Message/choice tables retain
`CF9000`/`D06000`; choices retain `025F0000`. All four complete resources use
checked unused physical storage beginning at `03000000`, preserving the original
physical bytes and the same four DMA slots. No resident/heap reservation, saved
format, profile identity, or permanent allocation grows.

## Artifacts

- Full: `build/v3-camper-text-runtime-03/animal-forest-v3-asset-loader.z64`.
- ROM SHA-256: `df8161549e9069ee68c34a4fae3cf3200739a40cb3adecef5e31f6a8aebd24e1`.
- UPS SHA-256: `0fbfa38e2fd4a71f6d9939e0f4e999e4a91ef4019e014ab6d95fa3f4cc526741`.
- Report SHA-256: `778db38b13be2c71056ea2c50f25a1d7f73209a0e205e3f20bb4fad802984e97`.
- Ten-item subset: `build/v3-optional-camper-text-01/animal-forest-v3-asset-loader.z64`.
- Subset SHA-256: `ce7e1cdd063be687e0fffd6ccfd3a70fd0796fa5e80656c392134543fba8dcd3`.

## Verification and defect repair

Seventeen focused/composition tests pass with the final runtime-03 cartridge:
`python3 -m unittest tests.test_v3_camper_text tests.test_v3_optional_composition -v`.
They check every old/new record, all mapped branches/choices, independent donor
text reconstruction with the explicit trade alias, bounds, preserved resources,
physical/virtual storage, header checksums, and all/empty exact full/V2 output.
The offline catalogue retains 59 experimental choices. UPS reconstruction passes.

The initial native run identifies a real cartridge defect: virtual text base
`04000000` loads record zero, but subsequent requests exceed the native DMA
validator's 64-MiB virtual ceiling. The runtime-01 cartridge is not usable.
The repaired allocation is `01FA0000`; the shared validator stays intact.

The corrected silent native run on runtime-02,
`build/v3-camper-text-native-02/results.json`, passes 74 records, 23 calls, and
54 assertions, with no failures. Result SHA-256:
`17f6e856fbe960e302a11920749f2fae5f942df870c84905692a9cb13488638a`.
It checks nine complete actual old/new message loads, five old/new choice reads,
invalid count rejection, actual directory offsets/lengths, and a real summer
continuation through both command dispatch and next-message loading. The longest
new record, existing last message, last new record, saved-town preservation,
memory guards, and fault state pass. The checkpoint is restored before resuming.

Runtime-03 differs from that tested cartridge only in the eight trade-command
value bytes and the ROM header checksum. All executable code, table/resource
addresses, choices, and other message bytes agree. Retain runtime-02's native
loader/continuation evidence for those unchanged paths; the final data adaptation
is covered by the donor/native table checks and focused tests, not a claimed
new ordinary conversation or trade execution test.

## Remaining work and boundary

Connect summer greeting selection, remaining normal conversation setup and
selected camping rewards, lighting/floor sounds, ordinary construction/entry/exit,
acquisition, and persistence. Installed text is not an ordinary conversation
pass or a complete-import playtest handoff. No GPU/hardware acceptance is claimed.
Both served patchers remain V2 until user testing and explicit approval.
GitHub development source is allowed. Imported saves require matching/superset
profiles and must not be loaded in V2; saved format 2 remains unchanged.
