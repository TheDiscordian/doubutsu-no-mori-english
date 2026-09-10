# Embedded menu text

## Scope

Translate native editor confirmation, inventory warnings, and Controller Pak
status/error windows. These strings live in menu overlays, not the main text
banks. Their original identities join the same text-application inventory.
Preserve the actual N64 limits and operations: its displayed wallet limit is
50,000 Bells, not the GC warning's 99,999. GC bank/diary-specific screens are
not native N64 features to import.

## Editor confirmation

Owner `00799580`, RAM `80895E00`, 3,168 bytes, SHA-256
`075807e24ac1374be646561638d14c6d0d355e478b89efb232f7b6347f20504b`.
Relocations `0079A1E0`, 176 bytes, SHA-256
`29d17144eaf385a563aff0838a39caff74c04bbc0baca13ec5ea57446ca5249e`;
sections `(2896, 256, 16, 16, 37)`.

The complete supplied GC strings fit existing slots: Is this OK? at `0BF4`
(12 bytes), Yes at `0C00` (4), Rewrite at `0C04` (8), and Throw it out at
`0C0C` (12). GC donors are `.data:0007F46C`, `0007F478`, `0007F47C`, and
`0007F484`. Bind the supplied REL and symbols, all source bytes, and exact lengths.
The prompt reader at `80896500` changes nine to eleven characters; its X origin
at `808964B0` changes 96 to 119 to keep the original text's centre with the
installed 62-pixel English width. The three answer pointer/length records at
`0C18` retain their pointers and change lengths to 3, 7, and 12. Positions,
colours, selection/cancel/discard handlers, file size, BSS, and relocations stay
native. No saved editor text changes.

## Inventory warnings

Owner `0079A290`, RAM `80896B20`, 3,392 bytes, SHA-256
`05cf6aa2ae96ddcfeaea98af50b34d3b432602277da5dbf3c09042cb2c15a47b`.
Relocations `0079AFD0`, 336 bytes, SHA-256
`a583a6a5ecf59b2fed4cc561d17bf361e990b4c227e7cfbf91b0f99ab0ce8e13`;
sections `(2192, 1200, 0, 16, 78)`.

Sixteen window records at `0C08` reference 34 line records at `09E8..0C07`.
Each line is X, Y increment, pointer, and character count. The first window
has two body lines and two choices; the others have two body lines. The native
drawer adds sixteen pixels after each line in addition to the stored Y increment.
Keep the four-line mailbox choice structure and native selected indices 2/3.
The GC equivalent has three body lines and selected indices 3/4; blindly
importing that table would break the native cursor/choice mapping.

The warning window asset is `00ACA000..00ACBA20`. The native parent loader
record is `007749C0 + 2C10`:
`0079A290 0079AFD0 80896B20 80897870 8089730C 80897394 8089728C 00000000`.

## Controller Pak status/errors

Owner `0079F810`, RAM `808A2EA0`, 5,936 bytes, SHA-256
`a30ee0787e1f5af42f95574ee2e6cc8265af43ad2bc9a0198853681399d9162c`.
Relocations `007A0F40`, 416 bytes, SHA-256
`c64e7efe9879f74fba6eb9112d9c5629182f5b64e3d85668918aac335c4dbe9b`;
sections `(4864, 1056, 16, 16, 98)`.

Thirteen window records at `1610` reference thirty line records at `1430..160F`.
Window 10 reuses window 3's three insert-Pak lines. Windows 11 and 12 are the
Reconnect/Repair/Quit and Yes/No choices. Keep selected indices and actual
reconnect, repair, deletion, reading/writing, and close actions unchanged.
Explain potential data loss before repair, without claiming repair is safe.
The native parent record at `007749C0 + 2C50` is:
`0079F810 007A0F40 808A2EA0 808A45E0 808A40F0 808A4188 808A4058 00000000`.

## Warning storage design

Append complete English warning strings after each native image and its existing
sixteen-byte BSS. Retain the BSS at its original relative address as zero-filled
loaded storage. Redirect only the existing line pointers/counts, adjust body
text centring/window width as needed, and preserve all code and control handlers.
Flatten relocation section offsets while retaining every original relocation
type/site and order. No new local pointers are needed for plain appended text.

Reserve separate VROM pairs `03E00000`/`03E10000` and
`03E20000`/`03E30000`, preserving native DMA indices and adjacent relocation
entries. Update only the two reviewed parent records. The shared submenu pool
must explicitly cover both image growths; allocate a bounded additional 4 KiB
through its existing size constant, without changing ordinary heap limits.
The current grid pool word is `25CE2220` at `800C4B10`; the additional reservation
uses `25CE3220` and retains the high-half contract at `800C4AFC`.
All shared-owner/pool verifiers must recognize only the fully verified new
pair before accepting these metadata and allocation changes. Existing prior
builds retain their original strict verification.

## Acceptance

Bind complete source/reference images, native line tables, original IDs, all
replacement wording, actual installed font widths, relocation at several heap
addresses, parent metadata, and conservative pool bounds. Retain every unrelated
resource and verify UPS reconstruction. Use a focused combined native drawing
check for complete English and unchanged state/guards; do not invoke destructive
Pak operations in a test. Ordinary menu/hardware acceptance remains separate.

The [implementation checkpoint](../docs/checkpoints/EMBEDDED_MENU_TEXT.md)
records installed candidates, passing host/combination checks, and the incomplete
native drawing batch. Installation does not establish ordinary menu acceptance.
