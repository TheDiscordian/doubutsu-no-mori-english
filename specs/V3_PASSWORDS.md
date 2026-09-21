# Shared GameCube password acquisition

## Scope

Use the donor's code routes for password rewards instead of placing
those items in unrelated shop stock. One codec and shared eligibility rules
serve the category; item records supply identities and selected destinations.
This does not imply that every decoded item is present in the native game.
The codec, eligibility, and selected-import reader are linked in the experimental
cartridge. No input UI or gift delivery is installed.

The algorithm reference is the pinned CC0 ACreTeam/ac-decomp
`src/game/m_mail_password_check.c`; Nook's result and handover rules are in
`src/actor/npc/ac_npc_shop_common.c`. Extraction checks the supplied GAFE01-r0
REL and symbols, the complete codec instruction range, root/key/selector
directories, and complete table lengths. Data comes from the supplied disc;
generated tables, strings, reference translation units, and objects stay ignored.

## Prepared format and API

`tools/v3_password.py` emits the bounded big-endian `AFPW` version-1 packet.
Offsets are fixed; strings preserve their complete source lengths, including
terminating zero bytes where the source key includes them.

| Offset | Bytes | Contents |
| --- | ---: | --- |
| 0 | 32 | Magic, version, total length, dimensions, text range, zero reserved fields |
| 32 | 64 | Password alphabet in donor-font encoding |
| 96 | 256 | Substitution permutation |
| 352 | 512 | 256 prime values, unsigned 16-bit |
| 864 | 128 | Sixteen eight-byte RSA/shuffle selector rows |
| 992 | 128 | Thirty-two absolute-offset/length pairs, unsigned 16-bit |
| 1120 | variable | Complete transposition keys |

`overlays/v3/password.c` exposes bounded encode/decode operations. Both require
exactly 28 input/output characters and write the destination only on success.
There is no heap, RNG, fixed RAM address, saved-state access, or per-item rule.
The canonical descriptor is 24 bytes: item, type, hit-rate index, NPC type/code,
checksum, reserved byte, and two eight-byte name fields.

The codec accepts ASCII `#` and its donor glyph 209. It retains the donor's
`0 -> O` and `1 -> l` aliases, while retaining case for every other letter.
Encoding outputs ASCII `#`. The descriptor's names remain donor-font bytes;
native display/saved-name conversion belongs to the frontend and must preserve
the entire name and space padding. Names containing only spaces must not pass
the source name-equality rule merely because both fields are equal.

The transform preserves substitution, both transposition stages, both bit
shuffles, reversible bit mixing, RSA selectors/high bits, six-bit packing, all
six types, and the source checksum. Modular exponentiation uses bounded
square-and-multiply. Decryption's inverse search is bounded; malformed tables
cannot create the source's unbounded search. The first three primes remain
17, 19, and 23, bounding the RSA modulus. Selectors exclude the key bytes and
duplicates; table and output bounds are checked.

The source popular-code encoder forces hit-rate four, overlapping a checksum
bit. Preserve that observed transform; some resulting codes fail the donor's
own checksum check. The source stage-zero shuffle leaves its last scratch byte
undefined. That byte is overwritten by RSA while encoding and is outside the
twenty decoded descriptor bytes. The implementation initializes it to zero;
the independent host reference uses zero-initialized automatic variables.
Neither detail justifies changing the donor's accepted-code behaviour.

## Prepared eligibility and selected destinations

`tools/v3_password_policy.py` compiles the pinned donor's complete eligibility,
price, item-conversion, and stock-list functions against actual disc tables in
an ignored host evaluator. Table roots, complete pointer targets, list/price
terminators, and source identities are checked. The evaluator runs under memory
and undefined-behaviour sanitizers and produces one permission mask per 16-bit
donor item. Bits 0/1/2 mean Famicom/user/other code eligibility; the latter covers
types 1, 2, 3, and 5. Permission is not a claim that an item exists in N64.

The evaluator needs no game state: the source user-rule queries all three ABC
priorities, so their ordering does not affect the union. The local and foreign
fruit prices are positive, and the year-dependent grab-bag price is unreachable
from the user eligibility path. These conditions are checked. No source RNG
branch is used by permission extraction. The full 65,536-byte matrix remains
local and is compacted into sorted inclusive ranges.

