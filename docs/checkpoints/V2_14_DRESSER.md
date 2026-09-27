# V2-14 dresser cancellation

The current stable cartridge is `build/v2-dresser-14/Animal Forest English V2.z64`.
B dismisses the filled-dresser prompt. The displayed order is Remove / Swap /
Never mind…, with the matching action comparison changed. Existing museum,
credits, keyboard, and other V2 fixes remain intact.

- ROM SHA-256: `0e81d5c62548c3a759cc89d63eba0975b1c336a3a941211a3000e317b9243bf2`.
- UPS: `build/v2-dresser-14/Animal Forest English V2.ups`.
- UPS SHA-256: `a1c52ab83e17137c254a8423c16f80cb731d3fbef7be3248eac4abfca515195d`.
- Browser export: `build/web-portal-08/site`.
- Browser recipe SHA-256: `24c7b84a089f55a6ecff6ea9e4ff9efcd361f87f9b874ea49d08d785008c6a5f`.

Three focused correction checks and eight combined-cartridge/Pages packaging
checks pass. The silent native run at `build/v2-dresser-14-native-02/` passes
29 assertions: B from all three rows, deliberate A selections, actual relocated
room cancellation, unchanged saved inventory/town bytes, guards, and checkpoint
restoration. See the [implementation contract](../../specs/DRESSER_CANCELLATION.md).

The local patcher at port 8073 serves this export. A silent Chromium download
using the supplied N64 ROM and English GameCube CISO matches the exact V2-14
ROM hash, uses the expected public filename, and reports no browser errors.
Website code and media are unchanged; the generated recipe reconstructs the
complete corrected output before export.

Saved formats are unchanged. Existing V2 saves are expected to remain compatible
in both directions without migration. A new hardware playthrough and save cycle
are not claimed. Experimental V3 imports are not part of this release, and the
released trailer remains unchanged.
