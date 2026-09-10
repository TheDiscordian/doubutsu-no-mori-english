# English mailbox and repayment labels

The mailbox heading uses the complete supplied Mail image. The repayment screen
uses Cash:, Payment:, You still owe, and Bells. Existing texture storage holds
the complete images and the unchanged relocated border tile; native code,
numeric fields, allocations, and saved formats remain unchanged. See
[the service artwork specification](../../specs/SERVICE_ARTWORK.md).

Three focused checks pass in 8.242 seconds: complete source pixels and geometry,
non-overlapping texture repacking with intact border pixels, independent MIPS
commands/source rejection, and full prior cartridge retention with UPS recovery
and corrected keyboard ownership. One title combination check passes in 7.845
seconds, retaining the complete catalogue/notice/tune and earlier artwork.
Unchanged title, conversation, and keyboard code reuse their recorded native
evidence. Ordinary screen appearance/navigation is not claimed from host checks.

Untitled candidate: `build/service-artwork-01/animal-forest-halfwidth.z64`.
ROM SHA-256:
`23f9d9724827d0de3c91bd00a91349b04b0d45371d1930ef71cdbb95910e711e`.
UPS SHA-256:
`39f651687baf0b2b9c41fa335af07a66c22131cc3f350c29f61ca7120e2f1289`.

Combined candidate: `build/title-service-combined-01/animal-forest-title-preview.z64`.
ROM SHA-256:
`5353187111c528ecb88e2efa5606e23dfd3a05adc10bb4d1ae16691c31132258`.
UPS SHA-256:
`6fd37fa2138f965e83a930bc615f79a4383ae75510987844a16da99ed0cb6ecc`.
The 32-MiB combined cartridge requires an Expansion Pak. The ordinary four-MiB
heap, saved formats, both Nook conversation corrections, Shrine wording, all
English text, and corrected grid remain. Earlier playtest ROMs are untouched.
Normal save/restart, changed screens/buildings, and hardware acceptance remain
playtest work; this is not a completed public v1 release.

## Next work

The birthday window has unmodified native prompt/OK strings as well as Japanese
month/day suffix images. Owner VROM `0079DA50`, RAM `8089A350`, size 2,336,
SHA-256 `96c2b38dff3968ed6c138cfe83b5daceb8ff11b116a543ee6ac96f3ab58f10e8`;
relocation `0079E370`, 192 bytes, SHA-256
`976c3542d4cddf142d26c2b36562f50f5532c8ff92e8701e4720367f8ba0c736`,
sections `(2272, 64, 0, 16, 41)`. Asset `00ADD000` is 22,208 bytes, SHA-256
`e0f0c6847214f1c116448e2172c02639d379795f3e14531cbdb5094ad7a9c0a6`.
All three remain original in the current candidate. The prompt at `8089AC4C`
is read as ten bytes by `8089A8B4`; OK at `8089AC58` is read as three by
`8089AA44`. Only twelve/four bytes of current storage exist for these strings.
The complete GC prompt is "When's your birthday?", not a short guessed heading.

The GC birthday screen uses month-name textures, one numeric day, and OK.
Its `m_birthday_ovl.c` records the layout and native date/input behaviour;
month images are twelve 64×16 I4 resources in `tim_win.c`, not a direct
same-size substitution for the two native suffix images. Design the complete
presentation without changing birthday input or saved dates. Reuse the existing
clock counter integration pattern to add both discovered embedded strings to
the common text inventory; neither is counted as applied until installed.
Native disassembly is in `build/disassembly/birthday-artwork/code.asm`.

The GC Controller Pak editor is an unused stub and supplies no direct translated
screen. N64 Notes/Pages/remaining labels therefore need an English native-screen
solution; do not import GameCube Memory Card terminology or handling blindly.
