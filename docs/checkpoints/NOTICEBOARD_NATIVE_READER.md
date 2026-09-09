# Native notice reader evidence and continuation

## Verified scope

The installed `build/noticeboard-pilot` ROM is unchanged from the initial
integration: SHA-256
`b7ed87865b948c2d34eae2febd85a41bc363c119177ac667d1789a46ecd3e37d`.
`tools/notice_reader_scenario.py` binds the full installed image, owner metadata,
relocations, original assets/helpers, and independent complete English bodies.
`tools/notice_reader_smoke.py` calls actual N64 code with an owned submenu state;
no reader instructions or assets are uploaded by the debugger.

The original owner loads the expanded overlay and its board assets from the
cartridge, invokes the real constructor, advances its allocation by the full
aligned size, installs relocated callbacks, and records one owner. Reopening
does not duplicate code or asset allocations. Temporary relocation and decoder
allocations are released. The final native destructor clears ownership.

All four complete initial bodies in both capitalization states have passing
source/cache/layout/draw evidence. Two-post alternation, reopening, malformed
record display, and corrected-record retry pass. Extra pages use actual native
input helpers and the original control handler: right advances, right at the
last page stays put, left returns, and simultaneous L/R does neither. The test
uses the original demo-mode setter to allow ordinary input in its title fixture
and restores the previous flag afterwards.

Across the retained body and final edge results, 33 actual draws verify 2,210
glyphs and 8,840 vertex positions. The draws include every initial body, full
error text, both six-line pages of a manual fixture, hints, entries 1/15, and all
twelve full month names at the native header coordinates. No image capture or
display rendering is used.

The final edge batch passes 40 native calls and 65 memory assertions, including
heap accounting, owner/code/assets, stack/fixture guards, full saved payload and
input/global restoration, checkpoint reload, blank FlashRAM/Pak, and graceful
shutdown. It uses four-MiB emulation, no audio, no user save seeds, and no save I/O.
The source-bound counter continues to credit only the four installed bodies.

## Evidence files and fixture corrections

`build/smoke-notice-reader-01` stops on a single 196,608-byte fixture allocation.
The fixture uses the native owner's 64-KiB asset buffer and separate 80,640-byte
owner and 49,152-byte reader/graphics allocations instead. This corrects an
unnecessary test allocation, not the ROM's heap configuration.

`build/smoke-notice-reader-02` completes the first body/capitalization case, then
stops on a test assumption that an address appears in only one animation cache.
A changed slot can leave its previous bytes in the other cache. Matching both
the address and all 96 saved bytes selects the correct current cache.

`build/smoke-notice-reader-03` skips that completed case and completes the other
seven, alternating posts, reopening, corruption, and retry. It stops when the
title attract-mode flag correctly suppresses input. These are partial runs,
not successful whole-run acceptance; preserve their completed body evidence.

`build/smoke-notice-reader-04` skips all completed body/cache cases, selects
ordinary input with the original setter, and completes only controls, labels,
and cleanup. Its plan is `build/noticeboard-reader/reader-edges-scenario.json`.

| Artifact | SHA-256 |
| --- | --- |
| Reader-02 results | `0944c4332de9155cf30bb13df97c7e71d9238874ebc915d414e4387abcbcf285` |
| Reader-03 results | `36f0d17f36017fbacb6edeb72685a2be6d0a2127cb701b16340d1099ffe27834` |
| Reader-04 results | `0424b85d56bbc0aa928201c06fcf574672e6043b9f405c361c9d22513c554618` |
| Edge-only plan | `beca0a3527c5fc9178f29546d4fc8441a258ebcfab9f477060b193a571df037c` |
| Restored checkpoint | `71ca08c9264340b24a97adc19139168507650be0c017ebfb0ebacb1b4124644b` |

`tests/test_notice_reader_results.py` checks the frozen evidence and reproduces
the final source-bound plan without repeating native calls. The four evidence
tests pass in `build/noticeboard-reader/native-reader-results-tests.log`.

## Continue bulk translation

Do not rerun completed storage or reader batches. Continue automatic-post
creation and full-field capture: seventeen treasure references have source review,
and `01F4` needs native-specific wording to retain its hidden-item clue. The
treasure audit and complete-field samples are in `build/audits/notice-treasure.json`.
The forty-one seasonal posts require native event/calendar matching as well.

Normal top-level submenu allocation/initialization, C-button/analogue selection,
A/B/START behaviour, editor publication, old Japanese automatic posts, real
save/reload, human presentation review, and original hardware remain. The fixture
does not establish normal gameplay, complete save compatibility, or hardware
acceptance. Other untranslated names/general text, title art, the keyboard stretch
goal, review, and patch-only release preparation remain part of the full goal.
