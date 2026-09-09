# Catalogue full-name checkpoint

## Installed

`build/catalogue-names-pilot` retains the complete inventory/editor/default,
notice, letter, font, and message integration and adds the catalogue's full
sixteen-byte item-name display. All nine categories and their seven visible
rows use complete names from the existing English resource. The native page
arrays, IDs, ordering, selection, prices, models, and saved data remain unchanged.

The [specification](../../specs/CATALOGUE_NAMES.md) records source identities,
both item-load callers, the draw caller, and the constructor's unconditional
initialization call. The original seven ten-byte fields exactly fill each
966-byte category page and cannot safely receive wider writes.

A 63-slot private cache associates each original field pointer with a full name.
Initialization resets ownership on every entry. Both native loader sites retain
their original ten-byte writes and populate the complete cache; page changes
update the existing keys. The catalogue name drawer resolves those keys and
passes sixteen bytes with all other arguments and the return value unchanged.
It performs no per-frame name DMA. Failed or missing entries show the complete
English error `Name unavailable`, not stale or silently shortened names.

This supplies another consumer of already installed names, not duplicate text
credit. The eight unresolved accented name fields remain unresolved. Embedded
category labels, wrapped-present text, and confirmation prose are not covered
by this item-name consumer and remain translation work.

## Artifacts and allocation

The overlay/relocation pair moves to VROM `03970000/03980000` at the original
DMA indices. The original 12,576-byte BSS remains at its original addresses,
zero-backed in the new file. Only four words in the original code change.
All 130 original relocations retain their order; the new total is 149, covering
the three additional hook calls and sixteen appended internal references.
Three fixed main-code imports are not relocated with the catalogue.

The appended native code is 532 bytes; its name-loader and draw wrapper each
have a 32-byte frame. Cache reset and lookup have no frame. The cache is 1,260
bytes in the MIPS build. These are measured compiler frames and owned sizes,
not a measured whole-game stack bound or normal-game execution result.

Aligned catalogue growth is 1,856 bytes. Together with inventory growth, the
alternative submenu sum requires 202,240 bytes, below the already installed
243,072-byte dominant pool. Main code, resident memory, saved dimensions, and
the actual four-MiB layout remain unchanged. No Expansion Pak requirement is
introduced and no hardware compatibility result is claimed.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Catalogue image | 53,584 | `7cbd4bbfd5699c28ef7bdded5af5c3125d0a1933192ecf366cab461d7f5ee972` |
| Appended code/data/state | 1,824 | `6a98c7e8b7dd97a76be8112fe9d16f9a374ab9feb5f8d2b3f7718d60d498cc4b` |
| Relocation | 624 | `e828349a5dd1b46b2df4673af1d9d3f0d1938af332c4ab1783cdcc7179831122` |
| Complete ROM | 33,554,432 | `b0061fd4e012a3b56ca15ebcf2e0d32c2da5eb89a1f6c9566820ffaa8897f9fa` |
| UPS patch | 4,607,844 | `30e96ba80d85b4bdeadfaca2e23478692f0bfeb71639d2d34169572de8d44a9c` |

## Reproduction and evidence

With the retained full inventory pilot prerequisites present:

```sh
python3 tools/build_catalogue_overlay.py
bash tools/build_catalogue_pilot.sh
python3 -m unittest discover -s tests -p test_catalogue_names.py -v
```

Independent builds in `build/catalogue-names-overlay` and its `-repro` directory
produce matching image, relocation, and report. The actual helper disassembly
and nineteen ELF relocation entries are inspected and pinned before installation.
The assembly retains original field strides, font geometry, and all unrelated
native words; the fixed external tail calls keep their main-code addresses.

All six focused tests have passing results. Host C executes under address and
undefined-behaviour sanitizers: 63 distinct destinations, every key updated,
complete sixteen-byte draws, no draw-time DMA, failed-load overwrite/recovery,
overflow/null lookup, reset/re-entry, retained original fields and guards, and
all original font arguments/return value. It observes two initializations,
130 compatibility loads, 129 full loads, and 130 draws using mocked imports.
These are host calls, not native emulator calls.

Artifact checks verify three relocation bases, original BSS/prefix retention,
internal and fixed external targets, cache bounds, source/pin rejection, and
allocation. The first allocation assertion used 1,792 instead of the correctly
aligned 1,856 bytes; its focused correction passes without changing production
allocation. Logs are `focused-tests.log` and `allocation-recheck.log`.

Both complete-cartridge checks pass in `cartridge-tests.log`: UPS reconstruction,
shared-owner verification, unchanged main code and all other translation data,
and equal combined accounting rows before/after this additional display path.
The prior inventory/notice/editor native batches are not replayed for this work.

## Remaining work

Include catalogue opening, scrolling, long names, selection/order, and closing
in the combined v0 safety pass, alongside inventory and the owner editor.
Do not infer normal-game or hardware acceptance from host/import mocks or
static relocation checks. Known game failures still block v0 under the
[verification policy](../V0_PLAN.md).

The next embedded-text batch has concrete native sources: wrapped-present text
at tag `8087913C` (five bytes), and nine catalogue category names at
`80879148` (six bytes each). The existing copy/measurement sites at
`808701DC`, `8087029C`, and `808702AC` retain those original widths.
The GameCube references are `present_str$820` and the ninety-byte
`mTG_catalog_str` in the supplied `foresta` symbol table. Native confirmation
phrases also need their complete wording and width consumers; the donor's
`mTG_tag_str_hontoni`/`mTG_tag_str_iidesuka` are placeholders, not translations.
Bind these source records and callers before applying wider English strings.
No font-atlas investigation or image replacement is part of this batch.
