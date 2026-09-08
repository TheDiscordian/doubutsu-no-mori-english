# Complete leaflet date-field work record

The optional date integration prepares complete English months, ordinal days,
years, and AM/PM times for shop-renewal, sale, and Redd leaflets. It changes seven
direct month/day/year calls and two Redd scratch pointers. The original 192-byte
hour function contains 156 bytes of independently compiled original code plus
zero padding. It has no imports, relocations, globals, or stack frame.

The resident module, actor frames/file/BSS sizes, relocation files, saved layouts,
approved font, and ordinary applied text remain unchanged. Source guards cover
the whole actors, fixed hour body, literal/direct interior references, import
targets, and overlapping patches. Renewal and sale reuse locals whose earlier
values are consumed; Redd's month moves below the saved incoming pointer.
See [the implementation contract](../../specs/LEAFLET_DATES.md).

## Executed checks

- Six formatter/installer tests pass in 4.062 seconds: all byte hours at sixteen
  unaligned offsets, invalid full-width inputs/null, complete supplied suffixes,
  two relocation bases, complete code/manifest mutations, and atomic install rejection.
- All 895 regression tests pass in 443.282 seconds. The final four-test caller
  audit also passes in 14.866 seconds; its added same-address-hour test is not
  included in the 895-test count.
- The silent native batch passes 256 hour values plus null rejection, twelve
  renewal date blocks, twelve complete sale preparations, and 33 complete Redd
  preparations. It executes 354 calls and 1,141 memory assertions, plus one
  assertion after restoring the checkpoint.
- Whole loaded actors/relocations, stack/allocation/code guards, live save,
  shared-field restoration, heap accounting, freed allocations, blank isolated
  FlashRAM/Pak, and graceful shutdown pass.

Renewal uses a test-only entry/exit in an owned relocated actor so its actual
date block runs with the original frame/local offsets. It does not execute
mailbox mutation, native schedule branches, creation, or delivery. Sale and Redd
execute complete original preparation functions. Sale checks existing ten-byte
item compatibility fields, not complete wider item capture. These fixtures are
not normal gameplay or original-hardware acceptance.

The first native run stopped on a test expectation for the three-letter month
May: the expected local span omitted its padding. Its complete May handbill
fields had already passed. The expectation was corrected to include the original
padded month span; the same production ROM passes the second complete run. No
checkpoint-restoration claim is made for the failed first run.

## Reproducibility and local artifacts

`build/leaflet-dates` and `build/leaflet-dates-repro` produce identical compiled
hour binaries and manifests. Hour SHA-256:
`eeb382edeeda4fb8ab3f7c070118a40ae224ee647b5a36b17294c924bec3bfaf`.

The 32-MiB ROM is `build/leaflet-dates-pilot/animal-forest-halfwidth.z64`, SHA-256
`6b2c9a01dec248f9a51c4efc8a0ad3f82e90f4302f6647351a5c5c9e244f2055`.
The 4,073,875-byte UPS has SHA-256
`ff0847fdfe0d25993976e1dc7b3b0d12da333c885bf83b67053b7c224663bba6`.
Independent original-ROM UPS application and resident-module verification pass.
Only DMA table `00019D40`, main code `00675720`, renewal actor `0084D180`, and
event actor `00850680` differ from the fortune-recovery pilot. Every other DMA
file, including both catalogues, fonts, resident module, and ordinary text, agrees.
All 13,383 ordinary replacements independently match the current built text banks.
The measurement check initially assumed equal native/built table record counts;
the built message/choice tables have appended entries. Checking every original
edit by its source ID succeeds without counting appended records as new sources.

Evidence:

- `build/tests-leaflet-dates-focused.log`, `build/tests-leaflet-dates-full.log`,
  `build/tests-date-callers-leaflet.log`, and `build/verify-leaflet-dates-install.log`.
- `build/audits/date-callers-leaflet.json`: seventeen resident formatter calls,
  two independently verified English hour calls, and four native notice/fishing calls.
- Scenario `build/leaflet-date-scenario.json`, SHA-256
  `268a084396ec7bc7e5fb3de184fa7481cab2361b46a495433e08cde5a59dd442`.
- Native results `build/smoke-leaflet-dates-02/results.json`, SHA-256
  `5d78298ebe212cc9e27275598133fa55381ac67203f6e0a5ced106ac143da940`.
- Native helper SHA-256
  `9267316e6b0790913c7efbed1e9ad10000e7f91689ed35293dd1d21f8e73597f`;
  runner SHA-256 `8f47f6ba71c0f0a2edc6a6e6499a24770d6d2c3fa0f14508f46ddc73d5700d89`.

## Required continuation

Connect complete leaflet creation and publication at actual native owner
boundaries, capturing complete item/name fields before native truncation and
propagating failures without stale or partial letters. Preserve native template
selection, schedules, RNG, and metadata. Finish combined notice dates and shop
names together, then the remaining fishing units. Native synthetic tests must
remain distinct from normal mailbox delivery, presentation, saves, and hardware.

The full translation/review, stability/save, title-first artwork, GameCube-style
keyboard, and patch-only release requirements remain active. This checkpoint
adds no ordinary translated records and does not complete the project.