The `AFPE` version-1 packet contains a 32-byte header: magic, version, range
count, total bytes, normal/special NPC bounds, reserved-item value, five source
magazine percentages, and eleven zero reserved bytes. Each six-byte row contains
unsigned 16-bit first/last IDs, mask, and a zero reserved byte. Canonical rows
are ordered, non-overlapping, and merge adjacent identical masks. The packet
preserves the source's reserved `FFFF` permission; the destination map never
treats that sentinel as a real gift.

HomePage furniture contains five Famicom-only rewards. HomePage floor/wall use
the other-code rule. Nintendo-code birth category 34 contains Nintendo bench
and ten Mario pieces. The ten Mario furniture records have other-code
permission despite no stock-list membership and an
empty `ftr_listMario`. Source acquisition must use those actual rules, not the
name or emptiness of one list. The ordinary metadata importer still needs the
linked password-acquisition adapter before enabling these records.

The separate `AFPM` version-1 packet binds implemented imports from the checked
current composition catalogue. Its 16-byte header is magic plus six unsigned
16-bit fields: version, count, stride 12, total bytes, zero, zero. Twelve-byte
rows contain source/native unsigned 16-bit IDs, live enable-field RAM address,
field width (one or four), and three zero bytes. Furniture keeps all four
rotations. The live reader must return exactly one; disabled, malformed, or
missing records resolve to zero. The map is build-specific, not a stable saved
format. No native correspondence is inferred from equal IDs. Existing native
items and display-parent aliases still need their separately reviewed mappings.

`overlays/v3/password_policy.c` validates both packets, resolves selected
destinations through a supplied read-only accessor, and implements Nook's
result classification. Checksum/type/rate, full-name equality, NPC bounds, and
no-gift outcomes are retained. An unavailable destination does not consume RNG.
Valid magazine attempts consume one continuous `[0,100)` game roll, including
zero/hundred-percent rates; invalid/NaN/out-of-range rolls reject. The explicit
`result_gives_item` helper excludes invalid, wrong-name, card-e, losing-magazine,
and cancellation results. None of these functions awards an item or writes
saved state. Prepared callback tests do not establish engine execution. The
installed native accessor and RNG binding below still need complete native
execution; input, dialogue, and handover remain absent.

## Linked engine and memory ownership

The ordinary runtime refresh accepts `--password-runtime <prepared-policy-dir>`
with the checked base lock. It rebinds all source functions/tables and the actual
import map, verifies the retained donor matrix against its known digest, and
links the shared modules without changing their donor rules. No native item is
inferred from equal source/destination numbers. The map must be refreshed when
the ordinary importer adds supported identities; installation alone does not
permit enabling password-only acquisition metadata.

The 32-KiB packet occupies `804C0000..804C7FFF`, beyond scenery, room rigs,
scrolling materials, and the full surface packet, before furniture banks at
`80500000`. Code begins at `804C0000`; complete codec/policy/map tables begin at
offsets `2800`, `3000`, and `5000`. The last sixteen bytes are a guard. The
linker rejects code/table overlaps and mutable compiler-generated data.

The public loader entry is `804B4D00`. Its code and strings must end before the
cache word at `804B4EF0`. The existing wrapped-present map at `804B4F00` and
equipment footer at `804B4FF0` stay untouched. The equipment packet retains its
size: extending it would overwrite the separately loaded scenery owner at
`804B5000`. Startup reloads the zero cache word. The lazy loader transfers the
complete packet, verifies CRC, performs data and instruction cache operations,
and only then publishes its ready value and calls the engine. DMA/CRC failures
never call the engine. No new ordinary heap allocation is introduced.

`password_runtime.h` defines the frontend contract: one call per submitted
attempt, exactly 28 ASCII input characters, two eight-byte donor-font names,
and an output offer. Cancellation uses the source trailing-space sentinel.
Invalid/cancelled attempts leave the offer untouched. The frontend must latch
the returned classification rather than invoking it again on every frame.
The native resolver reads checked one-/four-byte live selection fields. Magazine
rolls call native `fqrand` at `8002C9AC` and multiply by 100 as the donor does.
No function in this module writes inventory, a save, or dialogue state.

