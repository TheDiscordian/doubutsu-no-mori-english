# V2 native verification and contrast work record

## Result

The preceding goal turn makes implementation progress: commit `fe79d8f` adds
the N64-inspired keyboard, guarded builder, development artifact, and focused
checks. This follow-up executes the new drawer natively, resolves the preview's
missing menu setup, reviews its actual isolated-display output, and improves
the panel contrast. It does not replay V1 builds or reopen accepted V1 fixes.

The current private ROM is
`build/v2-keyboard-03/Animal Forest English V2 Development.z64`, with a matching
UPS and `build.json` in that directory. The panel uses `(235,235,235)` highlights
and `(174,177,181)` shading. The screenshot shows all English keys and control
hints, native N64 A/B/Start colours, four C buttons, L/R shoulder graphics, Z,
and the left-side stick. Dark labels are easier to read against this lighter
grey than the first V2 panel. No font pixels, key positions, input code, sound
code, saved formats, or native controller pixels change.

## Exact artifacts

- ROM SHA-256: `df903c293c98c9c8f942c95c47f7a8b1fbd8298ce86aa78d82eae2a4644fcd90`.
- UPS SHA-256: `daf3e16e01c6274fab7fc3cdfe1ac49261ef6345190596d1816e4acb00d2d558`.
- Editor SHA-256: `d10d7d276925dfc5c8b85409d59b8c47e3f6e69d7dc9f50b91ffb0ccb4888eb4`.
- Relocation SHA-256: `681e9988d8c19766971d817d73ee3f7dae79eab042ff5b6736e6d7b5f9d6ce7c`.
- Native results: `build/v2-keyboard-native-08/results.json`, SHA-256
  `47f0f285cd7661aca3d96802530203c1ee652e5f53eaec5c4774df0c28ae4615`.
- Inspected screenshot: `build/v2-keyboard-native-08/v2-keyboard-display.png`,
  SHA-256 `7e36c992757f693936f3648d56590bf56ebc73a7544e66b6a3d5a587455aaada`.
- Fixture receipt: `build/v2-keyboard-03/preview/preview.json`, SHA-256
  `edd9c552bb315e96cbee7bbfa69c5af6447a6c6e32beb09e5780b8fc8f76f8b6`.
- Native commands: `build/v2-keyboard-03/preview/commands.bin`, SHA-256
  `86357fe276753962349063f6b05144b0f822265ffef5d1d4329e2b46be8255c4`.

V1 Final remains unchanged at SHA-256
`0561182044c1526010ed77b1b9c72ac268794c2f7b615f8fa70c007f366483bf`.
The new editor stays 38,048 bytes, with 7,808 bytes of rounded suffix growth
inside the existing 8,192-byte reservation. The relocation is unchanged from
the first V2 build. No additional pool allocation is needed.

## Passing checks

`python3 -m unittest discover -s tests -p 'test_keyboard_v2.py' -v` passes all
four checks against the current `v2-keyboard-03` artifact in 2.472 seconds.
The checks bind the current source/receipt, reconstruct the complete UPS,
preserve every unrelated resource and metadata field, retain the complete
input/editor prefix at two runtime addresses, and check font/key/native-asset
retention and allocation limits. `AF_V2_BUILD` can select a different current
development directory without editing the test or replaying historical builds.

The unchanged texture decoder retains the previous four passing checks. It is
not rerun merely because the panel's drawing colours change.

The silent, isolated native run passes:

- Both keyboard and parent load through the actual cartridge loader, with
  complete relocated images compared against the independent model.
- 155 complete draws, 55 expected rectangles: four panel corners, eleven
  controller icons, and forty keys at their accepted coordinates and UVs.
- 13,448 emitted display-list bytes within the actual graphics head/tail bounds.
- Grey material checks, no grid error, intact owner/scratch/resident guards,
  unchanged input/editor data, unchanged native artwork, and unchanged save RAM.
- Complete checkpoint restoration and graceful emulator shutdown.

The isolated-display screenshot is inspected, not merely generated. It confirms
the visible letters/hints, panel contrast, and native controller graphics in
this controlled context. Mouse-pointer capture is disabled for this screenshot
so it does not cover the Z graphic. The screenshot skill guides the appearance
check using the existing isolated capture path; the user's desktop and audio
outputs are untouched.

## Preview corrections and retained limits

`native-04` completes 136 safe draws after the explicit eight-MiB relocation
bound is supplied. This closes the earlier setup stops. Its raw framebuffer
image is not valid appearance evidence: later title drawing and asynchronous
GPU output obscure the requested view.

`native-05` adds late execution through the final overlay stream while keeping
commands/vertices inside the larger opaque allocation. `native-06` captures
the isolated emulator display and exposes the absent title-fixture menu
projection: icons are visible, but polygon text is outside the title camera.
`native-07` supplies the existing native orthographic font/menu setup and its
matching matrix-stack restore. Its screenshot displays the complete keyboard
and reveals weak dark-label contrast. These are fixture corrections, not
changes to ordinary menu or font behaviour in the cartridge.

`native-08` checks the new lighter-panel build. The current preview source no
longer exports debugger-read RAM as a purported finished framebuffer image;
it records commands and uses the isolated display capture for appearance.
Removing that misleading diagnostic export is followed by Python/diff checks,
not another gameplay replay. Existing diagnostic files are preserved.

The construction receipt's `native_tests`/`hardware_tests` placeholders describe
build-time execution only. This record and the native run's results own the
subsequent verification state; a placeholder does not queue another test loop.

This remains controlled rendering, not ordinary menu interaction or hardware
acceptance. Pressed-state appearance, V2's ordinary menus, and exact V1 Final
→ V2 / V2 → V1 Final save loading remain unexecuted. Formats, readers, writers,
identities, and capacities are unchanged, so compatibility is expected in both
directions without migration. Keep save backups and use the corresponding
EverDrive save filename. Expansion Pak, 128-KiB FlashRAM, and RTC remain required.

## Next work

The requested V2 keyboard implementation and controlled native appearance check
are complete. Preserve this evidence and the development handoff. Address
concrete human playtest findings, including ordinary-menu or pressed-state
appearance, rather than repeating the title preview or historical save tests.
No public release, new RC sequence, or speculative neutral-artwork sweep is
authorised. This does not claim the entire project's exhaustive hardware or
whole-game review is complete.
