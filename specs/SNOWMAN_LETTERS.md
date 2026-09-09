# Snowman gift letters

## Verified source scope

Twelve native templates `0202..020D` correspond to the twelve Snowman gifts.
The complete English catalogue has all 36 parts, with only item field zero in
each body. The existing sixteen-byte item resource contains every complete name,
including the sixteen-character wardrobe name. `tools/audit_snowman_letters.py`
binds the exact native actor, relocation, functions, gift table, supplied English
executable/functions/gift table, all name mappings, banks, decoder, parts, and
field sets. Source approval alone is not installed translation credit.

Native actor VROM `00862870`, linked RAM `8096DC30`, has 16,912 file bytes.
Its separate relocation at `00866A80` has 1,104 bytes, with sections
`(16400,208,304,0,269)`. The creator `8096E1A4..8096E274` is 208 bytes and
its allocating owner `8096E274..8096E2EC` is 120 bytes. The gift table at
`80971C88` contains `1EA4/1EA8/1EAC/1EB0/1EB4/1EB8/1EBC/1EC0/1EC4/1EC8/2619/2719`.
The GameCube table's ten furniture IDs are `1F54..1F78` in steps of four;
flooring and wallpaper IDs agree. The GameCube name table divides furniture IDs
by four; the native wider resource retains its orientation-indexed slots.

## Creation and delivery requirements

Keep native selection: one random draw selects one of twelve gifts. GameCube's
collection-aware reroll is not present in this N64 function and must not be
introduced by a text port. The current private player pointer is `80136FD8`.
Preserve paper twelve, font zero, mail type eight, native cleared sender identity,
recipient identity/type, gift, and complete supplied wording/manual breaks.
Replace the ten-byte temporary item capture with the complete sixteen-byte
resource, then pack and reconstruct before publishing the 164-byte letter.

The owner allocates 164 bytes, excludes non-local players, checks queue capacity,
clears the letter, creates it, submits native mode-zero receipt, and frees it.
It currently ignores creation/receipt failure. The snowman-combination caller
at `809712BC` invokes that owner only for the perfect-build result and continues
to register the snowman. It has no verified durable pending-letter state.
An integration must guard receipt on complete creation and explicitly establish
what retains the reward after resource/allocation/receipt failure. Do not claim
retry merely because the creator preserves its destination.

The combined museum creator has only 544 bytes under its image limit. Select
an explicit validated allocation strategy before adding this dispatcher: an
actor-owned extension can use the existing on-demand complete creator framework,
or the image bound can change together with every loader/build/relocation check.
An Expansion Pak requirement is permitted. Never loosen a size check alone or
infer eight-MiB heap ownership without the corresponding layout/bootstrap work.

## Acceptance

Complete native creation and reader comparisons must cover all twelve gifts,
both capitalization states, native RNG and metadata, exact full item fields,
wrong-gift/template/resource/overlap rejection, receipt and failed-reward
retention, actor relocation/ownership, restored live state and checkpoint, and
blank isolated saves. Normal gameplay, save/reload, and original hardware remain
explicit acceptance work. No Snowman hook is installed by this specification.
