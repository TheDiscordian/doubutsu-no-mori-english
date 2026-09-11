# Town-tune and Controller Pak text follow-up

Two additional native menu omissions are corrected beyond RC5. This source
review follows the reported catalogue/repayment findings; these additional
findings are not attributed to a new human playtest.

- V1-24: complete GC `Are you sure?`, `Yes`, and `No` in the town-tune confirmation.
- V1-25: the N64-only Pak manager instruction becomes `Erase a Pak note`.

The [tune specification](../../specs/TUNE_CONFIRMATION.md) and
[Pak specification](../../specs/PAK_ERASE_HEADING.md) record exact native
bindings, storage, pointers/counts, positioning, donor/adaptation provenance,
and retained behaviour. No shared font, geometry, allocation, relocation table,
selection handler, sound, melody, transaction, or save reader/writer changes.

## Focused verification

Four `test_tune_confirmation.py` checks pass in 8.495 seconds. They check all
three complete counted strings, exactly five changed reader words, the retained
asset table, complete relocated pointer/count selection at three addresses,
opening-scale text containment, original BSS, complete cartridge resource
retention, UPS reconstruction, and rejection of altered sources/donors/metrics.

Four `test_pak_erase_heading.py` checks pass in 8.384 seconds. They check the
complete sixteen-byte instruction, only two changed reader words, exact native
centre retention, relocated pointer/count selection, BSS, every other resource,
complete UPS reconstruction, and rejection of changed inputs.

Both test groups pass on their initial execution. These are focused host/ROM
checks, not native rendering or ordinary screen acceptance. No emulator save,
Pak deletion, Pak repair, or user save operation is invoked. Reuse these passing
checks for unchanged code; the historical full suite is not rerun or claimed passed.

The read-only small-owner scan also identifies non-text binary runs in selected
hand/portrait/mailbox/collection data. It is only a lead-finding scan, not a full
embedded-text inventory or proof that other menus have no untranslated text.
The actual tune and Pak font readers are inspected in the retained native
disassemblies `build/tune-confirmation-inspect-01` and `build/pak-heading-inspect-01`.

## Committed construction

The first committed stage is `build/tune-confirmation-01`, from revision
`52d3b0ef3b7a9774bba8c745f90675e50bd38966`:

- ROM SHA-256: `5f85299d975858017f6d822664933bc332908cde17adf7ff0f4b175e941b1f13`.
- UPS SHA-256: `fcf9ce0ef32f5ca3e74b48cd55af9afc95f6041ef84067d1fe0f8ab77b4eace1`.
- Receipt SHA-256: `d6be17dd1d02d41add36c2cb4a2b5e6e651bf9b63375b1fa0956443efd7f1c3f`.

The combined development ROM is
`build/menu-text-followup-01/animal-forest-menu-followup.z64`, constructed from
revision `12859d73f4f0b45fd10f1b36e34c8b44096236ae`:

- ROM SHA-256: `800c7e9d4e6a4b81db05d0a8258d151417d02c9edc47806cf3429e3d144fab09`.
- UPS SHA-256: `51702b426b92097686087fc1bf239fe1ed4e4eb7c91a9bacdbbfb288de33e0bb`.
- Receipt SHA-256: `83da281a2b77dd9a44d946c540ad5369f4ca7af2462d79f3f06eb22731b5131d`.

Both receipts record a clean production worktree. Every other RC5 resource and
all prior corrections are retained through both stages. Original inputs and
earlier builds are preserved. Reproduce into fresh directories:

```sh
python3 tools/tune_confirmation.py --output build/tune-confirmation-new
python3 tools/pak_erase_heading.py --base build/tune-confirmation-new/animal-forest-tune-confirmation.z64 --output build/menu-text-followup-new
```

The [V1RC6 package](V1RC6_PACKAGE.md) includes this exact combined development
build and UPS, with passing package and standalone-patcher checks. RC5 remains
preserved separately. These changes require no save migration; compatibility with RC5 is
expected in both directions, not independently load/save-cycle verified.
Expansion Pak, FlashRAM, and RTC requirements remain unchanged. Preserve
original save backups, and do not use RC3 as a fallback. Ordinary appearance,
broader V1 acceptance, and public-release review remain unfinished.
