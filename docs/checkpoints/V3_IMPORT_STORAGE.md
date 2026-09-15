# Import storage expansion and fixed metadata slots

## Completed batch

ABI 67 provides 1,847,280 bytes of free import storage and fixed canonical
metadata slots without adding a file to the full DMA directory. The unchanged
English choice bank keeps its file identity and physical address at VROM
`025F0000`. Its shared native address calculation points to that resource.
The import resource expands to 2,281,488 bytes within its checked reservation.

The 184,336-byte resident package adds 114,704 bytes of permanent RAM. Static
profiles occupy fixed 80-byte slots at `80484000`; item metadata occupies fixed
32-byte slots at `80498000`. Each table has capacity for the supported canonical
ID range, with 25 static and 26 item records installed. Absent slots remain zero.
The normal heaps, dedicated model-bank allocation, and catalogue pool stay fixed.

The 204-byte initializer derives transient profile pointers from valid enabled
rows, retaining native-empty entries, callback-owned speed bag/mannequins, and
three empty end-padding entries. The 1,720-byte furniture helper and 980-byte
item helper use checked direct lookups. Existing public callers retain their
entry addresses through updated forwarding words; the bank owner receives only
the corresponding call-target update. Saved-format code bodies remain unchanged.

The [specification](../../specs/V3_IMPORT_STORAGE.md) records exact memory,
directory, choice-reader, and next-content requirements. Both served web patchers
remain V2; GitHub source publication does not authorise changing either patcher.

## Artifacts

Full integration: `build/v3-import-storage-02/animal-forest-v3-asset-loader.z64`.

- ABI 67; 64-MiB ROM, Expansion Pak, RTC, and 128-KiB FlashRAM.
- ROM SHA-256: `f12da1a8575403ab74ded685e916bf082b5c1d53e6b73c0ae74c0fe87d282ade`.
- UPS SHA-256: `d06810a6b264cb0659571c14d9eb393e22e41553d5bf0e3578a852cef077251a`.
- Build report SHA-256: `a3534ac6e88f07bca7c476ed44914278cfbb063ccadfab8891e3bf2183681dfb`.
- Resident package SHA-256: `a943e867dc549bfb04fa7e75d205132cffed38e19d29154bca177e92774f064e`.

The offline composer retains 49 experimental options and exact all/empty
outputs. Its generated subset selects Cheri, storefront, and red aloha shirt,
adding Cheri's two actual house-barrel dependencies:
`build/v3-optional-storage-01/animal-forest-v3-asset-loader.z64`.

- Subset ROM SHA-256: `fb8e3a93e908b39dee8e325196c72d33d1ec54cfdccb1df254be946eda1ced7d`.
- UPS SHA-256: `2805b0f5b8bf19ee6ee56e10adbfe5c6ea8c8f05aa9f1d7ff93e5db992f60948`.
- Build report SHA-256: `35c57e303602b57cdac39ac583b3d0ff5ed869e39fbbfcc5f846d730a87206d3`.
- Selection receipt SHA-256: `38d187cedbe6fdbdd2def2bdeac76c8a5e09778f18892aea498307d00b89f0d6`.

ROMs, patches, game data, and disposable emulator state remain ignored local
artifacts. No original input or user save is modified.

## Executed verification

Seventeen focused checks pass:

- Four new host/cartridge checks and eleven current-composer checks: 8.828
  seconds. Sanitized C fixtures check first/last/high sparse slots, malformed
  and disabled identities, active-pointer validation, rotations, complete
  initialization, retained callbacks, padding, and guards. Cartridge checks
  verify every installed row, complete package/CRC/forwarders, unchanged codec
  bodies, unchanged choices, directory termination, all unrelated resources,
  physical/virtual bounds, and checksums. Composer checks retain deterministic
  subsets, exact all/empty outputs, catalogue/HRA filtering, and actual codec
  equal/superset/missing-dependency behaviour.
- Two retained shared-C host checks: 0.335 seconds. The unselected compiler
  variants retain initialization, bank helpers, clothing ownership, and native
  catalogue availability. No historical candidate is executed.

Both full builds reconstruct their UPS outputs. The second build changes only
report metadata to make each batch section describe the active package/code;
its ROM and UPS hashes are identical to the first build. The subset also
reconstructs, and its active package hashes agree in all current report sections.

The first native preflight incorrectly assumed the retail 460 choice rows.
It stops before emulation; the current bank has 462 rows including two extended
English choices, and the actual native limit is already 462. Correcting that
fixture enables the first actual native run, with no further retry:
`build/v3-import-storage-native-02/results.json`.

- Result SHA-256: `87ec61ab519a473942d2e603dc7eef64b14c830333b3226081c92dc77ebb7cc0`.
- 84 records, 23 native calls, 48 passed memory assertions, zero failed assertions.
- Cold boot loads and verifies the expanded package. All 25 installed static
  profile pointers, low/high absent boundaries, final unused profile slot, and
  package/table guards pass.
- Existing native callers reach one-cell, two-cell, and callback-item type/price
  readers, retain the cherry-shirt reader, and reject absent boundary IDs.
- Choice index zero, both extended tail IDs, and long odd/even entries return
  the new VROM addresses and full English text through actual native DMA.
  The invalid index returns null/zero; all surrounding text-buffer guards pass.
- The emulator restores its checkpoint, has no CPU fault, and shuts down
  gracefully. Physical audio is disabled. No ordinary game save is performed.

The run executes the first build's ROM; the current second build has the same
ROM hash. No second emulator pass is needed for report-only changes. The previous
bank-lifetime fixture is not repeated. No new rendering, ordinary acquisition,
bank teardown, or cross-build reload result is claimed.

## Compatibility and next work

Format 2 and the selected profile bits are unchanged from ABI 66. The unchanged
codec accepts equal/larger profiles and rejects missing dependencies without
writes; ordinary cross-build reload remains unverified. Imported saves must not
be loaded in V2. Existing builds and saves are preserved.

Continue the camping models and their actual acquisition/scoring integration.
The reviewed static candidates have donor HRA birth category 37; the current
23-counter native adapter cannot accept that raw value. Preserve the Tent route
and implement a safe category adaptation. Other donor families, callback
behaviours, villagers, ordinary gameplay/persistence, browser composition, and
the separate e/e+ investigation remain in the full goal. This storage batch is
not a complete-import playtest handoff or a public release.
