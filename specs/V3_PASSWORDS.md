# Shared GameCube password acquisition

## Scope

Use the donor's password route for HomePage/Mario rewards instead of placing
those items in unrelated shop stock. One codec and shared eligibility rules
serve the category; item records supply identities and selected destinations.
This does not imply that every decoded item is present in the native game.
The codec is prepared, not linked. No input UI or gift delivery is installed.

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

## Required integration

1. Derive shared source eligibility from `mMpswd_check_present`: Famicom uses
   its whitelist, user-trade codes use actual tradable stock/price rules, and
   other codes use the source birth/category exclusions and item ranges.
   HomePage lists are evidence of acquisition, not the complete allowed set.
2. Resolve donor identity to a checked native identity. Reject missing,
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
7. Link the shared code/data with checked owner/storage/relocation bounds, then
   run one focused native acquisition batch on the current build. Use isolated
   saves. Enable item choices only after graphics, behaviour, real delivery,
   and persistence requirements are met. Preserve translation-only output.

The prepared decoder and encoder are not evidence for installed UI, native
execution, ordinary gameplay, save/restart, or hardware. Keep the current
experimental build and both deployments of the one stable patcher unchanged
until their respective integration and user-approval requirements are met.
