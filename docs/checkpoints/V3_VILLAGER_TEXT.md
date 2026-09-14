# V3 villager text checkpoint

## Result and artifacts

Both pilots have shared full-name and default-phrase readers, actual dialogue
insertion support, six-byte compatibility names, and native catchphrase reset
and propagation. Original name/default resources are preserved. Five focused
tests and a combined silent native check pass. Move-ins remain disabled.

- Current build: `build/v3-villager-text-02/animal-forest-v3-asset-loader.z64`.
- ROM SHA-256: `e4bdfab3fac69bb6be1f6bd6850611765e960b9242fd36a4212328cc1faa2b1f`.
- UPS SHA-256: `8ce74979b0d2d34f209ceda68486408ca1284d76b50ad2587b22d0e776cee124`.
- Blob SHA-256: `b3449045a80a79663a74ad9ed30efe836a854879c36b017cfa73c1e9dd1e6b64`.

Build 02 corrects report terminology: the V3 reference is a new saved-value
format, although the saved layout does not grow. Its ROM, UPS, and installed
code match build 01, on which the native check ran. No old cartridge is replayed
for this reporting correction. `build.json` binds current sources, complete
donor/reference hashes, and installed hooks.

Startup remains 432 bytes; asset/draw/audio code remains 2,032 bytes. Text code
is 992 bytes, with 24-byte wrapper frames before original-code delegation.
The blob grows from 16 to 32 KiB within the established 64-KiB reservation.
No ordinary heap grows. Cache invalidation includes the new code and return
bridges.

## Focused verification

`python3 -m unittest tests.test_v3_villager_text -v`: five tests, no skips.

- Address/undefined-behaviour-sanitized full/short/actor names, native fallback,
  phrase lookup, borrowing, custom text, reset, invalid/missing/disabled cases,
  unaligned output, and adjacent guards.
- ABI-4 startup/cache range, RAM/configuration/CRC/header rejection, repeated
  initialization, and original object-loader checks.
- Installed metadata, empty slots, complete text, reference keys, code, CRC,
  configuration, and end guard.
- Hook destinations/return bridges and unchanged original name/default/house
  resources.
- Current sources, save warning, complete UPS reconstruction, and exact
  translation-only V2-11 output.

## Native evidence

`build/v3-villager-text-native-01/`: current text cartridge, Expansion Pak,
private Xvfb, audio disabled, no initial screenshot, no seed save, and no
FlashRAM/Controller Pak write opt-in. The first attempt completes with 99
recorded steps and exit status 0. No retry is needed.

- Results: `fdbafdc763cc8f50b1a50b6794e386f0f019ba2148ea5a3a87338748ea2e1c5e`.
- Run record: `034bb859da5fa2db731f0560ffed8428797dfb1352b6097229d4d941dc62d4a2`.
- Scenario: `9a419c4ca7745cd9efc44aa06c37fba6ed3b8997792fdbb056f0f997d373e1d2`.
- Fixture: `8979230ff76c638348027503f41e9f5ff2eec808b729f516be1999d3d74243bb`.

For each pilot, actual native reset changes only four bytes in the complete
synthetic animal. Eight-byte lookup, six-byte compatibility lookup, actor-name
lookup, actual talk-name insertion, full phrase lookup, actor phrase, and actual
main/shared catchphrase insertion produce complete English. The native setter
copies the other imported reference without changing neighbouring animal data.
Custom `Yup!` remains literal; an original borrowed default resolves completely.

The original reset routine executes through its return bridge and changes only
its own four-byte key. An original villager keeps its name/default and can borrow
either imported phrase. A special actor keeps its original full name. Missing
imports and undersized destinations do not write. Unaligned outputs, message,
fixture/stack, complete-blob, and translation guards pass, with no fault. The
checkpoint restores the emulator before ordinary execution resumes and exits
cleanly.

## Limits and continuation

The fixture supplies actor/animal records: it does not prove full construction,
normal conversations/borrowing events, move-in, houses, or game save/restart.
Previous audio/draw evidence is retained for unchanged code, not relabelled as
new execution. V3 original hardware remains untested.

Next: initial defaults, verified native clothing/umbrella mapping, house records
and layer contents, roster selection, secondary ID-bounded name/mail readers,
and save/profile guards. Furniture and broader imports remain open.

The new `FE F3 ii 20` references require V3 and compatible profile metadata.
Do not load saves containing them in V2. Removing imports must account for
borrowed references in original villagers, not only imported actor IDs.
No user save is touched. Stable V2, both patchers, and the trailer remain intact.
V3 source may be pushed to GitHub; switching the web patcher awaits the user's
testing and explicit approval.
