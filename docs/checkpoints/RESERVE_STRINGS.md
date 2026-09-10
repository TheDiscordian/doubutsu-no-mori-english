# Complete native reserve labels

The combined `build/reserve-strings-pilot` installs all 77 source-bound general
reserve labels as `spare`, retaining all prior translation integrations. The
[specification](../../specs/RESERVE_STRINGS.md) identifies every original slot and
its five-byte capacity boundary. The option is explicit and disabled in earlier
recipes. It creates no runtime code, heap allocation, saved field, or selector.

- ROM: 33,554,432 bytes, SHA-256
  `07788752a8137962ff70c442e50f053371f9b6965c98256b7b904357dc87e4c7`.
- UPS: 5,133,090 bytes, SHA-256
  `1ce906c4b4c526db50d7bd99c09e682e75e24377bb8d0f8d7285aa882c7c7709`.

All four focused tests pass: three core checks in 1.559 seconds and the combined
cartridge check in 89.426 seconds. The standalone builder verifies every source,
exact replacement, all 1,562 indices, unchanged unrelated entries, and the
existing guarded string-data relocation. Partial, duplicate, changed, disabled,
wrong-bank/policy/payload, and changed-loader cases reject. The complete cartridge
retains every earlier resource except its general-string data/table and DMA
metadata. The UPS reconstructs the full output from the verified original.

The selected shop-unit capacity-isolation regression, twelve counter tests, and
eight text-classification tests pass. Actual installed reserve verification runs
inside combined measurement. The numerator grows by precisely 154 original
source characters; the denominator remains 751,284. No extra source IDs or
runtime work are counted as new text.

This is a data-only change. Existing native generic-loader and unchanged-runtime
evidence is reused; no additional native harness or emulator run is claimed.
Normal gameplay/save/restart remains in the combined v0 smoke. The next main
implementation is required apology-symbol input, with accents and residual
general/letter text also remaining.
