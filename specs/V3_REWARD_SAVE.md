# V3 saved reward state

## Scope and compatibility

`AF_V3_REWARD_PROFILE` requires the clothing profile and enables save format 3
with identity registry 2. It keeps the original `F980`-byte native payload,
`680`-byte extension, 64-KiB bank, selected identities, and every existing
profile/catalogue offset. It adds independent per-player trophy and golden-tool
celebration flags. Catalogue ownership is not evidence that a reward event has
finished, and finishing a celebration does not award a trophy.

Valid NAFJ, format-1, and format-2 banks decode into the current profile with new
flags clear and existing ownership retained. Format-3 banks retain the saved
flags. Matching or larger profiles are required; removing imports is not a
migration. Older format-1/2 V3 builds reject format 3, and imported saves must not
be loaded in V2. Preserve backups before moving a town forward. Ordinary
cross-version gameplay reload is not established by component verification.

Both served V2 patchers and the main import lock remain unchanged. Private
composition/export warnings come from the actual format-3 build report. Empty
selection still yields the exact pinned V2 translation and its save note.

## Layout

Addresses and offsets are hexadecimal unless a size is explicitly in bytes.
Four 12-byte records occupy extension offsets `360..38F`; `390..67F` is reserved
zero. Each player's record contains:

| Offset | Size | Meaning |
| --- | --- | --- |
| `0` | 4 bytes | Big-endian trophy bits 0–27; upper four bits zero |
| `4` | 4 bytes | Big-endian trophy bits 28–32 in bits 0–4; other bits zero |
| `8` | 1 byte | Celebration bits 0–3: axe, net, rod, shovel |
| `9` | 3 bytes | Reserved zero |

Both existing CRCs retain their definitions. Invalid reward bits or reserved
bytes return `AF_SAVE_REWARD_INVALID` (`-9`). Decode validates before changing
output, and pack validates before changing the bank. A failed preparation cannot
continue to device erase/write.

The 192-byte profile and 640-byte catalogue precede the 48-byte reward block in
working state. Total working state is 880 bytes; the runtime header and guards
bring its allocation to 912 bytes at `8046C000..8046C38F`. Reward flags occupy
`8046C350..8046C37F`, and four guard words start at `8046C380`. The owned range
before the codec at `8046D000` is sufficient; neither native save RAM nor a
permanent reservation grows. Old catalogue offsets stay valid. New-town reset
and explicit live-header clearing reset the expanded state.

## Shared installer and ownership

`tools/v3_save_rewards.py` is a shared player-action stage, not an item-specific
installer. It verifies complete source getter/setter/settlement functions,
current codec/runtime bytes, startup descriptor, and old public-entry jumps.
It rebuilds the runtime with the expanded state while requiring the same
1,867-byte extent and every existing symbol address.

The 772-byte reward helper occupies `8046B408..8046B70B`, within the retired
format-1 codec body. The installer restores the three original entry windows in
a temporary copy and binds the full retired 1,608-byte image before reclaiming
that interval. Original internal helpers have no exported consumers. Live
check/pack/collect entries at `8046B400`, `8046B7A0`, and `8046B9C4`, plus original
native bridges at `8046BA60/BA70`, remain intact. The new helper provides:

- `8046B408`: validate all four reward records.
- `8046B4A8`: query/mark one trophy or celebration bit, with bounded arguments.
- `8046B59C`: clear the selected player's reward record, then call the existing
  catalogue/native private-data clearing implementation at `80469B50`.
- `8046B640`: stop the fanfare and mark the active player's celebration bit.

The extended codec is 2,248 bytes at `8046D000..8046D8C7`. Its public targets are
check `8046D000`, pack `8046D55C`, and collect `8046D800`. Shared validation calls
`8046B408`; host-only codec tests compile the same validator inline. The
`8046D8DC` item-reader boundary remains a hard linker limit.

The actual startup descriptor at import offset `E0` selects the complete
12,288-byte resource at VROM `024A1080`, loaded at `8046D000`. It contains the
codec, item readers, and timed tent-lamp code. Do not patch the retired clothing
resource copy instead. Installation binds the active complete resource and its
original 2,976-byte clothing prefix, changes only the first `8DC` bytes, and
retains the full item-reader/lamp suffix. Descriptor and prefix CRCs are updated.
`active_codec_code` records the new map; the original clothing code receipt
continues to describe retained item-reader entries.

## Source semantics and completion

The donor trophy getter/setter support IDs 0–32, split at 28. The donor's
separate `golden_items_collected` field supplies four celebration bits. These
source fields are represented in the explicit extension, never copied into
similarly numbered N64 private-data offsets.

`af_v3_reward_settle` reads the source-mapped celebration type from the actor's
transient `D18` field. It resolves the actual active private pointer at
`80136FD8` against four slots beginning at `80126EC0`, stride `BD0`, validates
state, stops the installed fanfare, and records only that player's celebration.
An unknown active private pointer stops before audio/state effects. Native
private clearing at `800B7ADC` uses the shared wrapper; foreign private pointers
retain the existing fallback behaviour without clearing another player's flags.

The callback is installed but not registered as a complete player action.
Action registration/request routes and source scene/NPC/tree acquisition remain
required. The four golden-tool options stay disabled; this stage adds no choices
or translation text. The single provenance catalogue remains unchanged.

## Verification

The [checkpoint](../docs/checkpoints/V3_FURNITURE_PIPELINE.md#shared-reward-persistence)
records exact build hashes and results. Host checks use an independent full-bank
encoder and sanitizers over codec/runtime/helper calls, including mock device
I/O. Cartridge checks cover complete resources, source bindings, stable entries,
guards, actual hooks, composition, and original-ROM patch reconstruction.

The bounded native fixture executes actual cartridge-loaded code via test-only
jump wrappers, with private buffers and restored live state. It checks migration,
encoding, commit, settlement, and player deletion. It does not perform physical
FlashRAM I/O, ordinary save/restart, complete acquisition, or hardware testing.
Retain unchanged device-worker evidence without relabelling it as a new run.
