# V3 shop mannequin checkpoint

## Build

`build/v3-clothing-mannequin-02/animal-forest-v3-asset-loader.z64`, ABI 38.

- ROM SHA-256: `e6285f389a1e317d2ece4627f961bba173ac113eb411144dc525a53c7f88156e`.
- UPS SHA-256: `cf0a3e8d739179aad8c56d27063cea267cf12c95a11ca1c739e3c7a157234cd9`.
- Resident prefix SHA-256: `9b0758d37e2bc69594376d56b172fd81168d8bd960401494ac5e5fae01fbc0c8`.
- Full V3 resource SHA-256: `cc9c1b1c107646551df2ac56490189b8c49744cbd7a26d04bc6c9ca57da7a03b`.

The [mannequin adapter](../../specs/V3_SHOP_MANNEQUIN.md) widens all six native
count/search windows. The 840-byte helper lives at `80464C00..80464F47`, with
SHA-256 `a29ffda661af3017e09e61b25bf6ef41d56dac9f1b85a9d761738104d72789aa`.
The complete patched actor SHA-256 is
`c8df0d42582534a695129309e1e3f7951c52fe41f376850da73bc27e31e953e9`.
Its allocation, relocation, model, slots, and texture loading remain unchanged.
Save format 2 and the complete preceding selection/ownership layout remain
unchanged. Older format-1 V3 builds and V2 cannot load these format-2 saves.

The first build stopped at the overlap guard before producing a cartridge:
the proposed `A000..A400` reservation contained the existing field bridge at
`A200`. The corrected build uses the verified free `4C00..5000` region instead,
and checks the preceding shuffle array's declared capacity. The original bridge
and every other resource remain intact; no failed build was run in an emulator.

## Verification

The focused current-cartridge test passes in `build/v3-shop-mannequin-tests-01.log`.
It validates all six installed windows and retained delay instructions, restores
the complete original actor for comparison, checks the full compiled helper,
compares every other resource and preceding clothing report, validates repeated
installation/overlap rejection, and reconstructs the ROM from its UPS patch.
Restoring only the helper reservation and ABI restores the complete preceding
V3 resource, including stock, artwork, saved profile, and code.

The initial native setup omitted the existing verified boot-code proof for the
overlay loader. The debugger refused the call before executing it. The corrected
run, `build/v3-shop-mannequin-native-02`, supplies that proof and passes all 56
records, restores its checkpoint, and exits normally.

Native evidence includes actual loading/relocation of the full actor, two full
count calls over a real one-block field with four imports across all unrolled
positions, and five full tile searches. Original clothing, the sold marker,
unknown clothing, and disabled imports retain their expected results. The
native field-existence, bounds, indexing, and grid readers execute; no field
lookup callback is replaced.

Both complete foreground and reload functions transfer all original/imported/
original/naked texture and palette bytes to four guarded buffers. The fixture
models post-constructor slots explicitly; it does not claim constructor
allocation, drawing, or an ordinary shop visit. Actor code, grid contents,
resident code, allocation/stack/save/translation guards, and the zero fault
pointer are checked. Affected globals are restored and the fixture is freed.
There is no physical audio or user-save modification.

## Next implementation

`Shop_Design` has separate clothing checks for placing goods, selecting the
floor item, and reporting a sale. The native disassembly is retained in
`build/v3-clothing-shop-floor-source/code.asm`. The clothing upper-bound branches
are `80953F14`, `809548C8`, and `80954A74`. Lower-bound paths can enter their
delay/continuation instructions, so preserve those incoming paths when patching.
The existing furniture shop-floor adapter occupies 340 bytes of `7C00..7FF0`;
an additional checked clothing adapter may fit the same reservation after it.
The complete current owner must retain its existing furniture edits.

Connect those decisions before ordinary shop acquisition/display verification.
The actual sale path calls `800BFFC0`, records sold-clothing marker `1F35`, invokes
the mannequin clip's naked-model callback, and clears the foreground item.
Catalogue/home garment representations and ordinary buy/sell remain unfinished.
Keep queued NPC completion, outdoor pickup, and the full villager/item lifecycle
on the existing queue. Both patchers remain V2 pending user testing and approval.
