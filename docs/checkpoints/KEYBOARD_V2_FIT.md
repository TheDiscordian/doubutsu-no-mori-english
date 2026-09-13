# V2 keyboard shell fit

## Deliverable

V2-11 narrows the Cursor shell from 64 to 56 native pixels and moves its left
edge from X=236 to X=232. The C buttons and caption move eight pixels left to
stay centred within the narrower shell. Page/Done and their icons move four
pixels down, while the bottom shell shrinks from 36 to 30 pixels high with
15-pixel rounded corners. The shell's top remains at Y=198.

- ROM: `build/v2-keyboard-fit-11/Animal Forest English V2.z64`.
- ROM SHA-256: `8bbd1955536a2a3ac9f76d6f323842f5ce25c037e1ff5fd3da9f28d6dfe20507`.
- Original-ROM UPS: `build/v2-keyboard-fit-11/Animal Forest English V2.ups`.
- UPS SHA-256: `5ab213be6cd7b3499d99bbd18c477078c615da897aaa75e5e0b5bdfbd8cf6af0`.
- Construction receipt SHA-256: `3370b0d884caf2e6bbbc1d9ee24a4deee740417cb3152e0144022b8438c1dd93`.

## Construction and focused checks

Eight `tests.test_keyboard_v2_layout` checks pass in 4.199 seconds. The current
ROM changes only the keyboard's icon, caption, and shell position tables from
V2-10. Compiled instructions, relocation, owner size, textures, glyph metrics,
input handling, sounds, and every unrelated resource remain identical. The
editor remains 38,448 bytes, using its existing 8,192-byte suffix reservation.
The original-ROM UPS reconstructs the complete output, and all recorded
builder sources match. No allocation or save format changes.

The existing native scenario adds a held Start capture to inspect the lowered
Done button; its own same-build checkpoint is restored afterwards. It never
loads a previous-version checkpoint or opens a user save.

## Native fit check

`build/v2-keyboard-fit-native-01/` cold-boots the exact new ROM in silent,
isolated ares and reaches name entry through ordinary controls. All 47 result
entries complete, including eight-MiB, native-fault-zero, resident-guard, and
graceful-shutdown checks. The scenario exercises the existing keyboard actions
and records ten captures; the focused screenshot review inspects neutral,
Z/symbols, held Start, and C-right.

The screenshot skill guides review of the changed groups: Cursor is centred
within its narrower shell, Page/Done and their icons fit lower inside the
shorter shell, and held artwork remains visible without clipping. Original-
hardware appearance remains a human judgement. No old build is replayed.

- Native results SHA-256: `b13537465be9dc6bc2a79410e84a93f13948029c5981967abd18b792d483e90f`.
- Native run identity SHA-256: `81b75f717e763f8a94d6ccb0555490f1a5c614d9cc7f07f5f4a8485d6602b355`.

## Website and compatibility

The live local export is `build/web-portal-06/site`, with recipe SHA-256
`4978f8421d07eab4ee5c60d4198202e52698e8a8843c0ec4e0207b654b60102b`.
Its 23,093 commands retain 2,783,780 bytes of real GameCube donor copies; the
compressed recipe is 1,889,821 bytes. Five Pages staging tests and eleven
JavaScript patch-engine tests pass. Website prose and the trailer are unchanged.

`build/web-portal-check-11/` verifies actual silent Chromium downloads with
CISO, sparse ISO, and a Pages-style subpath. All three match the new ROM,
taking 0.69, 0.65, and 0.68 seconds. Cancellation, invalid inputs, download
clearing, and three responsive widths pass, with no browser errors or
non-local requests. The tracked Pages recipe and staging pins match this output.

V2-10 → V2-11 and V2-11 → V2-10 save compatibility are expected
without migration, not newly exercised loading claims. Earlier builds and
saves remain preserved. Expansion Pak, 128-KiB FlashRAM, and RTC remain required.
