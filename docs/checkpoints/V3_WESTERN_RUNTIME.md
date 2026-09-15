# Western runtime, larger model banks, and optional selections

## Installed development batch

ABI 65 installs tumbleweed, cow skull, saddle fence, western fence, desert cactus,
wagon wheel, and well, retaining complete models, English names/prices, fixed
identities, real acquisition categories, catalogue positions, full scoring, and
selected save dependencies. Saddle fence keeps both opaque parts; well keeps
its double-mirrored materials. The [bank owner](../../specs/V3_FURNITURE_BANKS.md)
reserves 921,632 Expansion Pak bytes for 100 banks of 9,216 bytes, without ordinary
heap or scene-object arena growth. The saddle model is not truncated.

The furniture catalogue has 459 rows alongside all 248 clothing rows. It needs
280,000 of 280,704 reserved bytes; its suffix uses 3,120 of 3,152 code bytes.
Western theme 55 has seven members and its complete English score-letter name.
The 58-record letter-name table has alignment padding only at the end.

Both event items remain in native list 3. Its 64 original entries end at the
terminator at `2E4`, followed by two padding bytes. The initial build rejected
a mistaken 65-entry expectation. The corrected build preserves this check and
appends both rewards before the actual terminator.

The offline composer has 46 experimental choices: twenty villagers, twenty-three
furniture items, and three shirts. Each new item is individually selectable.
Select-all reproduces the full integration ROM; clear-all reproduces exact V2-11.
Both local and public web patchers remain V2. These local artifacts are not a
complete-import playtest handoff. No ROM, patch, or extracted asset is committed.

## Artifacts

Full cartridge: `build/v3-western-runtime-02/animal-forest-v3-asset-loader.z64`.

- ROM SHA-256: `e9285a7d301b466b32eb4af022b5dc7ffaa555b3f1de93cffdb86bc838daa858`.
- UPS SHA-256: `072bb2082c5174dbeecc9f451be60423d361657aeee6a3d5c3a792650fa42e53`.
- Report SHA-256: `e6679d4b4faec83566d87d86ca7f942dd494de42405bca68752285325f4465f9`.
- Blob: 1,843,392 bytes, SHA-256
  `ca76a1c4dabb5e31cbbe6df8fb074e64ff6b9905e0c4adcce34c6c7f186ec819`.
- The 64-MiB ROM still requires an Expansion Pak, RTC, and 128-KiB FlashRAM.

The generated two-event-item subset is `build/v3-optional-western-01/`:

- ROM SHA-256: `0da5cb6a507eea53d804fefd726ad8f4bfbabda56b09afcd816a3bf4fa406f16`.
- UPS SHA-256: `a45dc022cdf39c5e4137af362d9c01e1e237c0d831d6acc6fc43125b6c13ab4e`.
- Report SHA-256: `041c771e03e1bb5b9566a1091a57a60a272c92da95b7313ccf87c4574b25d87e`.
- Only saddle fence and well are enabled; no unrelated dependencies are added.

## Executed verification

Five new installed-runtime checks and nine current-composer checks pass together
in 5.365 seconds. The additional Western-subset test passes in 1.360 seconds.
These fifteen distinct checks cover complete models/profiles, both opaque slots,
moved metadata, stock preservation, catalogue bounds, scoring bits, letter
records/padding, exact permitted ROM changes, relocation removal, CRCs,
all/empty outputs, selected-only HRA entries, fixed IDs, selection order, and the
actual C save codec. The generated subset also passes UPS reconstruction.

The initial native run at `build/v3-western-native-01/` completes its first
108 records (40 memory assertions and 62 native calls) before the bank fixture:

- All seven complete English names, prices, classification, and moved tables.
- Placement cells, plus retained static, animated, and clothing readers.
- Selected/disabled catalogue rules and true event eligibility.
- Actual event selection of well, pocket insertion, and saved ownership bit.
- Western theme count/mask, all 23 acquisition counters, and native points.
- Restoration of modified saved runtime and checked guards.

The bank part establishes 100 actual upper-memory pointers and count0=100,
count1=0, then stops at a mistaken one-byte expectation for a 32-bit counter.
The full run has 127 records, 53 passed memory assertions, 67 native calls, and
one failed expectation. Result SHA-256:
`159f21eef1a3f59b28bdf683cf4561797aa71808e3ddd696c1e9a86bc7d4c93d`.

The one permitted retry, `build/v3-western-native-02/`, reruns only bank work.
It verifies the native-relocated owner, full 100-bank table, heap-free count,
one dummy scene-object slot, and a 1,408-byte arena advance. It then stops at a
second fixture error: the expected source is `013BB000`, while the native signed
address is `013AB000`. Observed DMA SHA-256
`1e24ef09a24ade929598f235319af7bf9bb875078e40269d338580fbd4e5e760`
independently matches the complete actual `013AB000..013AB57F` source. This
classifies the mismatch as a fixture source-address error, not corrupted DMA.
The retry has 24 records, 14 passed memory assertions, five native calls, and
one failed expectation. Result SHA-256:
`f49103af625c3a00157ea400fd146aa9a722e985b649f07a6615141deb4f8fbb`.

The source expectation is corrected, but no third setup attempt is made. The
completed reader/event/scoring prefix is not replayed. Neither failed run is
relabeled a complete pass. Paired upper-memory saddle/well DMA, two-bank
reinitialization, executed bank teardown, and the final checkpoint/guard tail
remain unverified. The reservation is not hardware-certified.

## Compatibility and next work

Saved format 2 is unchanged; selected profile bits change. The actual codec
accepts equal/superset selections and rejects a missing Western dependency
without modifying its inputs or output buffer. Older full profiles lack these
bits and reject these saves. Do not load imported saves in V2. Ordinary
cross-profile save/restart remains unverified; existing saves are preserved.

Continue remaining donor families, faithful mailbox banking/reward delivery,
and ordinary acquisition/placement/persistence. Retain the bank tail for a later
meaningful integration check, not another setup loop in this batch. Further
imports must account for 32 remaining catalogue code bytes, 704 menu-pool bytes,
and bounded resident tables. Browser composition remains offline until user
testing and explicit approval authorise either patcher switch. V3 is not complete.