The single provenance catalogue credits both resource-failure diagnostics to
the assistant. They are project diagnostics, not translated donor dialogue.
The installer binds those entries to the actual compiled strings.

## Nook integration bindings

The current cranny owner retains its full native action dispatcher. Verified
disassembly is generated from the current build lock, not an assumed retail
ROM, using `tools/disassemble.py --build-lock`. Its action/next-action/function
fields are `938`, `93C`, and `940`; its actor allocation is `96C` bytes. Do not
copy the GameCube password fields at `9D8`/`9F8` into that smaller native actor.
The request-answer action is `809CC654`; setup is `809CDFF4`; per-frame indirect
action dispatch is at `809CE0AC..809CE0BC`. Native init/update tables are at
`809CE7E0`/`809CE88C`. Other shop variants require their own checked bindings.

The native submenu opens through `800C4D8C`, with `play + 1CBC` as its submenu.
Menu completion is read at `play + 1D98`. The cranny's buy-menu wait functions
at `809CC7E8`, `809CC854`, `809CC8A0`, and `809CC8D0` show the existing message
hide, open, close, and message-return sequence. These are integration evidence,
not permission to replace purchasing or to reuse its saved item fields.

The donor request-answer flow also rejects visiting players, full pockets, and
a common gift count of three. Preserve its actual reset scope; do not assume
that count is a new daily saved field. The takeout initializer inserts exactly
one wrapped gift through `mPr_SetFreePossessionItem`, increments that count,
locks message continuation, and sets the head lock. The following frames create
the handover actor and transfer ownership. Inventory insertion by itself is not
the complete delivery, and it must not be repeated in the frame-update action.

## Required integration

1. Retain the installed source eligibility from `mMpswd_check_present`: Famicom uses
   its whitelist, user-trade codes use actual tradable stock/price rules, and
   other codes use the source birth/category exclusions and item ranges.
   HomePage lists are evidence of acquisition, not the complete allowed set.
2. Complete existing-native and display-parent correspondence alongside the
   prepared import map. Resolve donor identity to a checked native identity. Reject missing,
   unfinished, disabled, or unsupported items before showing a gift. Do not
   cast donor IDs, alias missing items, or use checkbox order as identity.
3. Connect Nook's 28-character keyboard route and cancellation. Preserve the
   two fourteen-character display fields and full eight-byte donor name
   comparisons. Normal NPC and special-NPC checks need their actual source
   bounds and mapped identities, not an arbitrary nonzero code test.
4. Preserve all source result classes. Famicom/user codes require hit-rate one
   and matching names; popular codes also require valid NPC data. Card-e codes
   produce their no-gift message; mini codes require hit-rate one. Magazine
   rates 0–4 use the source probabilities 80/60/30/0/100 and genuine game RNG.
   A valid but losing code must not award an item. Invalid rate/type values
   never index an unchecked dispatch table.
5. Obtain existing official English messages and record their exact source in
   the single translation provenance catalogue. Preserve retry/decline flow,
   item/name interpolation, message timing, and no-award outcomes.
6. Enter the native animated handover route. The donor creates the gift actor
   with `birth_proc(item, 7, 1, shop)`, waits for animation and handover ownership,
   and unlocks dialogue only after completion. A direct pocket write is not a
   substitute. Handle full pockets, aborted input, disabled selections, and
   repeat conversations without accidental duplicate awards or a dialogue loop.
7. Connect the frontend to the installed shared code/data, respecting its checked
   bounds, then run one focused native acquisition batch on the current build. Use isolated
   saves. Enable item choices only after graphics, behaviour, real delivery,
   and persistence requirements are met. Preserve translation-only output.

The linked decoder and encoder are not evidence for installed UI, native
execution, ordinary gameplay, save/restart, or hardware. Keep the current
experimental build and both deployments of the one stable patcher unchanged
until their respective integration and user-approval requirements are met.
