# Complete treasure text helpers and native integration work

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

`build/noticeboard-treasure/creator` and `creator-repeat` contain identical images,
relocations, and manifests. The optional builder flag is `--notice-treasure`, with
the complete quest-reply chain and `--mail-glyphs`. Fado object ordering follows
the linker's text order; the linked ELF independently agrees with the relocation
inventory. The initial failed build log records the ordering mismatch; the final
build succeeds without weakening that comparison.

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| Creator image | 37,792 | `67d7400d4a557bbea2dca29bdcde1cc6e1e06810193c61dcde8b34ba6654033f` |
| Relocations | 656 | `375654f85296ffa6c13feafcbf0ac7d09bcf9e4c7a84f3c9ceefcb71045c3dfd` |
| Creator manifest | 14,717 | `b90a2343687d02c0ef34ce0bbdb4ed223aaf6be934b3573e71b95fd9681596a6` |
| Resident reservation | 32,768 | `493bc25a922bbd9d321759677134520bbb179413985f0e047df45e6e432664c6` |
| Bootstrap | 212 | `9c20b82708856897c19301bb23e35b84335482f9c10d4dd5ba5c3a3f7fb1d10f` |

`build/notice-treasure-runtime` has the current complete source inventory. Its
module, symbols, and bootstrap retain the initial notice build's binary layout.
The new notice unit is explicitly excluded from permanent resident compilation.
The creator entry uses a 112-byte native stack frame; decoder parts use 48 bytes,
apart from their called functions. These are compiler reports, not a measured
complete gameplay stack bound.

## Verification

Forty-four host creator/dispatcher tests pass, including all eighteen templates,
both capitals, all five article choices, every villager identity, sixteen-byte
item names, malformed descriptors/identities, overlap guards, every selected
cartridge-read failure, missing item resources, and recovery. Earlier NPC, Mom,
departed, event, HRA, postal, museum, shop, and quest-reply dispatch tests run through
the new first dispatcher and pass.

Five decoder tests pass, covering all eighteen bodies, exact compact fields,
native-specific clue retention, source-read failures/retry, output/input overlap,
and unchanged output on failure. The same 49 tests pass with AddressSanitizer and
UndefinedBehaviorSanitizer. Four artifact tests verify independent builds, loader
entry selection, unchanged resident code, source inventory, rejected variants,
and continued validation of the previous creator manifest. Four retained native
initial-reader evidence tests also pass without replaying native calls.

Logs are under `build/noticeboard-treasure/`: `creator-tests.log`,
`decoder-tests.log`, both `*-sanitizer-tests.log` files, `artifact-tests.log`,
`initial-reader-retention-tests.log`, and the build logs. Cross-compiled notice
helpers are in `mips/`; their object SHA-256 is
`fccc10a6bdaad414aed228a0c56e3c2b1721aa188b7cf429b6055a2cb87614f4`.

## Next required integration

The installed ROM remains `build/noticeboard-pilot`; **treasure creation and the
new decoder are not installed**. No treasure text gains application credit yet.

1. Bind item articles to the selected native item and its complete English name.
   Supplied `mIN_get_item_article` uses `ftrArt` and the item-category article
   tables, not a vowel heuristic. `ftrArt` has 1,266 bytes and `itemArt_Etc` has
   49 in the supplied REL. Their values use the same `0..4` article enum. Existing
   extended-name provenance supplies reviewed reference IDs. Account explicitly
   for native-specific/remaining names instead of guessing their identity.
2. Install native owner wrappers using the original selected animal (`s6`),
   template, item, coordinates, and RTC. In the 352-byte treasure scheduler frame,
   the post starts at `sp+68h`, its timestamp at `sp+C8h`, item at `sp+66h`, column
   at `sp+60h`, row at `sp+5Ch`, and selected template at the formatter's fifth
   argument `sp+10h`. The formatter call is `800A62A0`; publication is `800A62A8`.
   The original field preparer `800A5E58..800A5F08` is 176 bytes, called at
   `800A6214`. Verify every caller/side effect before reusing a native region.
3. Define and implement recovery if creation fails after the original code buries
   an object. Merely skipping the post or timestamp update leaves an unannounced
   object and is not complete handling. Check the actual placement/removal and
   eligibility code before choosing rollback, preflight, or durable pending data.
4. Route the reader to complete treasure decoding while retaining initial-post
   support and the passed native controls/cache behaviour. Keep old installed
   artifact verification usable; changing existing source-bound reader files
   indiscriminately would invalidate the retained initial-reader evidence.
5. Build the complete ROM, verify installed owner/reader/resources and UPS,
   update combined accounting only for verified installation, then run a bounded
   native creator/publication/readback batch. Do not replay completed initial
   storage/reader batches. Normal gameplay, save/reload, and hardware remain.

Continue the forty-one seasonal notices and other remaining text afterwards.
Keep the complete translation, review, patch-only release, title art, and keyboard
stretch goals active; this helper milestone is not project completion.
