# Complete world item-label checkpoint

## Installed

`build/world-names-pilot` connects the floating world item label to the complete
sixteen-byte English item resource. Its constructor, loader, proportional width
calculation, and draw call are installed together. The original forty-byte
state, ten-byte compatibility name, adjacent draw flag, and saved data remain
unchanged. Reset clears the private name; failed loads display the complete
`Name unavailable` error instead of stale or shortened text.

The [specification](../../specs/WORLD_ITEM_NAMES.md) records the native addresses,
width formula, ownership, and installation order. The complete line is centred
using actual font advances. Native text scale `0.875`, vertical placement,
colours, opacity, appearance/disappearance timing, item conditions, and artwork
remain. The GameCube reference's proportional-sizing intent is adapted to the
existing N64 mesh; the different GameCube mesh coefficients are not copied.
Neither measurement nor drawing performs resource DMA.

## Artifacts and memory

The separate startup font variant occupies 4,560 image bytes: 2,560 executable,
1,968 read-only, and 32 zero-backed state bytes. Its relocation is 464 bytes;
the existing system-heap loader requests 5,039 bytes including alignment.
This is 1,040 bytes more than the retained fourteen-glyph profile. The loader
keeps the same `0x3000` image limit, four-MiB bounds, CRC, relocation, and
fail-closed startup checks. The fixed resident module and submenu pool do not
grow. The complete build still targets four MiB; this is not hardware validation.

The existing font source and pixels stay unchanged. Both earlier font profiles
remain independently verifiable. The new profile changes only the font cartridge
blob and its eight-word resident configuration in the complete ROM; every
previous message, name, letter, overlay, editor, and native main-code resource
remains identical. World hooks are applied by the guarded startup installer.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Persistent image | 4,560 | `0e8d3860fea6f5d959e61dc0ce95b425f507fb42da16c3a6c2130bfcd2349db0` |
| Relocation | 464 | `247d442a7cd6c957ce097fe6845818582a98f411810c310be03223761e03353e` |
| Complete ROM | 33,554,432 | `df5eb3a45b2997345c6efd590c26a3f13c6c69b96b346d6fc999723279f2f71e` |
| UPS patch | 4,610,854 | `879b7a247dbde33266db4d3c7bb25a09db6cc56c0a7c767bf0795eec98cb0624` |

## Reproduction and passing evidence

With the retained inventory-description prerequisites:

```sh
python3 tools/build_extended_font_cartridge.py \
  --resource build/mail-glyphs/glyphs.bin --world-names --output build/world-names-font
bash tools/build_world_names_pilot.sh
python3 -m unittest discover -s tests -p test_world_names.py -v
```

Independent `build/world-names-font-repro` image, relocation, and complete report
agree. `build/world-names-font/font.asm` records the actual linked MIPS code.
The world reset, load, and measurement functions each use twenty-four-byte
frames; drawing tail-calls the original font function with no frame. The new
startup installer uses thirty-two bytes. These are individual function frames,
not the total nested stack requirement.

All six focused checks pass in `build/world-names-font/complete-tests.log`
(48.544 seconds):

- Sanitized reset/re-entry, full and narrow names, registered accent pair,
  partial-load failure/recovery, native-field guards, complete draw arguments,
  nonnegative width, centring, and no per-frame loads.
- Startup rejects each mismatched world hook and a rejected font install
  without partial world writes; successful and repeated installation preserve
  every unrelated word in the private host code map.
- Exact image/symbol pins, full native update/draw guards, real item-resource
  and resident-import dependencies, older font profiles, and relocations at
  three bases, including signed-low address boundaries. Altered code and
  state metadata are rejected even with refreshed self-reported hashes.
- Complete ROM/UPS reconstruction, retained catalogue/inventory integrations,
  all other cartridge resources retained, and unchanged combined source-ID
  accounting. Another display consumer does not earn duplicate text credit.

The four existing font/source/loader checks also pass in `font-regressions.log`.
The full main-code direct-control-flow scan finds only the retained native
`800CC318` branch entering the replaced width block at `800CC32C`; no direct
branch or jump enters the skipped interior. This is not a general indirect-call
proof. The installed width bridge restores the native state register before
resuming `800CC36C` and its phase/visibility logic.

## Remaining work

Ordinary world-label appearance, fade, scene changes, and new startup execution
join the combined v0 safety pass with the completed inventory, catalogue, and
editor work. No emulator scenario or hardware run is claimed for this batch.
The host and artifact checks do not substitute for that representative smoke.

Continue the existing remaining general-string/letter inventory, accented names,
and input/display consumers, then the bounded v0 pass and patch handoff.
The human playthrough follows that build. Title/image and GameCube-style keyboard
work remain in v1; the font-atlas investigation stays paused.
