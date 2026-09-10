# V1 playtest fix contract

The [human bug list](../docs/V1_PLAYTEST_BUGS.md) governs this fix pass. Preserve
original saves, all earlier translation resources, and tested native progression
fixes. Build fresh artifacts and provide one combined candidate after related
implementation changes. Intermediate fixes are not a completed V1 release.

## Press Start source representation

The English GC actor `ac_animal_logo.c`, `aAL_press_start_draw`, selects
`log_win_logo3_tex` and `log_win_logo4_tex` through the compatibility
`gDPLoadTextureTile` API: IA8, 64×16, X 96/160, Y 159. These two resources are
already linear N64 intensity:alpha bytes. They are not GX tiled alpha:intensity
textures. Texture storage must be established from its consuming path, not
inferred from the platform or from equal dimensions.

The pinned REL and scoped symbol map bind `.data:005E5020` and `005E5420`, each
1024 bytes. Their complete SHA-256 values are
`3d1eeece6cdc4781e256c7eade05979bb57ea3206b52a9b5656bbea783cbae95` and
`98b37743e07fb6b472434f5a651bf5948d4e53d8675f159faf25743946ad1fba`.
Copy them without untile or nibble exchange into native bank `01136000` at
`1110` and `1510`; keep the third 1024-byte tile at `1910` transparent. Preserve
the title overlay, allocation, transition logic, positions, native blink,
colours, and graphics commands.

`tools/title_start_fix.py` installs this correction after the title/artwork
combination. The earlier `title_assets.py` IA8 outputs and title-only builds
remain replay inputs, not corrected final prompt assets. A new playtest built
through that older path must apply this correction. The main animated logo's
23 model textures have their own verified tiled source path and stay unchanged.

Repack from the verified original, recovering every retained native DMA index,
relocated owner, expanded resource, and added file from the exact preceding
cartridge. Retain both physical/DMA startup copies, recalculate checksums,
require the same 32-MiB cartridge and complete unrelated resources, and prove
UPS reconstruction. Do not append a replacement to a padded cartridge and
silently expand it to 64 MiB.

## Mail and board layout

The human report distinguishes correct saved/read display from incorrect edit
display. The read-only mail and notice hooks deliberately fall back to native
fixed-column functions in editing mode. The letter header adapter also retains
native body/footer cursor handling. Changing the grid alone cannot fix those
caller windows.

The correction must share pixel measurements between wrapping, text, caret,
end markers, and vertical navigation. Keep explicit newline bytes and native
field capacities; do not enlarge the 96-byte mail/notice body merely by doubling
columns. Preserve letter header/body/footer selection, recipient identities,
confirmation, publication, and saved formats. Names and gyroid/apology editors
already have separate adapters and must not be accidentally replaced.

`overlays/editor_pixels/` shares the resident `af_mail_next_line` scanner between
byte-indexed cursor positions, native insertion-fit checks, vertical navigation,
and caller-window drawing. The native sixteen-column/six-row allocation remains
96 bytes; only these two multiline modes use the new layout. One-row inputs and
the 32-by-four gyroid adapter retain their existing cursor routes. A terminal
newline or exactly full last line keeps the native final-row boundary convention.

The shared editor replaces entries `80885AEC` (position), `80885F6C` (up), and
`80885FCC` (down). Each has an inspected two-instruction trampoline for other
input modes. Native insertion, deletion, capacity multiplication, field selection,
confirmation, and save writers stay unchanged. The mail draft body/footer entries
`80889A9C/808899E4` call the existing proportional classic reader functions; the
outer snapshot/read hooks keep their original callers and return-address contract.
The letter cursor call at `8088A114` corrects only body/footer geometry before
delegating to the existing recipient-aware adapter. The notice draft body entry
`8089542C` and caret call `80895850` share the same pixel layout.

The grid-input wrapper recognises native header/body/footer pointer changes only
when the active mail field and actual editor pointer agree. Grid ownership cannot
remain tied to the initial body address after native field selection. Keyboard
movement and page/case/order changes call native sound `0032`, the original page
selection feedback ID. Successful typing/deleting/Done/caret feedback remains
owned by the native processed-command handler. Tests do not play audible sound.

The three overlays retain their VROM slots and relocation neighbours. All existing
prefix words outside explicit hooks are preserved at both tested relocation bases.
Their aligned combined growth is 4160 bytes. The existing submenu pool word
`25CE3220` becomes `25CE4620`, reserving 5120 additional bytes. The ordinary heap
ceiling remains `80400000`; the complete cartridge still requires an Expansion Pak.
This is an explicit allocation change, not an increase to any saved text field.

## Camera, cash, and idle clock

The shared `gameplay_keep` bank at VROM `00A22000`, segment `04`, contains all
three surfaces. `tools/hud_label_fix.py` modifies only this same-size asset after
the title/editor correction. The camera's native IA8 64×16 load at offset `04A0`
reads `08F8`. The English GC `cam_win_mojiT_model` at `.data:00880490` binds
the genuinely tiled IA8 donor `cam_win_camera_tex` at `0087EE40`. Convert its
storage, keep its complete pixels, and preserve native camera controls/geometry.

The cash label uses native 96×16 I4 at `B4D0`, with a load at `B480` and quad
at `B320`. GC `mny_win_mojiT_model` at `008972D0` binds the 64×16 I4
`mny_win_money_tex` at `008966A0` and four vertices at `008971E0`. Install the
complete English "Your Bells" image, zero the unused 256 bytes, compile the
64×16 clamped load into the existing 56-byte command space, and copy donor
XYZ/ST geometry while retaining native flags, vertex order, and colours. The
blue bubble, amount display, cash rules, and saved data stay unchanged.

The clock's six native display lists bind quads `29E0`, `2A20`, `2A60`, `2AA0`,
`2AE0`, and `2B20` to AM/PM, hour tens/ones, colon, and minute tens/ones.
Move AM/PM X by +36 and the five remaining quads by -15. The total horizontal
extent remains 84..133; every other vertex component and all display commands
remain unchanged. Native digit/AM-PM selection, colon blinking, timekeeping,
date layout, allocation, and saved formats are not patched.
