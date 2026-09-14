# V3 clothing save checkpoint

## Implementation

[Format 2](../../specs/V3_CLOTHING_SAVE.md) adds separate clothing selection and
four-player ownership records within the existing two-bank FlashRAM layout.
The clothing variant accepts legacy NAFJ and format-1 V3 input, retaining
furniture ownership and initializing clothing ownership. Missing required
clothing, malformed extensions, and inconsistent ownership are rejected.
New saves are incompatible with older V3 format-1 builds and with V2.

The separate 2,008-byte codec is padded to 2,016 bytes, placed at VROM
`03F0F400`, and loaded to `8046D000` through the checked startup descriptor.
The three existing public entries dispatch to the new codec, preserving the
existing caller addresses and return bridges. The native save runtime keeps
its 1,867-byte size; the collection helper grows to 544 bytes so player clearing
also clears that player's clothing ownership. Startup is 604 bytes.
No original live-save fields, FlashRAM bank sizes, ordinary heaps, or DMA
directory rows grow. Resident runtime state grows from 704 to 864 bytes within
the already owned V3 range, ending at `8046C360`; codec data ends at `8046D7E0`.

## Artifacts

Current build: `build/v3-clothing-save-02/animal-forest-v3-asset-loader.z64`, ABI 31.
The final build adds complete-code installation guards and reports the active
format-2 state explicitly. Its cartridge matches the native-tested build 01;
those build-tool/report changes do not require another emulator execution.

- ROM SHA-256: `dc0de52bab863e601c5ba174d5a70a649baa72ba00828aeff550fc8c967609b3`.
- UPS SHA-256: `0dcec6ae64245e9cafa1ddfffd315f627a8a843b67bd98d03612841a435e3149`.
- Resident prefix SHA-256: `4af257b430ff45518b3edaa9b3abc684005e3a1e025fbc7a0009f1e15989328d`.

The complete blob file ends at `FBE0`, including ROM-only furniture, the shirt,
and the separate codec. The immutable current profile contains 192 bytes;
the original 160 villager/furniture bytes are retained, and shirt bit `BF` is
set in the independent 32-byte clothing profile. Punchy's default outfit and
move-in eligibility remain disabled. Both web patchers remain V2.

## Verification

Five focused clothing-save tests pass, covering the independent complete
encoder, format-1 migration, four separate player catalogues, non-aliasing of
clothing and furniture rotations, additions/removals, CRC/format/catalogue
rejection, disjoint buffers, unchanged data on rejection, installed code/
descriptor/public dispatch, and cartridge/profile checks. The startup check
uses address/undefined-behaviour sanitizers and covers descriptor/source/size/
destination rejection, DMA failure, CRC corruption, cache ordering, and the
retained low-memory path. Four existing non-clothing codec host tests pass on
the current conditional source; no old cartridge is replayed. The current
format-1 codec also explicitly rejects a format-2 bank without writing output.

Initial native attempt `build/v3-clothing-save-native-01` reaches the graph
thread but stops before any fixture/save calls because the dynamically loaded
reference cannot import the test package. The corrected module-search-path
retry `build/v3-clothing-save-native-02` completes all 52 steps and exits normally.
It verifies the complete startup prefix, separately loaded codec, and expanded
runtime initialization. It executes all three public codec entries through
their installed jumps, compares the entire encoded bank with the independent
reference, decodes all ownership, rejects a removed shirt without output writes,
and migrates a valid format-1 bank with furniture ownership intact.

All four player clothing bits can be marked without changing furniture bits;
unselected adjacent shirts do not alias the selected shirt. Furniture rotation
sharing remains correct. The actual native player-clear entry removes only
player three's furniture/clothing catalogue. Runtime state is restored, all
guards pass, both code regions remain intact, and the fault pointer stays zero.
The private allocation is freed and the emulator checkpoint restored. There
are no device writes or ordinary clothing save/reload claims in this check.

## Next work

Connect ordinary clothing item names/classification, menus/icons, wearing
dispatch, acquisition/buy/sell, catalogue orders, and mannequins. Use the new
independent ownership records through the normal collection path. Then verify
combined clothing gameplay and persistence. The separate unresolved NPC queued
completion evidence remains in [its checkpoint](V3_NPC_CLOTHING.md); do not
claim that the save tests resolved it. Controller Pak transport remains pending.
