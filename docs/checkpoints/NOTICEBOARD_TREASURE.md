# Complete treasure text, item articles, and native integration work

## Implemented

All eighteen treasure notices have complete C/Python decoding models, including
the native-specific `01F4` town/row clue. Seventeen use the supplied GameCube bodies
unchanged. The adapted two-line heading keeps the six-line structure, blank third
line, remaining wording, and sender decoration without disclosing the item.
Source lengths/CRC32 values and exact native field masks guard every body.

The optional on-demand creator captures full names, numeric N64 coordinates, and
the original town identity, then verifies complete decoding before publishing its
compact output. It uses the existing 164-byte loader destination only as scratch:
the first 96 bytes are the notice, and the final 68 are zero. Native saved records
remain 104 bytes with their RTC field at offset 96. Creator workspace stays 5,344
bytes; no native save or buried-object state is touched by the creator.

`build/noticeboard-treasure/article-creator` and `article-creator-repeat` contain
identical images, relocations, and manifests. The builder requires
`--notice-treasure --item-articles build/noticeboard-treasure/articles/articles.bin`,
the complete quest-reply chain, and `--mail-glyphs`. Fado object ordering follows
the linker's text order; the linked ELF independently agrees with the relocation
inventory.

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| Creator image | 46,592 | `eda487cce42ace3d63bbbc1709377bc7a51471f0232d11c1add8c80b059be980` |
| Relocations | 672 | `2f7a3e1fb6bc95c9c1d63fbe218f5f34581edabfeb291138eb84b71fc9b76212` |
| Creator manifest | 15,687 | `e9bed91641693f46bdf6fde790868756e75c9a6f5ad98754d4aa5b02ec1aa921` |
| Item articles | 8,576 | `639aaeb04f49e5c5e06daaae7c395bd4691fb68f3ec0d3ddd018e0946e04686d` |
| Resident reservation | 32,768 | `493bc25a922bbd9d321759677134520bbb179413985f0e047df45e6e432664c6` |
| Bootstrap | 212 | `9c20b82708856897c19301bb23e35b84335482f9c10d4dd5ba5c3a3f7fb1d10f` |

`build/notice-treasure-runtime` has the current complete source inventory. Its
module, symbols, and bootstrap retain the initial notice build's binary layout.
The new notice unit is explicitly excluded from permanent resident compilation.
The creator entry uses a 112-byte native stack frame, article lookup uses 32,
and decoder parts use 48, apart from called functions. These are compiler reports,
not a measured complete gameplay stack bound.

## Bound native item articles

`tools/item_articles.py` verifies the supplied REL/symbol map, rebuilds the full
approved name resource, and binds each translated name to its exact English
reference field and associated article entry. N64-specific names use explicit
approvals in `translations/n64-item-articles.json`, including `an N cube shirt`,
`some quest money`, and the bare `1,000 Bells` amount. No vowel heuristic is used.

The immutable profile covers all 3,563 translated storage slots. The 981 remaining
untranslated slots have a rejecting marker, not a guessed article. Four identical
furniture rotations share one entry; the table has 1,703 entries. Each stores an
article byte and the CRC32 of the exact sixteen-byte padded name. Its header binds
the whole name resource. See [item articles](../../specs/ITEM_ARTICLES.md).

The creator uses the same original `800BF10C` conversion as the name loader and
checks the complete field CRC before capture. The native request's byte ten is
reserved zero, not a caller-supplied article. Unknown/mismatched names fail without
publication. Clues that do not name the item do not require item-name/article
reads. The installer requires the exact enabled name resource; the embedded-profile
check rejects changed articles even if the manifest recomputes its own image hash.

## Verification

Forty-five host creator/dispatcher tests pass, including all eighteen templates,
both capitals, all five article choices, every villager identity, sixteen-byte
item names, malformed descriptors/identities, overlap guards, every selected
cartridge-read failure, article/name failures, missing resources, and recovery. Earlier NPC, Mom,
departed, event, HRA, postal, museum, shop, and quest-reply dispatch tests run through
the new first dispatcher and pass.

Six article source/runtime/installer tests pass. They cover every 16-bit native
ID, placed conversions, unknown entries, every changed byte of each known directly
addressed name, source/provenance mutations, missing original approvals, and changed
installed-name configuration. The same six tests and all 45 creator tests pass
with AddressSanitizer and UndefinedBehaviorSanitizer. Five artifact tests bind
independent builds, sources, resources, loader entry, unchanged resident code, and
the previous quest-reply creator. Four retained initial-reader evidence tests pass
without replaying native calls. The unchanged decoder retains its five passing
host/sanitizer tests; this article change does not repeat that completed batch.

