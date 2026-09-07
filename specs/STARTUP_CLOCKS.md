# Opening clock greetings

## Content and native context

The six opening greetings `13F2/141A/1442/146A/1492/14BA` use individually
approved complete GameCube references. Each retains the greeting, speaker
catchphrase, current town, year/month/day/hour/minute, and its native successor:
`13F4/141C/1444/146C/1494/14BC`, respectively. The native source already supplies
all these fields. No standing-resident actor or expression permission is used.

Each English reference also contains storage-location field `28`, highlighted
with `50:198CDC:08` or `50:198CDC:06`, and usually a possessive suffix. The native
message has no storage location to insert. Remove precisely that device clause
and its highlight, retaining the word `in`. Do not invent a card name or replace
the current town with a storage field.

All surrounding GameCube words, spaces, punctuation, manual line breaks,
page transitions, button waits, pauses, and next-message links remain exact.
Where the device name ended a line, the shortened line still ends after `in`.
This deliberate preservation leaves line-balance changes for the presentation
polish pass. The GameCube calendar order and AM/PM remain, including the greeting
that places the clock before the date. No automatic reflow is performed.

## Exact adaptation permission

The complete-reference approval adds `omit_startup_storage_location: true`.
This flag is valid only for the six same-ID greetings and exactly one explicit
span. `tools/reference_content.py` fixes every allowed full before/after clause;
the versioned approval also binds its decoded character offset, complete native
source, complete reference, and complete final encoded output by hash.

Verification requires all seven native catchphrase/town/calendar/clock fields,
no native storage field, and exactly one storage field in the reference.
Only this field may disappear from the otherwise unchanged combined command
and newline sequence. Additional wording spans, moved newlines or pauses,
changed fields, other message IDs, cross-ID references, non-boolean flags, stale
inputs, and modified final payloads are rejected. The independent builder checks
the repository's complete output hash even without edit-level approval metadata.
All ordinary field-availability, control-flow, and expansion checks still apply.
The sixty-four existing wording-only approvals retain their stronger unchanged
non-colour-control and newline rule.

## Runtime requirements

The existing complete resident clock runtime provides English month/date/time
formatting and `76` AM/PM insertion. The hour field precedes AM/PM in each message
and latches its meridiem in the same window. The separate ordinary-dialogue lunar
date preparation patch is not a requirement of these RTC greetings.

Basic reference generation withholds all six messages because the resident
command is unavailable. Original-draft selection also checks actual extension
tokens against the shared implemented-command descriptors. It withholds drafts
requiring `62/67/72/73/75/76` when the resident module is absent, without mistaking
native command arguments or two-byte glyphs for extension opcodes. Unknown or
wrong-size extension tokens fail instead of gaining a runtime permission.
The builder separately verifies the complete installed runtime and still rejects
unsupported commands; a selection option does not bypass those checks.

## Verification and acceptance

Focused host tests check every complete retail reference and resulting payload,
native successors, all retained delivery controls and newlines, the absent
storage field, hour-before-AM/PM order, the unchanged 1,024-byte expansion bound,
basic-build rejection, and malformed or overbroad approvals. Existing wording-only
and ordinary-date tests retain their original requirements.

The full regression run passes 537 tests. The eleven-test focused run also
includes the independent-builder rejection case: all six
modified payloads and all six uninstalled-runtime attempts fail. The twelve
complete cartridge loads pass for the greetings and unchanged successors, with
38 assertions over 69 recorded steps. Adjacent/module guards, checkpoint
restoration, blank FlashRAM/Pak, silent four-MiB configuration, and graceful
shutdown pass. The only injected function is text loader `8009E558`; no saving,
selection, date insertion, or actor action is executed by this fixture.

Generated build, coverage, and test evidence stays in ignored
`build/startup-clocks-*`; completed run results and hashes belong in
`docs/WORK_LOG.md`. Cartridge-loader checks establish complete installed text,
not ordinary startup selection, live date rendering, final presentation review,
normal saving, or original-hardware acceptance. Those remain required.
