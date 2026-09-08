# Renewal delivery work record

Complete English renovation letters are installed in the optional renewal pilot.
The runtime prepares a whole snapshot before copying any eligible home, preserves
native recipient/slot selection, and retains the pending notification on failure.
The [specification](../../specs/RENEWAL_LETTERS.md) describes the actual boundaries.

## Executed evidence

- Nine host adapter/installer tests pass in 9.041 seconds.
- Independent `build/renewal-actor` and `build/renewal-actor-repro` code,
  relocations, and manifests agree.
- `build/smoke-renewal-actor-01` passes 24 complete combinations and five
  eligibility cases, 165 calls, and 532 memory assertions.
- An additional post-restore assertion passes; the original checkpoint resumes
  and the emulator shuts down gracefully.
- Real native cartridge loading/relocation, actual caller gate, mailbox copies,
  whole-save comparisons, and complete saved-letter restoration are exercised.
- Disabled-catalogue failure retains all mailboxes and the notification flag;
  retry uses that retained state and clears the flag only after success.
- Allocation and stack guards, live-save/global restoration, heap accounting,
  and unchanged RNG/handbill fields pass. Isolated FlashRAM remains all `FF`;
  the Pak remains the blank fixture. No user save or physical hardware is used.

The full regression batch is tracked in
`build/tests-renewal-actor-regression.log`; only its completed result may be
reported as passing. Normal scheduling and shop progression remain unverified.

## Artifact identities

- ROM `build/renewal-actor-pilot/animal-forest-halfwidth.z64`:
  `7655a1cb1653a2535eebc6fe4addf290bdbd33c5ef9e4ef54114ba31713fb69f`.
- Actor, 7,472 bytes:
  `481e9aeb8fe8e7e42bdeab13d349c00747a8703eb13d4e740395772938305aeb`.
- Relocations, 208 bytes:
  `21776d6c069586cece7451cdce4859fcfd7e772f69b6d62244cdf0640e9a1b18`.
- Scenario:
  `48ddbd779c422f40302041167ad4f566da2eb91a5f8b448f7ac3cfeba9f193ad`.
- Native results:
  `28937a8e3c80737fba202d6d5528c4fecf061f173e78f634c0485ed76bdcc5ac`.
- Native helper:
  `73741d39897cd02ab07c6ea120132b63ac50ecd8a3a7ca2a2e713abfa90dfbb7`.
- Silent runner:
  `ab6636602a589c44264b734cff789dc3860dd0533dabf3e5fde3dcc1eb36b4b6`.

## Reproduction and remaining work

Build the existing leaflet creator with `build_mail_generation.py --leaflets`.
Build the adapter with `tools/build_renewal_actor.py`, supplying the native ROM,
current module manifest, and creator directory. Add
`--english-renewal-letters build/renewal-actor` to the complete ROM build with
`--english-leaflet-dates` and `--english-mail-snapshots` and their dependencies.

`tools/renewal_actor_scenario.py --output build/renewal-actor-scenario.json`
binds the default pilot and expected complete English content. Run that scenario
with the existing silent emulator runner, a new output directory, and a 240-second
bound. The original cartridge/Pak images and all game assets remain ignored.

Next: connect event-manager sale/Redd publication, with full selected item names
and retained chosen inputs. Its mode-two saved-event destination differs from
renewal home mailboxes. The original parent initializer discards child returns;
failure propagation and pending ownership require explicit integration. Main
translation, remaining general text, review, normal gameplay/save validation,
title artwork, keyboard stretch work, and patch-only release preparation remain.
