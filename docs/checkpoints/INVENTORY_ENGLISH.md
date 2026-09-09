# Inventory English checkpoint

## Installed

`build/inventory-english-pilot` contains 39 complete English inventory label
records and the ordinary inventory's sixteen-byte item-name load/draw path.
The 44 native menu definitions keep their option order and action callbacks.
Complete labels include `Put on Wall`, `Write Letter`, and `Spread on Floor`;
they are not shortened to the original eight-byte label capacity.

The supplied GameCube executable and symbol table bind each label explicitly.
Native `けす` uses the original translation `Delete` because the reference has
only a placeholder. `Price:` and the `Bells` suffix adapt the native two-row
price layout. Ten halfwidth spaces preserve the five twelve-pixel numeric
positions before the suffix. The unused fourth monetary option stays present
in its pointer array and remains unselectable under the native count.

Ordinary item names use the initialized contiguous ten-plus-six-byte tag span
only in the type-zero item branch. Mail/quest sender fields and their separate
renderer retain their original dimensions. Only the ordinary tag call to the
legacy item-name loader changes; other callers do not gain unsafe wider writes.
The [specification](../../specs/INVENTORY_ENGLISH.md) records the exact boundaries.

The menu and item windows measure installed font advances and round upward to
the native twelve-pixel window units. Internal spaces remain; only trailing
padding is excluded from measurement. Selection, prices, animation, callbacks,
and dialogue timing retain their original logic.

## Artifacts and allocation

The complete tag overlay/relocation moves together to VROM `03950000/03960000`,
at the same DMA indices. Its original 288 BSS bytes retain their addresses and
are zero-backed in the larger file. Native relocation order remains, with new
rows only for internal helper calls and appended action pointers. The fixed
external full-name loader remains at `801969C8` after relocation.

The tag grows by 896 aligned bytes. Together with the owner editor's 5,568-byte
growth, it uses 6,464 of the existing 8,192 reserved bytes. The dominant submenu
pool remains 243,072 bytes. Main code, resident module, memory bounds, saved
structures, and all earlier message/name/letter/font resources are unchanged.
The actual build retains its four-MiB layout; no hardware result is implied.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Tag image | 42,800 | `459ee92f99c222cc1fc30854b4fef32019c8d9797f25f436ae79289efacbbcb6` |
| Tag relocation | 3,360 | `511c047bd3a2390921139e4c3d0373c349717beaf0208553a6b9570b8a9e2e78` |
| Complete ROM | 33,554,432 | `236033f34bb70c076bb54780948ec79238f6230905999f9ed1b42799592e3cd6` |
| UPS patch | 4,564,116 | `415561306a95c4f686633d391c8b8882186c0ef57884ed5994701728e6a6d3ce` |

## Reproduction and focused evidence

With the retained seasonal runtime, complete names, creator, default-message
actor, owner editor, and supplied GameCube inputs present:

```sh
python3 tools/build_inventory_overlay.py
bash tools/build_inventory_pilot.sh
python3 -m unittest discover -s tests -p test_inventory_english.py -v
```

An independent overlay build in `build/inventory-english-overlay-repro` produces
the same image, relocation, and report. The approved helper image has 128 bytes
and no new stack frames; the only compiled external relocation is the fixed
resident item-name tail call. Original native prefix, callbacks, BSS, and source
identities are checked separately from the appended code hash.

The focused tests cover complete label/action identities, unchanged mail/quest
branches, three relocation bases, fixed external calls, actual shared allocation,
rehashed mutation rejection, ROM/UPS reconstruction, retained unrelated resources,
and combined original-ID accounting. The actual width/loader C executes under
AddressSanitizer and UndefinedBehaviorSanitizer with length, padding, corrupt
metric, sixteen-byte destination, and adjacent-byte guards.

The complete cartridge check and 29 affected notice/seasonal/owner-editor
regression tests pass in `build/inventory-english-overlay/cartridge-regressions.log`.
The five core/artifact checks pass in `focused-tests.log`; the complete cartridge
is checked separately after building, rather than accepting that initial skip.
The new actual-cartridge accounting test and seven counter regressions pass in
`accounting-test.log`. Together these runs pass all seven inventory checks and
the 36 affected shared-menu/accounting regressions; no native run is implied.

The combined counter inventories all 39 original label records in both old and
new builds, credits actual verified English labels once, and leaves numeric-only
source weight at zero. Other text records must remain identical between these
builds. The expanded owner editor is verified at its actual DMA location rather
than assuming the earlier keyboard file remains at its original address.

## Next work and limits

No native scenario or gameplay execution is claimed for this patch. Include
ordinary inventory open/selection, long item names, mail/quest transitions, and
price placement in the combined v0 safety pass. Reuse the existing scenarios;
do not build an exhaustive all-item/all-menu test matrix before continuing
remaining translation and consumer integration.

The [catalogue consumer](CATALOGUE_NAMES.md) supplies the complete cached names;
other full-name consumers, residual text/accents, normal saving,
contextual review, hardware, release preparation, and title/keyboard stretch
goals remain. Follow the [v0 plan](../V0_PLAN.md): testing-setup limits never waive
actual crashes, save damage, memory corruption, or unexplained possible game
failures.
