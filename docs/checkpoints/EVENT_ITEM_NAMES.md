# Event and home item-name integration

## Installed state

The complete combined build is `build/event-item-names-pilot`, produced by
`bash tools/build_event_item_names_pilot.sh`. The wrapper retains every prerequisite
of the [town/shop/player build](TEXT_NAME_CONSUMERS.md) and enables
`--english-event-item-names`. Generated ROMs, resources, and patches remain local
and ignored. The private repository stores implementation and verification tools.

Seven item-name preparations across six native actors use the existing complete
sixteen-byte resource and zero-safe message bridge: two home-room prompts,
Police2 lost-and-found, opening Nook, outside Redd, Saharah, and the fishing-event
reward. The [specification](../../specs/EVENT_ITEM_NAMES.md) records source
expressions, slots, main-window provenance, and installation guards.

The adapters preserve the original field slot, including outside Redd's slot two.
All other actor instructions, price/quantity logic, item transfers, selected
messages, line/page/timing commands, relocations, and BSS remain. No actor,
resident module, heap reservation, or saved field grows. Main code and the shared
bridge are identical to the preceding player build. The actual memory requirement
remains four MiB; this is not original-hardware certification.

## Artifacts and checks

- ROM: 33,554,432 bytes, SHA-256
  `668f1f69f7a6d3fee0cf33c2e44c4f23289124e92d33eff3661ac150ee64d4f3`.
- UPS: 5,053,837 bytes, SHA-256
  `71b56ee94bc335fdbb01b67334dc22afd077723aa8efcdc0eea122668cb5994c`.
- Seven independently assembled adapters: 236 instruction bytes, SHA-256
  `ac2db60c47a8185c0afaa741a7a70cc41c43bef6a9580ac3a7b6b695ebf531fa`.
- Existing bank edits: 13,769, unchanged. These connections apply already
  installed full English names in additional player-facing paths.

Reproduce focused checks with:

```sh
python3 tools/check_event_item_assembly.py
python3 -m unittest discover -s tests -p test_event_item_names.py -v
python3 -m unittest discover -s tests -p test_item_fields.py -v
python3 -m unittest discover -s tests -p test_translation_progress.py -v
```

All five focused tests pass: three core checks in 3.796 seconds and two
cartridge/accounting checks in 28.723 seconds. The core checks cover original
item/slot expressions, shared empty-field behaviour, source/dependency rejection
without partial writes, unchanged surrounding instructions, and relocation at
two bases including the home actor's 8,944-byte BSS. The complete-ROM comparison
requires all virtual file IDs and sizes to remain; only six actor payloads and
physical DMA address pairs differ. Every other decompressed payload is identical,
and the UPS reconstructs the completed ROM. Build checksum and installed-route
verification pass. No setup retries or native test-harness work are needed.

Five existing resident item-field tests pass in 0.115 seconds, including complete
insertion, shorter/empty replacement, invalid inputs, native fallback, and buffer
limits. Twelve fast progress-counter tests pass. The combined accounting check
verifies the installed event/home route and retains pending status for original
names with other unfinished readers. It does not duplicate IDs, equate resource
presence with application, or refresh a user-facing percentage unasked.

## Next implementation

Continue the existing reader inventory, not another source-matching audit:

- Festival-stall choices use the native ten-byte loader at `80A72E74`. Their
  four-row stack buffer is `sp+78..A0` inside a 168-byte frame; the live choice
  pointer at `sp+A0` must move if rows grow. The resident choice setter already
  accepts twenty bytes. Complete sixteen-byte names can use a larger local array,
  retained selection logic, and the existing full loader. Two embedded cancellation
  labels also need the exact English reference. Source disassembly is retained
  at `build/disassembly/stall-choice/code.asm`; the pinned GC counterpart is
  `local/ac-decomp/src/actor/npc/event/ac_ev_yomise_move.c_inc`.
- Native free-string item wrapper `800BB6F0` and direct free-field preparers need
  complete storage and reader connections. The ordinary free setter at `8009D6D0`
  uses twenty ten-byte rows at main-window offset `38` and resets flags for slots
  one, two, and five. Do not widen its writes or omit those flag semantics.
- Dynamic-choice substitution, character/display names, default catchphrases,
  remaining general/letter text, and accented names remain main-translation work.

The ordinary lost-property, opening-shop, visiting-shop, fishing-event, and home
paths join the combined v0 smoke with boot, other menus/dialogue, and save/restart.
No native gameplay or original-hardware test is claimed for this batch. Confirmed
crash/save/memory defects remain v0 blockers. Human playthrough follows the v0
build; public-release preparation and v1 title/keyboard work remain open.
