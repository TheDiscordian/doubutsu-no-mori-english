# V3 clothing save extension

## Implemented format

The [reward-enabled format-3 variant](V3_REWARD_SAVE.md) retains every clothing
record and profile offset described here. It adds 48 separate reward bytes,
expands runtime state to 912 bytes, and migrates valid format-2 banks. Format 2
below remains the clothing-only variant, not the current reward-enabled output.

Clothing needs independent selected/owned bits, not furniture rotation bits.
The clothing variant uses extension format/registry 2 while retaining the
original `F980`-byte town payload and `680`-byte extension in each 64-KiB bank.
The non-clothing development variants retain format 1. Import-free composition
and both V2 web patchers remain unchanged.

Format 2 preserves the existing villager/furniture profile at extension `018`,
and four furniture catalogues at `0C0`. It uses `2C0..2DF` for the 32-byte
clothing profile and `2E0..35F` for four 32-byte clothing catalogues. The
remaining `360..67F` stays reserved zero. Both existing CRCs cover the new
records. Clothing bits use the stable `34xx` item's low eight bits, LSB first;
the cherry shirt uses bit `BF`, independently of every furniture rotation.

The logical current profile becomes 192 bytes: 32 villager, 128 furniture,
and 32 clothing bytes. Working state adds four 128-byte furniture catalogues,
then four 32-byte clothing catalogues, totalling 832 bytes. The native runtime
header and four guards bring its allocation to 864 bytes at `8046C000..C35F`,
inside the existing explicitly owned Expansion Pak range. The immutable
profile occupies `80460020..00DF`. Native live-save RAM does not grow.

The decoder accepts legacy NAFJ and valid format-1 V3 banks. It preserves
original furniture ownership, installs the current expanded selection profile,
and initializes new clothing ownership to zero. Format-2 banks require every
saved clothing selection and consistent clothing ownership, as well as the
existing checks. Missing selections or invalid format/CRC/data must leave
destinations unchanged. Packing produces format 2 and preserves both native
payload/checksum semantics. Older V3 format-1 builds reject format 2; never
claim backward compatibility with those builds or with V2.

## Code ownership

The existing public codec entries and return bridges remain at their current
addresses. Entry jumps dispatch the clothing variant to its extended codec at
`8046D000`, inside the already owned V3 range and outside mutable save state.
The separate code resource is packed at VROM `03F0F400`, after the actual shirt
and before villager texture data at `03F10000`. Its maximum is `C00` bytes,
including alignment padding. No new DMA directory row is available or added.

A sixteen-byte descriptor at `804600E0` contains checked source, padded length,
CRC-32, and destination. Startup loads and verifies the ordinary `C000` prefix,
then validates this descriptor, loads/checks the separate code, and performs
native cache maintenance before calling any extended save entry. Only then may
save-state initialization and the installed flag complete. The separate code
does not turn ROM-only furniture data into a resident payload or change heaps.

## Verification and remaining integration

The [checkpoint](../docs/checkpoints/V3_CLOTHING_SAVE.md) records the passing
host/cartridge checks and corrected 52-step native run. Evidence includes an
independent complete format-2 encoder, format-1 migration, distinct furniture/
clothing ownership for four players, additions/removals, corruption rejection,
bounds, startup code loading/cache handling, public-entry dispatch, expanded
native save-state initialization, and the native player-clear hook.

The clothing resource profile and normal garment collection are installed;
the catalogue screen and garment menu consumers remain work. Private-buffer encoding/decoding
does not establish ordinary clothing acquisition/save/reload or Controller Pak
transport. Retain unchanged device-worker evidence instead of replaying old
builds. Older format-1 test fixtures require format-aware adaptation before
being used with a clothing-format cartridge; their fixed 160/672-byte buffers
must not be passed to the extended entries.
