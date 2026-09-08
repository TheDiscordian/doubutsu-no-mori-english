# Letters from departed villagers

## Installed scope and verified content

The eighteen native classic templates `00FC..010D` have complete supplied
English header/body/footer parts in catalogue two. All 54 parts match the
verified donor-bank transcoding without unsupported glyphs. The optional
`--english-departed-letters` ROM build connects complete native creation and
mode-zero queued receipt. It requires Mom integration and the creator built
with `--mother-letters --departed-letters`. The combined translation counter
checks the installed route before crediting its complete letter parts.

The native creator `mPr_GetForeingerAnimalMail` at `800B9C34..800B9DAC`
selects `00FC + personality*3 + RANDOM(3)`. Its full code SHA-256 is
`a23000c283f82ab03d9af62ab377460d27caf3539f316b7717b116ff7d6250f3`.
The corresponding supplied English function has 360 bytes and SHA-256
`e52db84f05b3eeddb0bc4fb2658a2bd9528ab4a1515db932d276d88956607ff3`.
Both use the same six personality groups and three choices per group.

| Field | Native source | Complete English source |
| --- | --- | --- |
| 0 | Player's saved name | Same six saved bytes |
| 1 | Departed NPC ID/name lookup | Full eight-byte English NPC name resolved from that ID |
| 2 | Remembered villager town | Same six saved town bytes |
| 3 | Player's saved town | Same six saved town bytes |

English headers omit the town field present in Japanese. Bodies `0100` and
`0107` also omit Japanese field zero. Preserve the complete English parts and
prune only unused captured fields; do not insert the omitted Japanese arguments
back into the translated wording. English footers still reference the full
villager name, and some also reference the remembered town.

The creator retains native sender/recipient metadata, gift zero, received font
zero, type zero, and the original selected stationery. Its original header/footer
temporaries are twenty/twenty-six bytes before ten/sixteen-byte copies. Complete
snapshot publication replaces those narrowing copies.
The main static staging letter is shared with Mom at `80144570`.

## Runtime contract

The optional `af_departed_mail_create` entry chains other requests through the
Mom dispatcher and then the ordinary NPC creator. The existing resident loader,
32-byte session, 5,344-byte workspace, and saved structures remain unchanged.
The twelve-byte descriptor occupies the existing animal argument slot:

| Offset | Value |
| --- | --- |
| 0..1 | `DM` |
| 2..9 | Copy of the native eight-byte remembered-villager record |
| 10 | Zero |
| 11 | `FD`, outside native personality range 0..5 |

The record contains a big-endian NPC ID followed by six remembered town bytes.
The player argument points to the unchanged sixteen-byte recipient identity.
Condition and visitor flags are zero, and the reply-origin pointer is null.
The descriptor is synchronous stack storage; no pointer is retained.

Output/input/resource overlap and alignment checks precede descriptor reads.
Only native villager IDs `E000..E0D7` are accepted. The source-bound existing
alias resource supplies the full English name. Four fields are captured before
selection; unused fields are pruned by the complete template formatter.

The creator clears private staging, obtains the native personality, and calls
the original floating RNG. Signed truncation of the single-precision draw times
three matches the original instruction. It retains the original temporary-field
call order and six-byte temporary NPC name independently of the full English
snapshot name. The original paper selector and sender helper set native metadata.
Only successful complete snapshot generation copies all 164 bytes to the caller
and publishes capitalization. Failed creation leaves that destination unchanged.

The optional image has no writable/BSS data. Its native relocation validator
also accepts paired `LUI`/`LWC1` references to aligned four-byte read-only floating
constants inside the image. Other unsupported instructions and escaped targets
still fail. Existing ordinary and Mom creator artifacts remain valid.

## Native entry and failure boundary

`mPr_SendForeingerAnimalMail` occupies `800B9DAC..800B9E44`, SHA-256
`56babf0ec91465d24802377cc595c1a36ece8e949c549aa586a69e9ca7b6f7de`.
Its supplied English counterpart has 156 bytes, SHA-256
`ecb310217d103a0e450730000121b1baa25e48fbb2fadb9eec9f43fafb527045`.

The 376-byte native creator is replaced in place with a 48-byte-frame wrapper
and padding. It copies the eight-byte remembered record using halfword operations,
rejecting null or odd addresses before the loads. It forwards the descriptor to
the resident loader and returns a complete destination pointer or zero.

The installed caller gate at `800B9E00..800B9E34` removes the early shared-staging
clear and checks both creation and mode-zero receipt before clearing the
remembered villager. Each failure branches to the original epilogue at `800B9E34`.
Unavailable text, failed loading, and refused receipt do not erase the record
or submit an older staged letter. Original player eligibility, queue capacity,
recipient ownership, receipt policy, and the rest of the caller remain intact.

Native personality lookup, random selection order, stationery selection, and
selected town/name identity are retained. There is no reroll within a synchronous
attempt. Failure does not roll back RNG or retain the selected template/paper
across later attempts; the remembered villager remains eligible, but a retry can
select a different letter in the same personality group. No new durable retry
state is added.

## Verification and remaining acceptance

Host tests cover all eighteen templates in both capitalization states, all 216
full villager names, complete metadata/snapshot/reconstruction, and the inherited
Mom and ordinary NPC creator contract. Invalid IDs, fields, source resources,
floating values, stationery, unavailable catalogue reads, and aliases reject
without partial publication. The same tests pass under address and undefined
behaviour sanitizers.

Installer tests verify all 54 source-bound parts, exact allowed instruction
ranges, both failure destinations, legacy variants, atomic dependency/guard
rejection, and the actual built ROM. Independent cross-builds and independent
entry/gate assembly agree. The native batch compares 36 creations with original
native metadata, temporary fields, and RNG; all eighteen delivered letters
reconstruct completely. Six rejection cases and a resource-recovery retry pass.
The [integration checkpoint](../docs/checkpoints/DEPARTED_VILLAGER_LETTERS.md)
records exact artifacts and validation evidence.

Normal scheduling, queue draining into homes, remembered-villager retention
through actual saving/reloading, human playthrough, and original hardware remain
acceptance work. Direct calls with restored fixtures do not establish these.
