# Complete shop and Redd leaflet creation

## Implemented scope

`overlays/mail_generation/leaflet.c` creates complete received-letter snapshots
for 22 native-selected classic templates. It is a reusable creation transaction;
the optional [renewal adapter](RENEWAL_LETTERS.md) connects it to home mailbox
publication. Sale/Redd native registration remains to be connected. The optional
[date patch](LEAFLET_DATES.md) is installed separately.

`tools/leaflet_letters.py` binds all 66 header/body/footer parts to the verified
native ROM, supplied English executable/banks, and unchanged immutable catalogue
two. It checks complete encoded payloads and exact native/English field sets.
Native source tables and English selector/metadata functions establish which
template belongs to each operation; numerical ID equality alone is insufficient.

| Templates | Native selection | Captured English fields | Received metadata |
| --- | --- | --- | --- |
| `0018..001A` | Renewal table `{18,19,1A,1A}` indexed by native shop level | Month 0, ordinal day 1, year 2 | Status 0, type 2, paper 55 |
| `0002..0011` | Four shop levels by furniture/carpet/wallpaper/clothing category | Month 17, ordinal day 18, full time 19; count 0 where referenced; complete item 7 for `0002` | Status 0, type 2, paper 55 |
| `0031..0033` | Original three-way Redd draw | Month 0, ordinal day 1, full time 2 | Status 0, type 3, paper 54 |

Each template's full GameCube wording, literal spaces, newlines, article commands,
header marker, footer, and capitalization order remain intact. Several English
sale templates omit a count present in Japanese; the selected English text is
not modified to reinsert it. Fields unused by the complete selected template
are pruned only from saved capture, not deleted from its text.

## Date meaning and source ownership

The input is a fourteen-byte `AfLeafletChoice`: selected template, year,
month/day/hour/count, and three selected native item IDs. Renewal supplies the
original planned reopening date; sale/Redd supply the original start timestamp.
The creator does not draw random values, edit native handbill tables, change a
clock/schedule, or rewrite the supplied selection.

All supplied English renewal templates describe the closed day. Native `001A`
instead describes reopening day, and the original N64 caller subtracts one day
only for shop levels below two. The English GC caller unconditionally copies the
planned date and subtracts one day. Its binary prefix has the unconditional
one-day argument before the recipient loop. The English creator therefore
subtracts one day for every renewal template, using only local values. Native
scheduling must retain its original branches and notification lead time.
Passing the native already-formatted date would subtract twice for early shops;
the adapter must pass the original planned reopening date instead.

Calendar validation accepts real Gregorian dates within 1901–2099. Renewal on
1 January 1901 is rejected because its previous day cannot be represented by the
supported English year formatter. Invalid dates are rejected, not silently
substituted with an incorrect event announcement. Month/day fields retain the
complete nine/four-byte GC padded forms; year uses four digits and time uses
the complete six/seven-byte AM/PM result.

Sales require one to three items, bounded by the selected shop's native maximum.
Each item comes with a twenty-byte `AfLeafletItem`: its same selected native ID
and a complete sixteen-byte name plus article. Unused IDs must be zero. The API
rejects mismatched identities, short/truncated fields, invalid articles, and
command/extended-glyph prefixes. The adapter must resolve names from the approved
complete resource before the native ten-byte clamp; this API cannot prove that
an arbitrary supplied string belongs to a numeric item ID.

## Transaction and native code

The caller supplies a prepared 164-byte letter, immutable choice/item inputs,
separate capitalization word, and sixteen-byte-aligned 5,280-byte workspace.
Work, letter, and capitalization outputs cannot overlap inputs or one another.
All selected fields and all complete template parts pass packing and independent
resident cartridge restoration before any destination writes. Publication changes
only the received metadata, split marker `80`, and complete 122-byte envelope.
Identities, attachments, and all other original metadata remain. Rejection retains
the complete letter and capitalization state; work is disposable scratch.

