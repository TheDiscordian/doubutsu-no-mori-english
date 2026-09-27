# Console storage preparation checkpoint

The ordinary converter prepares the lossless format-five envelope at
`build/v3-console-games-prepared-04/`. It retains the complete 1,472,384-byte game/
tag packet, twenty launch bindings, eleven pinned donor persistence functions,
and unchanged 3,476-byte recipe executor. No ROM, saved format, native hook,
selector, deployment, or existing save changes.

Command used:

```sh
python3 tools/v3_furniture_pipeline.py convert --representation console \
  --assets-only --output build/v3-console-games-prepared-04
```

Use a fresh directory for another build. The 3,368-byte MIPS envelope has SHA-256
`b6d98f6f6748ae7867482fcbad86c04fe33ed898239ee0e0b16aaed5dd5d3ede`.
It links at zero, has no mutable globals/unresolved symbols, and uses at most
152 stack bytes along its longest call chain. Pack offset is zero; expand is
`8FC`. Caller workspace is 72,064 decode bytes and 16,384 hash bytes; decode
storage can also hold the canonical pack buffer between operations.

## Focused evidence

Two new targeted tests and the refreshed common-core receipt check pass:

- `test_lossless_capacity_malformed_streams_and_atomic_pack`: 446 assertions
  under address/undefined-behaviour sanitizers. Deterministic encoding, complete
  decode, guards, read-only inputs, malformed headers/streams, ordinary and
  compensated checksum damage, alias/size rejection, and unchanged output on
  invalid/oversized input pass. The independent established Python Yaz0 decoder
  also reconstructs each complete successful input.
- `test_mips_preparation_receipt`: compiled/source digests, fixed bank size,
  and explicit uninstalled status.
- Existing `test_prepared_mips_core_matches_current_sources_without_install_claim`:
  current common-executor receipt and complete packet. Unchanged donor recipe
  comparisons from the preceding batch are retained, not replayed.

All successful cases include 6,528 independently randomized console bytes:

| Input | Encoded stream | Spare capacity |
| --- | ---: | ---: |
| Empty payload with valid metadata | 8,141 | 55,709 |
| Existing hardware-test town data | 14,909 | 48,941 |
| Dense synthetic letters/map | 58,699 | 5,151 |

The hardware-test save is read only as compression data, not booted in an old
ROM or retested for gameplay. The stress case fills all 192 letter records with
random printable bytes and every foreground word with a random fourteen-bit
value. It is dense storage, **not a semantically valid town or exhaustive
capacity proof**. An entirely randomized payload rejects before output changes.

The first fixture accidentally repairs the same checksum byte it corrupts,
restoring the valid input. Its one justified retry leaves checksum-only damage
unrepaired while retaining compensated damage elsewhere; it passes. No emulator
harness expansion or historical ROM replay is used.

## Required continuation

Connect native probing, packing, commit, initialization, player clearing, and
startup using the [storage specification](../../specs/V3_CONSOLE_STORAGE.md).
Never copy encoded or partially validated data into the live town. Preserve
both banks and stop before I/O on capacity failure. A candidate RAM layout fits
between carrying state and model storage, but the installer must still prove
and guard actual allocations. The active ABI-275 cartridge is unchanged.
Console launch, graphics allocation, QD, ordinary save/reload, and hardware remain
pending; no optional console is enabled by this preparation.
