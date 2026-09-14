# V3 imported villager names and default phrases

## Implemented scope

`tools/v3_asset_loader.py --villager-text` includes the pilot artwork, draw,
and audio paths, then installs Cheri/Punchy's shared full-name and catchphrase
readers, six-byte compatibility-name reader, and native catchphrase-reset hook.
Main dialogue name/phrase insertions use those readers. The
[initial-default adapter](V3_VILLAGER_DEFAULTS.md) also connects Cheri's verified
starting outfit/defaults and both pilots' personality lookup. Punchy's outfit,
umbrella identity, houses, roster selection, ID-bounded secondary readers, and
imported save/profile handling remain required before move-ins are enabled.

## Donor binding and metadata

Names come from pinned `forest_2nd.arc`; defaults/personality/growth come from
the pinned donor REL. Full phrases use `forest_1st.arc`'s actual string bank
and offset table. That archive is 852,896 bytes, SHA-256
`461d3d0e0293dac2d93ade9cf317487c92dc15a199da8f698b8f99cba1d812c0`.
Verify edition/revision, archives, REL, symbols, decoder, and native ROM.
Encode complete supported Latin text. The first clothing/umbrella values remain
donor references. A separately verified native clothing mapping occupies the
row's final two bytes; zero means the starting outfit is pending.

Twenty fixed 32-byte rows start at `80462C00`. Registry version 1 determines
the slot: N64 actor minus `E0DA`. Missing imports contain zero rows.

| Row offset | Field |
| --- | --- |
| 0, 2 | Sixteen-bit actor ID and donor clothing ID |
| 4…7 | Personality, umbrella, growth permission, present flag |
| 8…15 | Eight-byte padded English name |
| 16…25 | Ten-byte padded full catchphrase |
| 26…29 | Four-byte saved default reference |
| 30…31 | Verified native clothing ID, or zero if pending |

Only the two ordinary pilots have present rows. Cheri (`E0EA`) has `tralala`;
Punchy (`E0ED`) has `mrmpht`. Present metadata is not move-in eligibility.

## Saved default references

Use `FE F3 ii 20`, where `ii` is the stable N64 identity byte, for imported
defaults. This is a V3 saved-value format, although the saved structure and
four-byte field do not grow. The bytes are ordinary native glyph values, not
partial `7F` commands or `80` two-byte glyphs. Reject collisions with original
default keys. The non-Latin prefix cannot be ordinary custom English text.
Arbitrary pre-existing Japanese custom-text compatibility is not established.

Reset writes only `Animal+4E5..4E8`. The original native four-byte setter/copy
propagates a reference without losing its owner. Full display lookup resolves
that owner, not the speaker, so imported and original villagers can borrow
either pilot's phrase. Custom English remains literal. Imported villagers can
also borrow original defaults. The sole ambiguous native key `D0902020` uses
V2's canonical Dozer phrase for an imported borrower; original owners retain
V2 behaviour.

Saves containing these references require V3 and compatible metadata. Do not
load them in V2. Removing an import can leave references in original villagers'
borrowed phrases even when no imported villager remains. Profile/save handling
must inspect or retain those dependencies; checking roster IDs is insufficient.
Runtime profile rejection/migration and save/reload evidence remain pending.
Preserve user saves and use disposable saves for development.

## Hooks and native fallback

| Existing entry | Replacement responsibility |
| --- | --- |
| `80196044` | Eight-byte display-name lookup |
| `80195D20` | Actor-based full display name |
| `800ACC38` | Six-byte internal/saved compatibility name |
| `80194FDC` | Complete default/borrowed catchphrase lookup |
| `800A9EC8` | Four-byte imported default reset |

Every hook requires exact preceding instructions. Four return bridges at
`80462F00..80462F3F` execute the displaced, non-PC-relative instructions and
jump back to unchanged original code. The actor-name wrapper handles the null
destination itself and enters the original prologue at `80195D28` for fallback.
Initial-default adapters add four bridges at `80462F40..80462F7F`.
No special/player actor becomes an imported villager because its `fgName`
resembles an imported ID.

Full readers retain resource-enabled flags and destination-capacity checks.
Imported lookup requires completed V3 startup, the assigned actor ID, and a
present row. Missing imports/invalid IDs do not write display output. The
six-byte reader preserves native/test identities 0–217 and low-eight-bit argument
conversion; `FF` stays no-write. Both pilot names fit six bytes. Wider future
names need complete display readers and a reviewed saved-name alias policy.

The 216-entry name/catchphrase resources and original house/default resources
remain unchanged. Secondary readers with their own 216-ID guards, including
letter creators, still require V3 integration.

## Memory and verification

ABI 4 uses a 32-KiB blob at `80460000..80467FFF`, inside the established
64-KiB V3 region. Tables/audio retain their addresses. Text code starts at
`80464000`; the end guard is `80467FF0`. Startup verifies the full CRC/header
and writes back all data. ABI-4 code-cache invalidation covers
`80460100..80467FEF`, including return bridges and text code. Earlier variants
retain their cache range. No ordinary heap or saved structure grows.

The [text checkpoint](../docs/checkpoints/V3_VILLAGER_TEXT.md) binds its exact
output, five focused tests, and the combined native reader/insertion/reset pass.
The [defaults checkpoint](../docs/checkpoints/V3_VILLAGER_DEFAULTS.md) records
the current cartridge's six focused tests and native initial-default checks.
These do not establish ordinary gameplay, imported save/reload, or hardware
compatibility. GitHub development continues; the web patcher stays V2 until
the user tests V3 and explicitly approves the switch.
