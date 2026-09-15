# V3 ordinary summer-town check

## Current inputs and fixture

Cartridge: `build/v3-tent-lamp-runtime-02/animal-forest-v3-asset-loader.z64`,
SHA-256 `ff4e5ebafcb15d8ef777d569e0b2f4d29d848223d8e44ef15653c539796279d0`.
Only this current ABI-83 cartridge is executed.

The disposable `build/v3-campsite-town-seed-01/` binds the current format-2
profile to the preserved source town, SHA-256
`d489736e39abc7eff1c5b5085bf52e679186f2882a0247339e11603799b80b60`.
The resulting FlashRAM SHA-256 is
`e1a456f278e092d87bc7c74c9af4f9d2df9cda0f4b2a1206b8b473275c870d64`.
Every original payload byte except the signature/checksum remains unchanged.
No villager, tent, gift, or progress state is inserted. The separate emulator
RTC is August 22, 2026, noon, a summer Saturday. The host clock and source save
are untouched. One focused fixture test passes both banks through the actual C
codec and checks content/source retention and invalid-input rejection.

## Ordinary arrival and event placement

`build/v3-campsite-arrival-01/results.json`, SHA-256
`78dadab6abf64a0d39b1858ebfe228612b72f5f40591a4f6f1311bf199ecac0f`,
completes eleven records and three passing fault/guard assertions. Normal
controller input cold-boots the copied town and selects the player. Outdoor
scene 7 loads, with event 70 in daily slot 6 and foreground `5849` placed at
acre `(1,2)`, unit `(3,9)`, approximate world centre `(780,1660)`.
The test does not insert that foreground or invoke the placement function.
This establishes ordinary event activation and saved-grid tent placement.

The player starts at `(2128,160,1488)`, outside the tent's acre. No live tent
actor or lamp is expected there. The recorded camper-state header does not
include its Animal identity, so it is not independent proof of visitor
registration. The read-only observer includes that identity for future checks;
the completed arrival is not replayed merely to add another field.

## Bounded approach result

First approach: `build/v3-campsite-approach-01/results.json`, SHA-256
`0d3457ce093aee19680a4de769d68c75bfe8997a3d038915e26694d4c1839e2e`.
Fourteen records complete, with no fault and intact save/translation guards.
Westward movement stops at `(1858,160,1622)`. Private isolated-emulator captures
in `build/v3-campsite-route-view-01/` show the riverbank and a bridge to the
northwest. The capture tool uses the private X display, not the user's desktop.
The second view opens inventory rather than the town map; no map evidence is
claimed. Capture result SHA-256:
`86ecf00c39ec5dd43e5f28c7bc9b4a5dbd72cf43308bbd40f67818a6d7cb5259`.

The one corrected approach resumes the current checkpoint without replaying
arrival: `build/v3-campsite-approach-02/results.json`, SHA-256
`bf0dbb3df9103e6237497abf12d1891248715ecfb1781b612894373cfe79080b`.
Sixteen records complete with three passing assertions and graceful shutdown.
The route overshoots the bridge approach, ends at `(1578,160,1201.10)`, and still
cannot cross the river. The capture confirms that location rather than a tent
or an engine fault. Wall-clock-duration movement varies with emulator speed;
any future combined route should use bounded frame/position feedback.

Both navigation attempts are complete. Do not add more attempts to this batch.
Natural actor construction, tent entry/exit, GPU appearance, conversations,
reward handover, and ordinary save/restart remain unverified. The earlier
controlled exterior allocation result remains unclassified because this route
does not reach that code. The actual scene-lamp callbacks retain their separate
passing native evidence; this navigation result does not invalidate that test.

## Continue

Continue remaining masked readers and donor-content implementation. Retain a
later combined ordinary route without replaying passed unchanged prefixes.
The captures additionally show a zero hour around noon (`0:05 pm`); inspect the
current clock formatter before claiming standard English twelve-hour output.
That is a concrete rendering follow-up, not a CPU fault or permission to change
either patcher. Broad original-hardware acceptance remains the user's playtest.

Saved format 2 and selected identities are unchanged. Imported saves require
matching/superset profiles and must not be loaded in V2. Neither web patcher
changes until the user tests V3 and explicitly approves the switch.
