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

## Notice dates and tune labels

The notice paper's slash is a distinct 16×16 I4 image at asset `00ABA000`
offset `CE18`. The model at `9F20` uses texture alpha and draws two quads at
`9B90`, over the date's month/day boundaries. Clear only the 128 texture bytes;
zero intensity is transparent under that bound combiner. The English date
reader, paper, draw commands, and geometry stay unchanged.

The unmodified tune overlay `0079C020` has a 16-row note table at `16A0`.
Each 20-byte row stores frame pointer, segment-C texture pointer, float Y offset,
and two RGBA colours. GC's `note_moji` at `.data:00080B58` uses 36-byte rows
with the same note ordering/Y/RGB values. Bind both tables before replacing
textures; the native segment-9 load at tune asset `00AD1000:0330` samples
16×16 I4, matching GC's `onp_hyouji_moji1T_model` at `004A2488`.

Install the GC A–G textures and random-note `?` into eight native 128-byte
slots. Rest and off already match the English source and remain unchanged.
Preserve note indices, pitches, sounds, animation, colour, frame, and saved
melody. The English OK model `004A9310` binds its quad at `004A8DE0`;
copy its XYZ/ST into native `3650`, retaining native flags, colours, and order.
The corrected X extent is 74..106 and Y is -63..-47. Native N64 controls stay.

## Inventory money bubbles

The native money renderer at `808802A8` in overlay `00785700` draws each of
five digits separately, stepping 12 pixels, at scale 0.75 on both axes. The
halfwidth atlas leaves five ink columns starting at zero, so each digit occupies
only 3.75 pixels at the left edge of its slot. This is not a string-spacing bug.

`tools/inventory_money_fix.py` changes this caller's X scale to 1.25 and first
origin from 122 to 123.5. Ink becomes 6.25 pixels wide inside each original
12-pixel slot; Y scale stays 0.75. Four non-relocated instructions change.
The duplicate `t2=255` becomes the float 1.25 bit pattern; alpha reuses the
existing `t0=255`, and only the X-scale stack argument uses `t2`. The original
font call, one-digit length, colours, height, five-slot loop, division/remainder,
leading-zero suppression, money value, font resource, other readers, and all
allocations remain unchanged. No new code space, saved data, or global font
metrics are required.

## Letter address prompts, names, and draft defaults

`tools/letter_ui_fix.py` appends checked helpers to the address and board
overlays. The address owner moves from VROM `00792700/00794240` to
`03E60000/03E68000`, retaining its DMA indices and linked RAM `8088ADB0`.
Its original 416-byte BSS becomes explicit zeroed prefix storage. Board remains
at `03B60000/03B70000`, linked `80888E90`. Preserve every prefix word outside
the three named calls, with independent relocation checks at two heap bases.

Address font calls `8088BB60/8088BEFC` select the prompt and recipient adapters.
The two exact twelve-byte native prompt arrays at `8088C888/8088C894` select
the complete GC `.data:0007A5E8/0007A5FC` arrays: "Choose an addressee." and
"Your address book is empty!". Match content and length, then centre using the
installed proportional width routine. Preserve bubble, colours, Y, and animation.

The recipient caller passes a complete native eighteen-byte Mail name record.
Byte `10` identifies NPC type one, and byte `0C` is the NPC identity index.
For any of the 216 supported villagers, request `E000 | index` from resident
`af_load_display_name` at `80196044`, into eight temporary bytes. The installed
table maps index 132 to Limberg and 140 to Buzz. These are test cases, not special
cases in the implementation. Player/unsupported records retain their six saved
name bytes. Failed lookups restore the fallback even if the loader partially
wrote its output. No saved name, identity, town, or recipient-selection byte is
rewritten. This shared fix covers possible affected villagers beyond the single
reported Limberg case.

Board constructor call `8088A750` wraps the retained native init `8088A2D0`.
After init, WRITE/EDIT modes zero/two normalise only exact stock draft defaults.
The ten-byte header `さんへ` plus padding, with split zero, becomes `To ` plus
padding with split three. A stock footer equal to the trimmed sender name plus
`より` and padding becomes `from ` followed by that same player name. The source
wording is GC `.data:0007B374/0007B378`. Native capacities remain ten/sixteen
bytes, and the body remains ninety-six. Custom templates, read modes, body,
recipient/sender identities, and stored mail are not broadly migrated.

Combined aligned overlay growth is 1536 bytes. The submenu pool receives 4096
bytes (`25CE4620` to `25CE5620` at `800C4B10`); ordinary heap `80400000` and
eight-MiB cartridge requirement remain. Explicit VROM moves reject collisions,
unknown owners, unaligned destinations, and startup/DMA-table relocation.

## GameCube keyboard background

`tools/keyboard_background_fix.py` replaces the plain beige panel with the
English GC `kai_sousa_mojibanT_model` material (`.data:00420730`, 104 bytes).
Its active pointers bind two genuinely tiled 32×32 IA8 textures at
`004124C0/004128C0`, and sixteen vertices at `0041FFF0`. Two four-triangle
groups assign the complementary upper/lower corners. The donor clamps both
texture axes; half-panels sample 64×32 texels of each 32×32 image.

Keep the complete converted texture pixels, GC primitive colour 225/205/225,
environment colour 160/90/245, texture alpha, bilinear filtering, and corner
directions. Adapt the four quadrants from the GC 180×73 key background to the
existing 236×114 N64 panel, so native control hints remain backed and readable.
This is a sized adaptation, not a claim of identical complete GC keyboard art.
The 40 key positions, keycaps, selection colours, labels, all input handlers,
pixel-editor fixes, and saved capacities stay unchanged.

The N64 combine words `FC30FE61 55FEF379` encode the same equation in both
RDP cycles. The GC command `FC30FFFF 5FFEF238` encodes the material only in its
first cycle. Comparing the full packed words is incorrect; both native cycles
must match that donor equation. Each RGB channel is primitive times intensity
plus environment times one minus intensity, with alpha directly from texture.

Derive the new drawing function mechanically from the hash-checked prior grid
source, changing only its name and panel helper. Preserve the prior installed
editor in full except call `808882D8`, and retain native encodings of the two
control hints in the appended copy. Imports into the prior editor receive local
relocations; resident font imports remain absolute. The new 35,392-byte editor
moves from `03940000/03948000` to `03E70000/03E80000`, preserving DMA indices
and linked RAM `80885140`. Its 2,512-byte relocation resource and owner metadata
are updated together. Aligned growth is 5,120 bytes; the shared pool receives
8,192 (`25CE5620` to `25CE7620`). Guard the signed immediate against crossing
`8000`; the ordinary heap remains `80400000` and requires an Expansion Pak.
