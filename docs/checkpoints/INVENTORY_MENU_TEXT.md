# Embedded inventory menu text checkpoint

## Installed

`build/inventory-menu-text-pilot` adds thirteen complete English records to the
full catalogue/inventory/editor/letter translation build: nine catalogue
categories, the wrapped-present label, the throw-away question, and the two
confirmation lines. Category names, `Present`, and `Throw it out?` retain exact
supplied GameCube wording and padding. The donor's two placeholder lines are
replaced by the original translation `Are you` / `really sure?` for native
`ホントに` / `いいですか?`.

The [specification](../../specs/INVENTORY_MENU_TEXT.md) records source fields,
pointer/copy/draw sites, geometry, and ownership. Catalogue copies now use
ten-byte rows and actual font widths; present text uses seven bytes. Both fit
the original ten-byte field, with the existing adjacent clearing retained.
The three questions draw from complete immutable strings with explicit lengths.
No saved fields, sender fields, callback identities, item IDs, or category
arrays grow or change meaning.

The throw-away question's 76 unscaled pixels require seven native width cells.
The owned clamp increases a smaller option-based width to seven and leaves
wider widths alone. Its original height write and return path remain. The
two-line confirmation fits the existing six-cell width. Original line count,
spacing, colours, scale, selection order, cancellation, and actions remain.

The base action-label pilot measures the English Yes/Quit options without
accounting for the still-Japanese throw-away question; that can make this
question window too small. This complete profile fixes the width along with
the question text. The older pilot is retained as a reproducible checkpoint,
not treated as the preferred playtest build.

## Artifacts and allocation

The image keeps the complete original 42,800-byte inventory profile, with only
the explicitly bound prefix edits, then appends a 32-byte width clamp and
aligned text. The old action records and compiled helpers stay at their original
positions. The image/relocation still use VROM `03950000/03960000`.
Original pointer HI16/LO16 rows remain; three new jump rows bring the total to
835. Older inventory and catalogue profiles remain verifiable.

The tag grows by 1,088 aligned bytes over retail, 192 more than the base
inventory profile. Tag plus owner editor uses 6,656 of the existing 8,192-byte
reservation. The catalogue/inventory alternative sum is 202,432 bytes under
the same 243,072-byte pool. Main code, resident module, original BSS addresses,
saved data, and the actual four-MiB memory layout remain unchanged.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Inventory image | 42,976 | `a75f80b344586548662f5d2163516ab9adad60c9652fb20bedead6c71fc18759` |
| Relocation | 3,376 | `a1b79c7152ab142a2df04839b55c00a9b46ef12554aa4ecf51a21f0bc2abd22b` |
| Complete ROM | 33,554,432 | `8e7033b789d57b115a90701a09dc571e09f09c5e7bfec111c065c8aacdfe443d` |
| UPS patch | 4,608,026 | `77c890adab11974946fadbf606293a7dc5e36ff0ecedcce10f5b8d4894c57c20` |

## Reproduction and evidence

With the retained full catalogue pilot prerequisites:

```sh
python3 tools/build_inventory_menu_text.py
bash tools/build_inventory_menu_pilot.sh
python3 -m unittest discover -s tests -p test_inventory_menu_text.py -v
```

The pinned Docker assembler independently produces the exact 32-byte clamp.
The independent `build/inventory-menu-text-overlay-repro` image, relocation,
and report agree with `build/inventory-menu-text-overlay`. Its `clamp.asm`
records the actual assembly. No base helper recompilation or font change is
needed for the immutable text and branch extension.

All four new artifact checks and seven earlier inventory/catalogue profile
checks pass in `focused-tests.log`. These cover complete references and text,
unchanged base reconstruction, native destination dimensions, actual font
widths, all new string pointers and jumps at three relocation bases, guarded
base/extended profiles, rejected rehashed changes, and shared allocation.
The small host instruction model executes the actual clamp words for widths
zero through sixteen, verifying only the width field changes, adjacent guards
remain, and control returns to `8086FB88`. This is not N64 CPU execution.

Both complete-cartridge checks pass in `cartridge-tests.log`: current shared
owner/allocations, UPS reconstruction, unchanged main code and every unrelated
resource, and combined original-ID accounting. The counter inventories these
thirteen records in both builds, credits each complete installed translation
once, and retains every other record and credit unchanged. It adds no duplicate
credit for already translated names or action labels.

## Remaining work

Ordinary category changes, present display, throw-away/cancel, and two-line
confirmation join the combined v0 safety pass. No gameplay, saving, hardware,
or final visual acceptance is claimed by these source/artifact/host checks.
Known game defects still block v0 under the [verification policy](../V0_PLAN.md).

Inventory mail/quest labels still use their original six-byte name fields and
Japanese phrase composition; complete letter bodies do not finish this label
consumer. Native mother text is two bytes at `80879144`, copied at `80870000`
with length two at `80870004`. The supplied GameCube tag code instead composes
complete `Delivery for`, `Letter to`, `from`, `to`, and related descriptions;
its `mother_str` is `home`, so do not blindly copy that isolated word into the
native Japanese grammar. Audit the complete sender/quest display path together
with its wider name resources and copy/draw bounds.

Other wider consumers, residual strings/letters, eight accented names, contextual
review, save/gameplay checks, patch-only release work, and v1 title/keyboard
goals remain. Do not restart the paused font-atlas investigation.
