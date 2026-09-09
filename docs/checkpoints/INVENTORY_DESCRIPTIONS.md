# Inventory letter and delivery description checkpoint

## Installed

`build/tag-descriptions-pilot` contains complete English inventory mail/quest
descriptions, including full eight-byte character names. The supplied GameCube
wording, three-line order, fortune exception, and name-colour roles are retained.
The N64 scale, line interval, animation, actions, and saved structures remain.
The [specification](../../specs/INVENTORY_DESCRIPTIONS.md) records the complete
composition, native interfaces, source bounds, allocation, and counting rules.

Examples are `Letter to / Freckles / from Tom Nook`,
`Delivery for / recipient / from sender`, and
`recipient's / fortune / from Katrina`. Mother uses `home`; the academy uses
`the HRA`. Museum recipient/sender displays translate the typed canonical
identity to `Museum`, including in existing Japanese saves, without changing
that saved identity or the museum's native identity comparisons.

The tag owns two complete display-name fields; the original two six-byte fields
are not widened. The private 300-byte quest-name resolver retains every original
instruction except its five name-loader calls. Existing quest selection,
first-job substitution, completion state, and return behaviour remain native.
Drawing uses cached names and performs no resource DMA.

## Artifacts and allocation

The installed image reuses the replaced Japanese drawer's 952-byte range for
the 928-byte English segment walker, with padding in the remainder. Appended
helpers, quest resolver, text, and zeroed private storage produce a 44,384-byte
tag. Its 2,496 aligned growth bytes plus the owner editor's 5,568 bytes consume
8,064 of the existing 8,192-byte reservation. The catalogue alternative requires
203,840 bytes under the unchanged 243,072-byte pool. No main-code, resident-code,
saved-data, or actual four-MiB memory-layout change is needed.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Tag image | 44,384 | `0462b689b147edced562fec29d8910b89fa47a0d27034db89c01f296d69d9613` |
| Relocation | 3,568 | `d2db49411e8c8ddd4bca5e1633ffcb142c0b97b199a9a6014e1655099e378901` |
| Complete ROM | 33,554,432 | `34fe328e1871532ca03c63f43792c5da1fa238cb76b30b9111c223b8b359cf16` |
| UPS patch | 4,609,762 | `15e2b57b8f4459433b775146504fccfa921ff961931c2026b37f509cc5139066` |

The prior category/present/confirmation profile remains exactly reconstructible,
including every original action label, item-name helper, and width fix.
All earlier message, name, mail, font, creator, catalogue, and editor resources
remain in the complete cartridge. The private repository contains tools and
specifications, not extracted ROM code or generated game assets.

## Reproduction and evidence

With the retained full-menu prerequisites:

```sh
python3 tools/build_tag_descriptions.py
bash tools/build_tag_descriptions_pilot.sh
python3 -m unittest discover -s tests -p test_tag_descriptions.py -v
```

The pinned Docker toolchain builds the native MIPS integration. Independent
`build/tag-descriptions-overlay-repro` image, relocation, and report agree.
`overlay.asm` shows the linked ELF before the guarded binary hook replacements;
`installed.asm` disassembles the actual installed binary, including those hooks.
The compiled segment walker uses a 152-byte stack frame, preparation uses forty,
name adapters use thirty-two, and the draw adapter has no frame. The copied
native quest resolver retains its forty-byte frame. These are function frames,
not a claim that all nested calls use only that amount of stack.

Fifteen focused core/artifact/shared-profile checks pass in
`build/tag-descriptions-overlay/focused-tests.log`. The sanitizer core checks
fifteen complete compositions, eight-byte names, saved player spelling, native
Japanese Museum identities, supported special senders, fallback behaviour,
owner changes, unchanged input/adjacent guards, actual font widths, line order,
segment positions, scale, and line spacing. An additional focused core run in
`colour-check.log` passes exact per-kind colour-role assertions.

Artifact checks bind the complete GameCube references, native quest resolver,
hook arguments and continuation, unchanged prefix and control flow, three
relocation bases, compiled imports, private data, and shared allocation.
Rehashed changes and partial profiles are rejected. These checks include the
prior inventory, category/present/question, and catalogue artifact profiles;
they do not rerun their complete native scenario matrices.

Both full-cartridge tests pass in `cartridge-tests.log`: source/output UPS
reconstruction, shared owner and allocation verification, all unrelated
resources retained, and combined original-ID accounting. Eight original
Japanese records receive English credit once. The counter includes those same
records in the prior build's denominator and preserves every other record and
credit. Native suffix aliases and additional name consumers do not add duplicate
credit. No unsolicited percentage estimate is produced.

## Remaining work

Normal inventory/mailbox/Pak transitions, delivery selection, museum mail, and
fortune display join the combined v0 safety pass. No native emulator scenario is
constructed or replayed for this batch. No ordinary gameplay, saving, original
hardware, or final visual acceptance is claimed by the host/artifact checks.
Confirmed game defects still block v0 under the [verification policy](../V0_PLAN.md).

Continue remaining general strings and letter records, accented names, wider
input/display consumers, contextual review, the combined v0 safety pass, and
patch-only handoff. Title/image replacement and the GameCube-style keyboard
remain v1 work. The paused font-atlas investigation stays paused.