Current logs are under `build/noticeboard-treasure/`: `article-tests.log`,
`article-creator-tests.log`, `article-sanitizer-tests.log`,
`article-creator-sanitizer-tests.log`, `article-artifact-tests.log`,
`article-initial-reader-retention-tests.log`, and both article-creator build logs.
Retained decoder logs are `decoder-tests.log` and `decoder-sanitizer-tests.log`.
Cross-compiled notice
helpers are in `mips/`; their object SHA-256 is
`fccc10a6bdaad414aed228a0c56e3c2b1721aa188b7cf429b6055a2cb87614f4`.

## Next required integration

The installed ROM remains `build/noticeboard-pilot`; **treasure creation and the
new decoder are not installed**. No treasure text gains application credit yet.

1. Install native owner wrappers using the original selected animal (`s6`),
   template, item, coordinates, and RTC. In the 352-byte treasure scheduler frame,
   the post starts at `sp+68h`, its timestamp at `sp+C8h`, item at `sp+66h`, column
   at `sp+60h`, row at `sp+5Ch`, and selected template at the formatter's fifth
   argument `sp+10h`. The formatter call is `800A62A0`; publication is `800A62A8`.
   The original field preparer `800A5E58..800A5F08` is 176 bytes, called at
   `800A6214`. Verify every caller/side effect before reusing a native region.
2. Implement recovery if creation fails after the original code buries
   an object. Merely skipping the post or timestamp update leaves an unannounced
   object and is not complete handling. Check the actual placement/removal and
   eligibility code before choosing rollback, preflight, or durable pending data.
3. Route the reader to complete treasure decoding while retaining initial-post
   support and the passed native controls/cache behaviour. Keep old installed
   artifact verification usable; changing existing source-bound reader files
   indiscriminately would invalidate the retained initial-reader evidence.
4. Build the complete ROM, verify installed owner/reader/resources and UPS,
   update combined accounting only for verified installation, then run a bounded
   native creator/publication/readback batch. Do not replay completed initial
   storage/reader batches. Normal gameplay, save/reload, and hardware remain.

Continue the forty-one seasonal notices and other remaining text afterwards.
Keep the complete translation, review, patch-only release, title art, and keyboard
stretch goals active; this helper milestone is not project completion.

## Native burial evidence and implementation direction

Native placement is `8008EA5C..8008ECA0`, SHA-256
`3009f5d79b645a51c8c86bac40ac88a41e8e3181a5885b72194db969fea6f766`.
Its frame is 152 bytes. It selects among thirty eligible acres, with foreground
base `8012D148`, 512 bytes per acre. Buried flags start at `801362DC`, 32 bytes
per acre. The call at `8008EC44` passes the foreground pointer, item, column, row,
buried-flag pointer, and eligible-unit count to `800A3E34`.

The deposit function is `800A3E34..800A3F70`, SHA-256
`c98de5761cb2d728ad36c720331480b947db4d6d465ba68b43a598ed1c846373`.
It chooses one eligible empty unit. Ordinary treasure writes the item halfword
at `800A3EE8` and its buried-row halfword at `800A3F14`. Pitfall `2512` instead
calls the native hole-number helper and writes `002A + hole_number` at
`800A3F30`, without changing buried-row flags. With no available hole number,
it writes nothing. Placement still returns success after calling this void
function, so that result alone does not prove burial. The scheduler explicitly
selects pitfalls at `800A6110..800A6134`; this branch is reachable.

A scan of every extracted native file finds only these direct calls:
`800A6214 -> 800A5E58`, `800A6170 -> 8008EA5C`, and
`8008EC44 -> 800A3E34`. This inventory does not exclude computed indirect calls.
The old town helper is also called at `800A6400`; do not reclaim it together with
the treasure-only field helper.

Prefer a before-burial on-demand transaction that snapshots the chosen acre's
512 foreground bytes and 32 flag bytes, invokes the unmodified deposit function,
then reduces the actual change to a small undo record. Retain that record until
complete post creation/publication succeeds. Restore immediately inside the
loaded transaction if deposit changes an unexpected set of fields. This handles
duplicate items elsewhere and pitfalls without guessing which object was placed.
Allocation/read failure before this transaction runs must not call burial. Later
creator failure must use the retained undo record even if allocation fails.

This direction is not installed code. Establish exact lifetime/stack ownership
for undo, preserve RNG order and animal/template selection, and prove cleanup
and eligibility. The 352-byte scheduler frame has formatter scratch at `D0..F7`
available once native formatting is removed; its candidate list starts at `FC`.
A 164-byte staging copy at `68` would corrupt that list. Keep loader staging in
its wrapper's own frame; copy only verified compact output/undo data to the parent.
