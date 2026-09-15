# V3 native summer calendar

## Result and current artifacts

ABI 73 installs the summer-camper calendar, independent expanded event index,
native readers, and initialization/cleanup hooks. Calendar activation depends
on at least one of the ten selected camping furnishings. All seventy original
event types, eighty-one native schedule rows, sixteen daily-event slots, and
the existing saved-event layout remain. Event-manager tent activation, a complete
visitor Animal, conversations/rewards, and lighting are still required.

Full integration:
`build/v3-campsite-calendar-runtime-02/animal-forest-v3-asset-loader.z64`.

- ROM SHA-256:
  `90279325c2c9c0b316e9705e741d4e1f7313c80b88df93e18736d0d84be35b6d`.
- UPS SHA-256:
  `e9574b51190990b89738b80a7410dafefc4a1105518c5038f40ead1405bb285a`.
- Build-report SHA-256:
  `b687603059f655afe7293887d265a66cbc8e868c91c8dddc68378ec5c2c4fedd`.
- Ten-item subset: `build/v3-optional-campsite-calendar-01/`, ROM SHA-256
  `8853dea5acd84b50361e0a1eec1c036d386136547c66bde4e2bab443f9a06eda`.

The offline composer contains 59 experimental choices. All selections reproduce
the full integration; no selections reproduce exact V2. Both served patchers
remain V2. These artifacts are not a complete-import playtest handoff.

Saved format 2 and selected identities are unchanged. Imported saves require a
matching/superset profile and must not be loaded in V2. The native check below
uses event-save structures in emulated RAM; it does **not** establish a FlashRAM
save/restart/reload cycle or cross-profile compatibility.

## Installed ownership

The checked package remains at VROM `02400000`, RAM `80473000`; its size is
`30000` (196,608 bytes), adding 4,080 bytes. Its physical storage and DMA directory
do not move. The package ends exactly before the existing resource at VROM
`02430000`, so future growth must relocate storage or add another checked owner.
The ordinary heap, model banks, and native daily-event capacity do not grow.

| Owner | Address | Bytes |
| --- | --- | ---: |
| Calendar/selection/lifecycle module | `804A2100` | 1,600 |
| Native calendar adapter | `804A2740` | 588 |
| Independent event index | `804A2B00` | 128 |
| Calendar operation/source packet | `804A2C00` | 256 |
| Final package guard | `804A2FF0` | 16 |

Only the calendar module entries have native callers. The compiled selection
and lifecycle functions still require the event-manager and visitor adapters.
The old package guard at `804A2000`, old scene packet, and all previous code/data
remain. The calendar packet has its own guard. Startup transfers/checks the full
package and invalidates code `804A0100..804A2AFF`, covering both calendar modules.

Forty checked instruction writes update eighteen HI/LO index consumers, two
type-loop limits, and two calls. Native initialization retains its sixteen
daily records and original BSS writes, then initializes the independent index.
All dynamic index readers move, including the original event-16 direct reader
and clearer. Pointers to the end of the daily-event array remain unchanged;
those coincidentally used the old index's start address.

The new calendar runs after the original job gate and scene-specific rows,
immediately before first-entry/old-event cleanup. Its return preserves the
native first-entry result. Native cleanup covers types 0–70. Shared native
readers handle type 70 through the new directory without reading adjacent BSS.

## Concrete defect found and fixed

The first native run (`build/v3-campsite-calendar-native-01`) found no camper
record after the calendar call. The observed record hash matched the empty
native record. This was a production binding defect, not a test-setup failure:
GameCube's current-week number is 7, but N64 uses 9; their last-week numbers
are 6 and 15. Sending donor byte `BE` to the native decoder requested the wrong
week. Native current-week decoding also lacks GameCube's month-end clamp.

`af_v3_campsite_decode_date` accepts the checked camper template only. It retains
the donor's current-week calculation/clamp and uses native `8E`/`FE` encoding
for first/last Saturday when required. The original date decoder and all other
event schedules are untouched. The module's separate day-subtraction helper
retains the donor's zero-day rollover. This also preserves the donor's exact
month-end Sunday result, rather than substituting a different weekend rule.

The fixed build is `runtime-02`; `runtime-01` is retained as a failed diagnostic,
not the current cartridge or composer base.

## Executed checks

All fifteen current focused/composition tests pass:
`tests.test_v3_campsite_calendar` (3) and `tests.test_v3_optional_composition` (12).
They cover all forty installed writes, unchanged native schedules and other
resources, full package preservation/expansion, DMA and cartridge checksums,
sanitized startup/CRC/cache paths, exact all/empty composition, subsets, and
profile dependency rejection. Unchanged module logic retains its separate
three-test evidence; that historical module suite was not replayed.

The corrected silent native run passes 112 records, 63 native calls, and 55
assertions, with no failed assertions:
`build/v3-campsite-calendar-native-02/results.json`, SHA-256
`47c8982572841c92784273e59be32b9bb0d04d47680c2d90158ebe7e28b006cc`.

Passing actual native execution covers:

- Complete installed calendar code/packet and independent index initialization.
- Saturday and Sunday insertion, start/end hours, the June-1 previous-month
  boundary, donor month-end clamping, inside-tent continuation, and exit-frame
  one-time activity.
- Original event-16 insertion alongside camper type 70, shared schedule/status
  queries, status set/clear, and retained native first-entry return.
- Native saved-event allocation, correct type/year/date header, cleared forty-byte
  payload, full camper-ID write/readback, and release. No FlashRAM save call runs.
- No summer entry when all ten camping selections are disabled.
- Retained neighbouring original BSS, existing save runtime, all checked guards,
  checkpoint restoration, and no faulted thread after resumed execution.

The probe uses only a 256-byte private bridge/schedule allocation; it does not
repeat the unresolved exterior field-allocation fixture. Startup and the test
are silent and isolated from user saves. The emulator exits cleanly.

## Next implementation

Bind the event manager and a real visitor Animal, including all masked identity,
appearance, defaults/clothes, greeting memory, and conversation readers. Do not
alias a saved town resident. Native event manager actor 52 uses VROM `00850680`,
linked RAM `8095B8B0..80962460`, profile `809622EC`, and actor size `250`.
Its current disassembly is `build/disassembly/v3-campsite-event-manager/code.asm`;
initialization calls `80961768`, and movement calls `809618A4`. Its native
controller layout is not assumed identical to GameCube's larger manager.

Then connect actual English conversation states, the donor's 20% Tent reward
selection with enabled-item filtering, lighting/sounds, and combined ordinary
entry/exit/persistence. The ABI-72 exterior allocation failure remains unresolved
for that meaningful gameplay batch. Neither source publication nor passing
native component checks authorises switching either web patcher.
