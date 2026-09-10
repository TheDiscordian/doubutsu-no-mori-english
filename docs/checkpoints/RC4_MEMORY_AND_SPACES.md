# RC4 town memory and ordinary-space markers

## Reproduction and cause

The user reports that both RC1 and RC2 saves fail after character selection
in RC3, while creating a new file works. The supplied RC2 cartridge save is
copied from the SD card to ignored `local/rc2-save-report-g3O4lU/rc2.fla` and
verified against the original before the card is released. Its SHA-256 is
`d489736e39abc7eff1c5b5085bf52e679186f2882a0247339e11603799b80b60`.
Both redundant native payloads match and pass native signature/checksum checks.
The original copy and identical `test.flash` seed remain unchanged.

Silent isolated cold boots use that same seed and
`tests/rc3-existing-save-diagnostic.json`:

| Cartridge/run | Faulted thread | Largest free gameplay block |
| --- | --- | --- |
| RC2, `rc2-existing-save-diagnostic-01` | None | 12,480 bytes |
| RC3, `rc3-existing-save-diagnostic-01` | `80145630` | 304 bytes |
| Corrected, `rc4-existing-save-diagnostic-01` | None | 25,216 bytes |

RC3 deliberately faults at `80029AF4` by storing through `11111111`.
The fault client's strings are `ovlmgr: Out of Memory` and `528`.
`upstream/af/src/boot/ovlmgr.c:ovlmgr_LoadImpl` binds that size to the temporary
relocation table allocation, not the saved record or font size. The RC3 font
blob grows from 12,704 to 28,528 bytes; its retained system allocation reduces
the subsequently created gameplay arena. Apart from that font/configuration
change, RC2→RC3 only changes the transition scale and DMA metadata.

The shared scenario contains a no-op `debug` key; the valid runner key is
`command`. No register assertion is credited for that action. The diagnosis
uses the actual saved native thread context and heap instead. A successful
emulator process exit is explicitly not counted as proof of game success.

## Correction and source

[The font memory specification](../../specs/FONT_EXPANSION_MEMORY.md) establishes
the new exclusive `80450000..80457FFF` reservation. The unchanged font blob
loads at `80450010`, with sixteen-byte guards at both reservation boundaries.
The title ends before this region; ordinary allocators remain below `80400000`.
The compiled 536-byte replacement fits inside the existing 620-byte loader
function. Every other resident symbol retains its address. There is no new
ordinary allocation, save-format change, or glyph edit.

[The marker specification](../../specs/NAME_SPACE_MARKERS.md) changes the shared
name-window branch at `808847AC` from `17010030` to `10000030`, retaining the
delay slot and original continuation. Ordinary spaces no longer produce the
fixed-width `SP` decoration. Actual text, caret, input, grid labels, and saves
are unchanged. The original English GC renderer only uses that decoration for
its separate wide-space code.

Candidate `build/rc4-memory-candidate-01/animal-forest-memory-fix.z64`:

- ROM SHA-256: `5930435f588947df35313ae9cc2ea301af9fc7e68d59a7d8e13a48741d4f3067`.
- UPS SHA-256: `f0e7d50f644135ea99cecb11b84056151b07f28500a9b36d2fe07dc1244f16a1`.
- Loader SHA-256: `e3f287ef40b7bb2856984d10b43d2e8bdeebbc0b2a1d68105a82f08538362995`.
- Font blob SHA-256 remains `eee404b58a40916500934e1bc5b80025640e35fbea6159a540753e0147c7532f`.

## Completed checks and limits

Four `test_name_space_markers.py` checks pass for native branch behaviour,
mixed-width/repeated/leading/trailing spaces, relocation, retained resources,
and full patch reconstruction. Four `test_font_expansion_memory.py` checks
pass in 11.336 seconds, including a fresh pinned Docker compilation and host
address/undefined-behaviour sanitisers. Unknown resources, bad bounds, failed
DMA/CRC/entry, absent memory, and re-entry remain guarded.

`tools/rc4_native_evidence.py` independently checks the saved native RAM:

- Cold load: state SHA-256 `ed153cdc2024db5c3f36f12e5879f2bd726de03dfa6db0685206990749417eff`.
- Controller movement: `rc4-town-stick-01`, state
  `11edd72e6f3882926d30ace79a316de72567b4240fffd7575c222460db9b1f44`.
  Player moves from `(2128,160,1488)` to approximately `(2129.92,160,1622)`.
- Four-MiB rejection: `rc4-no-expansion-01`, state
  `12ec315b71ed6c39eb36905def04d43eeb13201586042c8c649b3b33fc6a73b1`.
  No font/title upper-memory owner or faulted thread; graph caller stops cleanly.

Complete relocated font contents match, including its required resource pointer
and sixteen spaces in the mutable town-name buffer. All font/title/module
guards and gameplay heap links remain intact. Native evidence is silent and
contains no screenshots or user-device audio. The first continuation used the
D-pad, which did not move this game; one justified follow-up uses the existing
analogue-stick `s` mapping and confirms movement. No repeated setup loop is used.

These checks do not establish a manual save/quit/restart cycle, RC3-created-save
loading, reverse loading into older RCs, broad gameplay, or original-hardware
acceptance. Cross-version compatibility is a preference, not a mandatory gate;
the fixed allocation crash is a stability defect independently of that preference.
The original seed is never modified; loading writes only isolated working saves.

## Handoff work

Commit the source, run `tools/rebuild_v1rc4.py`, and package with
`tools/package_v1rc4.py`. Packaging binds the complete native loading/movement/
unsupported-memory evidence, independently reconstructs the patch, and executes
the archived standalone patcher. Record the resulting revisions/archive hash
in the package checkpoint before handing over the fresh V1RC4 path.
