# V2 keyboard development work record

## Scope and result

The user authorises V2 development and explicitly withholds public release.
The private development build implements the requested grey keyboard panel,
N64 controller graphics, and left-side stick. V1 Final and all existing saves
and artifacts remain untouched. This is a development handoff, not a V2 Final
release or a claim of visual/hardware acceptance.

The changes preserve the complete current input/editor prefix except its draw
call, all forty key positions, glyph-origin metrics, consolidated symbol page,
sounds, proportional editing, bindings, and saved capacities. Native controller
texture tables and materials provide the original N64 artwork. The shoulder
image is blank, so mirroring it for L does not mirror any lettering. A/B/Start
retain their separate soft alpha mask rather than drawing the opaque colour
tiles alone. Pressed frames respond through the native read-only button getter.

## Artifacts

- ROM: `build/v2-keyboard-02/Animal Forest English V2 Development.z64`.
- UPS: `build/v2-keyboard-02/Animal Forest English V2 Development.ups`.
- Build receipt: `build/v2-keyboard-02/build.json`.
- Source asset previews: `build/v2-keyboard-02/artwork/`.
- ROM SHA-256: `28bfa59fa406765d785a3f8734efaaac8b0e1fe352bf4223d888cf2d124c1b03`.
- UPS SHA-256: `0d40c9a6ea204e01687766d8acae59997b6fcee4b5dc67dac875809c52feabf3`.
- Editor SHA-256: `9e8bde06110bc6c995b153671bfa9537444101fcbd177b8570bffce52958c97d`.
- Relocation SHA-256: `681e9988d8c19766971d817d73ee3f7dae79eab042ff5b6736e6d7b5f9d6ce7c`.

The editor image is 38,048 bytes. Its rounded suffix growth is 7,808 bytes of
the existing 8,192-byte reservation, with 384 bytes remaining and no additional
pool allocation. Compiler stack records show a 160-byte drawing frame and
64-/48-byte text/label frames. Compilation uses the pinned Docker image from
`tools/toolchain.py`, without network access.

The baseline SHA-256 remains
`0561182044c1526010ed77b1b9c72ac268794c2f7b615f8fa70c007f366483bf`.
ROM size remains 32 MiB; Expansion Pak, 128-KiB FlashRAM, and RTC requirements
remain. V1 Final → V2 and V2 → V1 Final save compatibility are expected with
no migration: no saved fields, identities, capacities, readers, or writers
change. Those particular load directions are not independently tested. Back
up saves and associate a copy with the new EverDrive ROM filename.

## Verification

Passing checks:

- `python3 -m unittest discover -s tests -p 'test_keyboard_v2.py' -v`: four
  checks against the current V2 artifact. They cover source/receipt hashes,
  complete UPS reconstruction, all-resource retention and metadata, prefix
  retention at two relocated addresses, wrong-input rejection, font metrics,
  native artwork, hint encoding, and allocation limits.
- `python3 -m unittest discover -s tests -p 'test_texture_preview.py' -v`:
  four decoder checks, including native RGBA16 colour and alpha.
- Python compilation and `git diff --check` pass.

The source inspection decodes native texture bytes only; those images are not
screenshots or evidence of in-game appearance. No old cartridge is rebuilt or
re-tested, no accepted save workflow is reopened, and no percentage tool is run.

## Bounded native-preview attempts

The preview is an isolated, silent, checkpoint-restored drawing fixture. It
does not alter the delivered ROM or the user's saves. The setup attempts are:

1. `build/v2-keyboard-native-01`: Xvfb is absent from PATH; the emulator does
   not start. The existing binary is available at
   `/home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb`.
2. `build/v2-keyboard-native-02`: with that explicit path, the title boots and
   the graph-thread checkpoint is reached. The extra 0x70000 fixture allocation
   does not satisfy the main-heap bounds. V2 drawing is not called.
3. `build/v2-keyboard-native-03`: the native retry uses verified-empty Expansion
   Pak scratch at `80510000..80580000`. Setup then stops because the host
   relocation model is still using its default four-MiB address bound. No V2
   keyboard code is executed. This is a fixture validation failure, not a
   demonstrated cartridge crash.

The final source correction passes `memory_end=0x80800000` to the existing
relocation model. It is not rerun in this batch. Native drawing, RDP appearance,
pressed-state appearance, and hardware acceptance remain unverified. The batch
does not keep looping on setup or mislabel the failed setup as a passing draw.

The next useful native check is the existing corrected scenario, not a new
harness or historical replay:

```sh
python3 tools/emulator_smoke.py \
  --rom 'build/v2-keyboard-02/Animal Forest English V2 Development.z64' \
  --output build/v2-keyboard-native-04 \
  --scenario build/v2-keyboard-02/preview/scenario.json \
  --seconds 180 --expansion-pak --no-initial-screenshot \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb
```

The completed preview should verify guards and unchanged input/save data,
retain forty key rectangles, validate the grey material and eleven controller
rectangles, capture the actual native framebuffer, and restore the checkpoint.
Until then, the development build is available for human playtesting without
calling the V2 appearance finished.

## Reproduction

```sh
python3 tools/keyboard_v2.py --output build/v2-keyboard-next
```

The builder requires the preserved V1 Final ROM, original Japanese ROM, and
already-extracted supplied GC reference. It refuses changed source hashes and
existing output directories, generates new local artifacts, preserves unrelated
resources, and verifies patch reconstruction. No full historical build chain
or public upload is required.
