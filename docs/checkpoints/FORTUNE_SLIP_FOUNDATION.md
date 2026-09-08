# Fortune-slip foundation work record

This checkpoint implements the complete fortune-slip transaction and independent
catalogue-three support. It does not install the native Miko hand-off. All 68
phrase/outcome values have complete supplied English references; all three
letters retain their full header, body, and signature. The native wave decoration
is an explicit character mapping, not an identical GC-artwork claim. The approved
font and its spacing are unchanged.

## Builds and tests

The full regression batch passes 870 tests in 326.967 seconds:
`build/tests-fortune-slips-final-full.log`. Ten focused tests pass in 14.474
seconds: `build/tests-fortune-slips-focused.log`. The initial regression run
reported two test-maintenance failures: a historical pilot carried a stale
module-bound NPC overlay, and an invalid-ID fixture still called newly assigned
catalogue three unknown. The font probe fixture now constructs a current
unhooked ROM in memory, preserving historical artifacts; unknown-catalogue
fixtures use unassigned ID four. No checks were removed. A source-mutation test
also needed the actor's physical DMA address rather than its VROM address.

The resident module and bootstrap were built independently in
`build/runtime-module-fortune-slips` and `build/runtime-module`; both outputs
match. Resident linked size is 24,288 bytes, leaving 288 within the unchanged
24 KiB limit. Module SHA-256:
`2399b8cad820cf83f8d1d9c36c58633703facba4f12b3835a2637e43487faef6`.
The 212-byte bootstrap remains
`7f7e2328039febb22b6748f1458c85e2c7fca338dd5ffbbafa792daa52eb78b6`.
The module-bound ordinary NPC creator was rebuilt against the new imports.

The complete fortune transaction compiles to 2,244 bytes in
`build/fortune-slip-probe/generate.bin`, SHA-256
`90cfcaa099c4671de18fc0d17df3e51c4b493b9bcee627bb948ac658abf24104`.
It has no mutable/global data, retains all selected fields, and stores a full
slip in 97 bytes of the existing text area. General generation has a 216-byte
stack frame and the fortune creator a 64-byte frame; owned work is 5,280 bytes.

## Native CPU evidence

`build/smoke-fortune-slip-foundation-01` passes forty complete slips, eight
invalid choices, disabled-resource rejection, and four older-catalogue reads.
Its 55 native calls and 525 memory assertions verify full output and metadata,
captured choices, unchanged native RNG/handbill fields/live save, complete code
and source retention, and allocation/stack/module guards. The private allocation
is freed, checkpoint restored, and emulator shut down gracefully. FlashRAM/Pak
files retain their blank hashes. Audio is disabled, with no user save or Expansion
Pak involved. These are owned-memory creator/decoder checks, not a normal
fortune purchase, inventory hand-off, visible letter window, or hardware test.

Evidence hashes:

- Scenario: `c415ad60db2fbe6eb0db74359fd4f186df8a407a6aae457a663bfb52c40fdf1e`.
- Results: `6ee81b34967f075e65b6fbcfd0b998bcb72667857ab6a611fe327f9da8d0b138`.
- Native helper: `7ce92bae025dd9e0f1aa04a4894aecc2b0d925b8c6ef4cb17e98668254e25800`.
- Runner: `0a2dbdf3db1e5071d96ad87b302cfa9a901d1ed1cddf1a9de5c34bcff06cdae1`.

## Current cartridge and remaining work

`build/fortune-slip-foundation-pilot/animal-forest-halfwidth.z64` is 32 MiB,
SHA-256 `7762e4a9bb69db70922c39bcfd5c4e1c8a6715895a2b6edb66b45c18d1165e46`.
Its UPS is 4,030,677 bytes, SHA-256
`975271cab5db8c3ddca03ccfb0e6f162f7f5c22597d0d761004917070e090daf`.
Independent extraction reconstructs every one of the unchanged 13,383 applied
ordinary edits, and applying the UPS to the verified native ROM reproduces the
build. The original native font resource and Miko actor are unchanged.

Compared with the credits pilot, changed DMA files are `00019D40`, `00675720`,
`007908A0`, `00815B70`, `008A6C10`, `02800000`, and `03200000`; these cover DMA,
module imports, reader/creator call sites, and the rebuilt NPC creator.
The only added DMA file is catalogue three at `03050000`. Catalogue two and
every ordinary text-bank payload remain unchanged. No ordinary-bank coverage
increase is claimed for the separate saved-letter resources.

The next native adapter has verified static capacity evidence: Miko uses an
8,192-byte overlay slot, and its 2,376-byte instance can grow to the existing
2,400-byte maximum. The allocator does not enforce the overlay-size bound, so
the new builder must do so. Per-instance pending state can retain choices
without a shared pending global or a long-lived heap allocation. The concrete
state layout, relocation merge, initialization/cancellation lifetime, native
recipient staging, retry semantics, and transaction-before-hand-off still need
implementation and tests. Full actor and region hashes are in the
[specification](../../specs/FORTUNE_SLIP_LETTERS.md).

The unrelated ordinary NPC-creator rejection remains deferred. Full text/review,
normal gameplay/save paths, title-first GC images, GC-style keyboard, hardware
acceptance, and public patch-only release preparation remain in the complete
project scope. The repository stays private; local ROMs, reference text/assets,
generated patches, and save fixtures are not committed.
