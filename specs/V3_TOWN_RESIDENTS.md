# V3 ordinary-town resident adaptation

## Policy

All twenty GAFE01-r0 additions retain their fixed actor identities, appearances,
names, phrases, personality values, starting garments, and authentic arrival rooms.
The eighteen islanders use the N64 town's existing personality-based schedules
and ordinary town interactions. The donor growth-role byte remains 2; a separate
explicit town-mode byte authorises this adaptation. Cheri and Punchy retain role 0.
The GBA island, island quests, and evolving gift-layout subsystem are not imported.

The experimental builder accepts `--enable none`, `pilots`, or `all`. These are
development integration modes, not public browser options. The complete-roster
cartridge enables twenty new IDs, without replacing any of the 216 original
villagers or using the two reserved test identities. Public composition still
requires off-by-default individual selections and complete dependency handling.
Neither local nor public web patcher changes without user testing and approval.

## Selection and storage

`overlays/v3/town_eligible.c` checks the runtime-ready flag, fixed identity,
installed metadata, personality range, original role, explicit town mode,
move-in flag, selected villager bit, and exact selected starting garment.
Any failed import dependency makes the new villager ineligible. Original IDs
0–215 remain eligible independently of import state; IDs 216–217 are excluded.

The twenty mode bytes occupy checked empty storage at `80461F60..80461F73`,
immediately after the relocated 224-byte native growth table. Flags remain at
`80461E60`, and metadata remains at `80462C00`. No saved field, identity bitset,
candidate array, shuffle array, or scene allocation grows in this batch.

The new policy and full-register-preserving bridge occupy 364 bytes at
`80473E40..80473FAB`. This fits the checked 448-byte gap between the clothing
helper and accessory registry. The private predicate at `804634B0` jumps to
the bridge; all other compiled selection instructions remain unchanged.
The bridge preserves full 64-bit caller-saved registers other than return value
`v0`, protecting callers compiled with knowledge of the old private function.
Neither policy nor outfit helper modifies HI/LO or floating-point state.

Unseen counts, history reset, move-in candidates, and initial population all
use this predicate. Initial shuffle length is 216 plus the eligible import
count; compact shuffle positions are mapped to fixed IDs before storage.
The native RNG, original growth restrictions, one-per-personality starting
population, fifteen resident slots, and existing appearance history remain.

## Native schedules

The unmodified schedule implementation at `800AEA80..800AEDDB` indexes its six
tables using the saved personality byte, not the villager ID. Complete schedule
data at `8010B970..8010BB27` is verified against the original cartridge, including
all entries, table headers, and pointers. The fifteen schedule slots remain at
`80137444`; there is no new resident-slot capacity.

Normal, peppy, lazy, jock, cranky, and snooty villagers use the corresponding
native home, outdoors, and sleep periods. The existing timed forced activity,
first-job/event outdoors override, and departure-slot release are retained.
This is explicit ordinary-town adaptation, not an island timetable simulation.

## Evidence and remaining work

The [checkpoint](../docs/checkpoints/V3_TOWN_RESIDENTS.md) records current hashes,
focused tests, and native execution. Resident selection and schedule components
have passing evidence. Full ordinary arrivals, conversations, house visits, and
save/restart integration remain separate gameplay work. The additional audio
instruments and aloha display/catalogue/acquisition consumers remain unresolved.

This cartridge keeps the preceding complete-house build's exact save profile
and format. That is not fresh evidence of bidirectional ordinary save loading.
Earlier builds without the aloha dependencies reject these profiles. Preserve
existing saves, use disposable copies, and do not call this a full V3 handoff.
