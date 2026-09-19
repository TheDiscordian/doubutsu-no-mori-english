# Museum letter headers

## Display and identity

Mail recipient type two is the faraway museum. Its canonical six-byte N64
identity is `19 07 F8 11 05 C3`; do not rewrite it. Display `Museum` in the
recipient picker, editable header, opening/closing animations, ordinary reader,
and generated snapshot header. Recipient type is independent of sender type:
an incoming museum reply still addresses the player. Player names, unsupported
identities, villager-name lookup, custom salutations, signoffs, body text, and
native header-only mail types retain their existing behaviour.

The English name comes from the supplied GameCube game's `l_museum_name_str`,
`foresta.rel .data+0000CD80`, containing `Museum` and two padding spaces. The
single credit is `ui/mail/museum-name` in `translations/provenance.json`.

## V2 installation

`tools/v2_museum_header_fix.py` consumes exact V2-11 and creates a separate V2-12
cartridge and UPS. It never overwrites the source cartridge, saves, or patchers.
The `AF_MUSEUM_HEADER` compiler option selects the corrected C implementation;
baseline builders retain their checked layouts when the option is absent.

The board installer appends the corrected header code to the complete current
letter overlay, retaining every prior UI/default/editor fix. Only the existing
header entry's jump changes in the old prefix. Its internal relocation remains
present. The owner row receives the exact larger bounds. The 1,536-byte rounded
growth fits the 2,560 unused bytes of the existing letter-UI reservation; the
shared pool and resident reservation do not grow. Existing cursor code stays
installed, preserving editing geometry.

The resident reader's public addresses must not move. An 84-byte adapter at
`80194970` uses checked zero padding between the module descriptor's end at
offset `88` and the watchdog at offset `100`. The entry at `801984D0` jumps to
the adapter. Type two writes exactly six English bytes and returns six, including
for unaligned destinations. Other identities execute the two displaced
instructions and resume at `801984D8`. The ordinary and snapshot readers share
that entry. Bootstrap, descriptor fields, BSS, watchdog, and other runtime
functions remain unchanged. The matching C case provides the host-test model;
rebuilding the whole resident module is not part of this incremental installer.

## Verification and compatibility

Host checks cover all editing/animation states, ordinary and generated headers,
all 216 villager indices, player/unknown fallbacks, incoming museum replies,
colours, geometry, and immutable source state. Cartridge checks bind input/output
hashes, actual relocations, allocation bounds, unchanged delivery code, unrelated
resources, and UPS reconstruction. The focused native fixture uses only code
loaded from the new cartridge and isolated data, with silent audio.

Save formats and delivery processing do not change. Compatibility with V2-11 is
expected in both directions without migration; existing museum-addressed letters
use the corrected display. This does not establish a new ordinary save/reload
or original-hardware test. Actual evidence and remaining visual verification are
recorded in `docs/checkpoints/MUSEUM_LETTER_HEADERS.md`.

V3's locked development ROM and exact no-import V2 reference remain unchanged.
Carry this correction into V3 through its checked installer/composition process;
do not silently replace a locked base or either served patcher.
