# Initial noticeboard integration

## Installed scope

`build/noticeboard-pilot/animal-forest-halfwidth.z64` installs the four complete
initial announcements, a full-body proportional reader, English entry/date
labels, and bounded extra-page controls. The supplied initial bodies retain
their complete wording and manual breaks; only `C Stick` becomes `C Buttons`.
The immutable English catalogue, existing letters, item names, fonts, and
resident translation module remain unchanged.

The 188-byte initial creator fits within its original 236-byte function. Four
canonical compact records replace the original formatter calls, with unchanged
timestamp placement and eleven unused slots cleared by the native routine.
The original four-ID table stores the four fixed template/checksum words.
Posts remain fifteen 104-byte records, each with 96 message bytes and eight RTC
bytes. Saved storage does not grow.

The reader overlay contains 13,840 bytes, including its original code/data and
zero-backed state. The original 128-byte BSS addresses remain fixed. Appended
code and two full-body caches add 7,056 declared bytes; the loader's aligned
increase is 7,104 bytes. The submenu pool reserves an additional 16,384 bytes:
214,400 native bytes become 230,784. Independent evaluation of the actual
constant/branch instructions agrees with the allocation model. This arithmetic
check is not execution of the allocator or proof of every live submenu lifetime.
The physical memory configuration remains four MiB.

Read controls invoke the original handler first. C buttons, analogue post
selection, A, B, START, and transitions retain priority; L/R select extra text
pages. The two caches preserve both posts during native transition animation,
compare the complete 96-byte source on reuse, and release decoder scratch after
each cache miss. Corrupt/unsupported records and allocation/read failures display
a complete error; reopening permits retry. The native editor body/cursor drawer
is retained. A creates a fresh draft, never editable snapshot bytes.

The original five keyboard palettes and repeated native case/ornament conversion
reach 253 byte values, excluding both reserved prefixes `7F` and `80`. The audit
binds the actual selector, conversion function/table, and English-first editor.
This establishes discrimination for native manual input; it does not migrate
old saved Japanese automatic posts or prove compatibility with arbitrary edits
made by other ROM hacks.

## Verification

Six reader host tests and the same six AddressSanitizer/UndefinedBehaviorSanitizer
tests pass. They cover all four complete bodies, cache reuse/refresh, two-post
transitions, extra pages and control precedence, retained editor forwarding,
malformed records, allocation failure/retry, unchanged saved bytes, entry labels,
and all twelve full month names. These controls/draws use host adapters, not a
native display or controller session. Logs include
`build/noticeboard-reader/sanitizer-tests.log`.

Six compiled/ownership tests and four full-ROM/installer tests have passing
results. Two independent overlay builds agree on image, relocation, initial
creator, and complete manifest. Rehashed mutations cannot change native code,
initial state, appended code, relocations, imports, or constructor addresses.
Failure does not publish partial replacement maps. Complete ROM/UPS checks retain
every unrelated DMA file; changes are confined to the board overlay/relocation,
its submenu owner metadata, the three declared main-code regions, and the DMA
table. The counter credits only the four installed Japanese-source bodies, once.
The retention test records the DMA table as an expected changed file and verifies
its surrounding bytes. Final artifact logs are `install-tests.log` and
`retention-test.log` in the reader directory.

The silent native storage batch `build/smoke-notice-storage-01` passes all 36
calls and 46 full-buffer/guard assertions across 112 records. Actual N64 execution
creates the four canonical records, counts/clears the board, appends through all
fifteen positions, and shifts a full board on the sixteenth append. Mixed manual
posts and both capitalization states retain full 104-byte records, timestamps,
and source buffers. Adjacent-save and stack guards remain intact. The complete
checkpoint restores, FlashRAM/Pak stay blank, and shutdown is graceful. The
300-second-bounded run has no audio, screenshots, user save seeds, or save I/O.
Its frozen result test checks all planned calls and outputs without replaying it.

The separate [native reader batch](NOTICEBOARD_NATIVE_READER.md) executes the
actual submenu program loader, constructor, complete English decoder, draw
wrappers, and L/R controls in an isolated owned submenu fixture. All eight
body/capitalization cases, 33 native draws, 2,210 glyphs, and 8,840 vertex positions
have passing evidence. Cache reuse, corrupt-record recovery, full month labels,
final guards/state/checkpoint restoration, blank saves, and shutdown pass.
Normal submenu initialization, C-button/edit navigation, save/reload, human
presentation review, and hardware testing remain explicit acceptance work.

## Artifacts

- ROM, 32 MiB: `b7ed87865b948c2d34eae2febd85a41bc363c119177ac667d1789a46ecd3e37d`.
- UPS, 4,456,858 bytes: `1ba6a0f5524d9f55dcf7cfb39e37c1b9c6dad21e5db03db13dbaf8beddb58cd4`.
- Reader image: `176691bed9eeeafe53e586fe928d3baa9e9dc43835a08cdede81107393bda145`.
- Reader relocation, 560 bytes: `dabe4c9ad7f3ac3ef7649e513e70958acd66b41597f1fc530c13e1931d96c59c`.
- Initial creator: `59816fc8421e5332a082ed94c7adc09c7c7cc0cc171c9d89b14ecbec6e478940`.
- Native scenario: `54c616411ab15ead83eebfecd0b797824216d8197d187bdef7b15048106db9eb`.
- Native results: `a177ce2031976e8cfae29398a722097c11d726c7b11442bab3a4f84fc5abe7a4`.

## Reproduction and continuation

Build the resident manifest with its complete source inventory. Explicit
on-demand notice units stay outside resident compilation; all their sources
remain hashed. The resulting module and bootstrap match the prior binaries,
including symbols, linked/reserved sizes, and heap bounds.

```sh
python3 tools/build_runtime_module.py \
  --rom 'local/rom/Doubutsu no Mori (Japan).z64' \
  --output build/noticeboard-runtime
python3 tools/build_notice_overlay.py \
  --module build/noticeboard-runtime/module.json
```

Use the complete [native-name build](NATIVE_ITEM_NAMES.md), with resident path
`build/noticeboard-runtime`, extra option
`--english-noticeboard build/noticeboard-reader`, and output
`build/noticeboard-pilot`. Generate the storage batch with
`python3 tools/notice_storage_scenario.py`. It is already passed; do not rerun it
merely to revisit progress.

Continue the 41 seasonal and eighteen treasure bodies with native calendar, venue,
coordinate, and full-field meanings retained. The treasure audit approves seventeen
supplied references and flags `01F4` for native-specific text: the donor reveals
the buried item instead of preserving the native town/row-only clue. The reader
still accepts only the four initial templates. Old saved automatic-post display,
normal draft publication, persistence, reader hint/date placement, other remaining
text and full-name callers, review, patch-only release preparation, title-first
artwork, and GameCube-style keyboard remain. The full project goal stays active.
