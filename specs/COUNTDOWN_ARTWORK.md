# English countdown display

Use the supplied English GC countdown artwork for the two matching 128×32 CI4
atlases. Keep the original countdown numbers, timing, models, animation, palette
animation, calendar behaviour, actors, and streamed allocation unchanged.

Native object `D5E000` slice `6838..8C80` has SHA-256
`951601010899e42143c277c7aff2412923726bbce2a80bdacb71c8b16f886b01`.
Both seasons reuse structure type `21`. The current stream is the copied prefix
of object `03D00000`. Palette type `4A` resolves to `D5C0E8` in both seasons.
All visible colours match GC `.data:501800`; the native animated palette route
stays unchanged. The digit model is type `22`, outside the changed slice.

| Native texture | GC `.data` texture | Change |
| --- | --- | --- |
| `D65258` | `517E40` | Already identical; keep COUNTDOWN/NEW YEAR |
| `D65A58` | `518640` | Matching GC design omits `あと` |
| `D66258` | `518E40` | Replace `ふん`/`びょう` with `min.`/`sec.` |

The actual GC front and balloon model fixups bind T2 at `519B64`/`519BDC`
and T3 at `519B94`/`519C0C`. Their vertex loads bind `519B7C → 5198F0`
(twelve vertices) and `519BF4 → 5197F0` (sixteen vertices). Native T2 uses
fourteen corresponding vertices at its two readers, as does T3. Verify the
actual donor bindings and all native positions/UVs before installing unscaled
texture data. Native geometry, flags, lighting, and triangle order remain.

The main actor `944E90` is 2960 bytes, SHA-256
`4cd38ec47aa9e77dcb892daff87e8485ddb56de27b2b76e12f2bf0dc55cb9099`;
its relocation `945A20` is 240 bytes, SHA-256
`c52cbfe1f17a672d222c9a8a27de4c5c2d99b5d37d470ed5b681e28204ba68a2`.
The digit actor `94B4B0` and relocation `94BF40` also remain unchanged.

Verify both installed object copies, every other resource and seasonal stream,
and complete UPS reconstruction. Three original bitmap labels contribute seven
source characters to the shared counter. Seasonal/storage aliases add no IDs.
The omitted prefix receives explicit source-matching artwork-omission credit;
the two unit labels receive their exact English text. Ordinary countdown-event
and original-hardware acceptance remain playtest work, not assumed test results.