`build_mail_generation.py --leaflets` compiles a distinct 3,100-byte probe using
the pinned Docker toolchain. It has no mutable/global data, data relocations, or
unresolved symbols. Six imports are bounded resident functions: snapshot packing,
restoration, catalogue-header validation, and month/day/year formatting. All
internal absolute jumps are inventoried and independently relocated. The full
hour formatter is included as original local code. Reported frames are 104 bytes
for leaflet creation and 216 for generic generation before nested reader calls.
There is no resident-module or saved-structure growth.

## Actual owner boundaries still requiring installation

Renewal publication and its notification failure gate are installed by the
[renewal adapter](RENEWAL_LETTERS.md). The addresses below also define its
original source contract. Event-manager publication remains uninstalled.

Renewal ownership metadata is at `801011B0`; its native file/relocation rows are
`0084D180`/`0084E000`, linked range `809583B0..80959230`, profile `80959040`.
`809583B0..809585F4` prepares and copies a separate letter for each eligible home.
The intended adapter creates one complete base letter before any home copy,
then uses the original recipient eligibility, identity, and mailbox operations.
This avoids publishing some recipients and failing generation for others.
Its caller at `809586A8` currently ignores failure and clears the notification
bit at `80135C12`. That clear must depend on successful complete preparation;
otherwise a failed allocation would permanently lose the notice. The original
no-notice/full-mailbox/working-player behaviour needs explicit comparison.

Event-manager ownership is at `80101310`; file/relocations are
`00850680`/`00857100`, linked range `8095B8B0..80962460`, profile `809622EC`.
`8095B9CC..8095BA60` clears its static letter at `80962330`, performs classic
loading, sets metadata, and calls receipt at `8095BA48`. Sale initialization at
`8095BDE8..8095C09C` and Redd initialization at `8095C09C..8095C264` return one
unconditionally after their registration calls. The Redd selector at
`8095BBFC..8095BC60` draws its template before preparation. Failures must not
reroll stock or the chosen Redd template, erase a previous pending notice, or
report successful publication.

Native receipt `800B6A3C..800B6AC8`, mode two, synchronously copies all 164 bytes
to saved event leaflet `801361E4` and clears only flags at `8013628A`. Its source
remains intact; this path is separate from the five-slot ordinary mail queue.
Its complete original hash is
`032319ed0866342abee88c99f07298dfe958ad6e3fb83fae8e20da2b70b2ae70`.
Native copies preserve opaque snapshot bytes, but ordinary delivery remains a
separate validation requirement. No save-format extension is approved here for
uncompleted pending generation.

Appending code must preserve original relocation/DMA-row ownership, profile
addresses, and the verified [date patch](LEAFLET_DATES.md). Check the actual
general-actor allocator before choosing expanded loaded bounds; the fortune
NPC's pool limit is not evidence for these different actors. Prefer zero new
resident-module code. Any temporary allocation must be freed on every completed
synchronous path and cannot outlive its owner without explicit durable handling.

## Executed evidence and limits

Seven focused tests pass. Complete output is compared with an independent
in-place GC formatting model for every template, all months, both capitalization
states, sale counts, and every month boundary in 1901–2099. Source/binary mutation,
every cartridge-read failure, disabled catalogue, invalid choices, aliasing,
padding, source retention, and output guards are checked. Six generic probe and
ten fortune-source/creator regression tests also pass.

The native batch passes 77 complete creation/readback cases, six rejected input
combinations, disabled-catalogue retention, 165 calls, and 1,418 memory assertions.
Whole source inputs, RNG, handbill table, live save, heap accounting, guards,
checkpoint restoration, blank saves, and graceful shutdown pass. Native item
values are explicit synthetic sixteen-byte inputs, not evidence of native item
lookup. The lower year boundary is covered exhaustively by host tests; the
native non-sale rejection fixture also supplies an invalid non-null item pointer
and does not isolate that date boundary. No ordinary actor or delivery hook is
installed by the probe. See [the work record](../docs/checkpoints/LEAFLET_LETTERS.md).
