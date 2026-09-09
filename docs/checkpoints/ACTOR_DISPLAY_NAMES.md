# Complete festival and reserve character-name preparations

## Installed state

`build/actor-names-pilot` connects the two moon-viewing participant actors and
the fishing participant actor to complete eight-byte names in dialogue slots
one through five. Their selected actors, participant order, skipped entries,
messages, random-number calls, and timing remain native. The reserve actor also
loads the complete `Tom Nook` name for identity `D008` into slot one, preserving
the preceding full-item preparation. A failed name load leaves the field
unchanged instead of copying an uninitialized temporary.

All four preparations fit existing stack frames. Actor sizes, relocation tables,
saved fields, the resident module, persistent text image, font, and actual
four-MiB memory configuration remain unchanged. The [specification](../../specs/ACTOR_DISPLAY_NAMES.md)
records the exact frame boundaries and the reserve sequence's approved use of
one unused item-adapter padding instruction.

```sh
bash tools/build_actor_names_pilot.sh
python3 -m unittest discover -s tests -p test_actor_display_names.py -v
```

The complete builder verifies both actor-name application and the preceding
text-extension adapters together. A missing, modified, or falsely reported layer
does not pass. The counter invokes that installed verification and keeps other
identity-name readers pending. Its ledger and summary now describe the same
build-specific remaining readers; completed shared choices are not listed as
pending in the summary metadata. Source IDs and weights are not duplicated.

## Artifacts

- ROM: 33,554,432 bytes, SHA-256
  `252efc3da4a1b721017b15e116f08f353ee50a6db06ac89353287516fa13b6ad`.
- UPS: 5,094,371 bytes, SHA-256
  `73fb8cf2cd249c54ec6677825f92edbf5cb79175d2da20375c0289deb916aa84`.
- All 13,769 bank edits and every preceding text resource remain installed.
- Only the four approved actor payloads and physical DMA packing change from
  `build/text-choices-pilot`; main code and permanent allocations do not change.

## Bounded checks and limitations

Risk and stopping condition: verify each complete local name fits its original
frame; preserve original slot and actor selection; validate the reserve load-
success branch; bind exact source/import/relocation bytes; and reconstruct the
complete patched cartridge. Shared name-loading/rendering code is unchanged,
so no new all-record native matrix is needed for these call-site changes.

All six focused tests pass in 49.545 seconds. They cover original stack boundaries,
slot expressions, reserve arguments/failure target, independent MIPS assembly,
two-base relocation, failed-guard atomicity, every retained cartridge payload,
UPS reconstruction, both verification layers, and combined accounting. Seventeen
existing display-field/resource-failure/counter regressions also pass. Both
preceding baseline/choice cartridge verification regressions pass in 24.179
seconds, confirming that the added actor layer does not invalidate older builds.

The recorded native check in `build/text-choices-native-01` executes the unchanged
full-name/general-field code on the preceding cartridge and passes twenty calls
and thirty memory assertions. Its module, name resource, text-extension artifact,
main code, and startup ownership remain identical in this actor build; complete
cartridge comparison verifies those dependencies. This is reused evidence for
unchanged helpers, not new execution of the four actor functions. No new emulator
scenario, screenshot, audio output, or user-save change is made for this batch.

Ordinary festival/reserve interaction joins the combined v0 smoke. Normal
progression, save/restart, and original hardware remain unverified. No missing
gameplay evidence is labelled a pass, and no actual crash/save/memory defect is
waived by the bounded test scope.

## Remaining name-reader work

The source-bound `build/audits/identity-name-callers.json` records direct calls
and aligned literal pointers for animal-identity, table-identity, and quest-name
APIs. It is an inventory, not proof that a listed native call still reaches the
player: several letter/quest paths already use complete owned replacements.
The special-name inventory is `build/audits/special-name-callers.json`.

Next, classify the map-name caller `8088E030`, opening guide `809C8318`, fishing
event table-identity caller `80A90270`, and the remaining identity-based main-code
preparations against their installed owners. Complete live readers without
widening saved identity fields or redoing finished letter/quest replacements.
Retain default catchphrase input/display, other item readers, residual text and
letters, accents, v0 safety/handoff, and v1/release requirements in the full queue.
