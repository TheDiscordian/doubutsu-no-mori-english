# Full names in player capture and dig messages

The player actor uses three ten-byte name/load/set sequences for special insect
capture text (`808CD040`), special fish capture text (`808CF9A0`), and dug-up item
text (`808D309C`). These sequences populate main-message item field zero. Their
surrounding functions obtain the actual main-window singleton through
`8009D1F0`; the replacement does not reinterpret an unrelated window.

Each sequence retains its original unsigned item expression: the insect actor
halfword at `a2+021C`, the fish callback's low sixteen return bits, or the player
halfword at `t6+0D1C`. It passes that ID and slot zero to a complete-name bridge.
No widened name is written into the original stack temporary. The seven-word
replacement fits each original load/set sequence. All other actor bytes,
branch destinations, messages, pauses, colours, and animations remain unchanged.

## Bridge ownership

The existing runtime redirects native `800BB6A0` unconditionally to the resident
quest item setter. Its seventy-two-byte tail `800BB6A8..800BB6F0` is inactive.
The new bridge occupies that exact span, keeping the original eight-byte entry
jump and delay slot intact. The installer checks both that live jump and the
complete original tail before reusing it. A native reference scan rejects any
external entry into the tail and any entry into the three player sequence
interiors. The original wrapper's own internal branch belongs to its bypassed
body, not an external caller.

The bridge is the same independently assembled zero-safe helper used by
[shop names](SHOP_ITEM_NAMES.md): a valid nonzero item loads all sixteen bytes
through the resident API, while item zero clears the whole field. It preserves
the caller's stack and return address. It adds no allocation, saved field, or
resident-module byte. Instructions are included in the ordinary ROM main-code
load, not written into live code by a new runtime installer.

The complete original player actor and relocation are hash-bound. None of the
three patched spans contains a relocation; all other relocation operations and
actor dimensions remain unchanged. Independent Docker assembly checks the
three call sequences; the existing helper assembly checks the shared bridge.
Final verification reconstructs the actor and bridge and checks installed module,
item resource, setter, and reader dependencies. It rejects missing or changed
application evidence.

## Verification scope

Focused checks cover source argument expressions, zero/ordinary item routing,
no partial installation, inactive-tail ownership, relocation at two bases,
retained complete ROM resources and virtual file sizes, and UPS reconstruction.
The combined counter verifies the new callers but retains pending status for
names with other unconnected consumers. It does not duplicate original text IDs.

Representative insect capture, fish capture, and digging belong in the combined
v0 smoke with shops, menus, letters, and save/restart. Host argument and artifact
checks are not native gameplay or original-hardware certification. See the
[checkpoint](../docs/checkpoints/TEXT_NAME_CONSUMERS.md).
