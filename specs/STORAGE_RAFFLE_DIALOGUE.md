# Native storage, raffle, and offering dialogue

## Complete native messages

`translations/n64-storage-raffle.json` contains six complete original drafts.
They preserve native meanings and actions where the supplied GameCube menus or
special-actor command sequences differ. They do not replace compatible references
merely to avoid a missing English glyph.

| Message | Preserved native meaning and controls |
| --- | --- |
| `0A0B` | Stored-item question with item field `31`; Remove / Never mind... / Swap remain in original order `007E/000D/00E9`. |
| `10D9` | Excited jackpot announcement and complete first-prize item. |
| `10DA` | Stretched congratulations and complete second-prize item. |
| `10DB` | Repeated win announcement, complete third-prize item, and player name. |
| `10E1` | Four paired twin-speaker segments: welcome, raffle day, contrast, and first-floor direction. |
| `112C` | Offering question, original give/refuse labels, thank-you at `112D`, and reassurance at `112E`. |

The three prize announcements retain every native expression and pause. Their
GameCube counterparts add an actor slot-nine request and alter the native Nook
expression sequence; this work grants no new special-actor permission. Existing
native prize selection and delivery are unchanged and need normal gameplay checks.

The offering question does not rename the native shrine as the GameCube wishing
well. Its existing replies remain appropriate: thanks for giving, or reassurance
that money is unnecessary. The stored-item question retains the native three-way
choice order and does not import GameCube-only label IDs or cancellation commands.

## Twin-speaker formatting

The native raffle greeting contains four `5C/5D` pairs; the supplied English donor
has three. Retain all four native pairs and all original pauses, including the
separate contrast before the first-floor direction. Each echo retains the original
RGB `198CDC`, line-anchor command `53 01` (eight pixels), and character scale `54 1A`
(26/32). The complete English echoes are `...Welcome!`, `...day!`, `...But,`,
and `...1st floor!`. Their respective colour-span lengths are 11, 7, 7, and 13.
Apply the same native scale to every echo character, including spaces; do not
truncate an echo to match the old Japanese glyph count. Only colour-span lengths
and repeated character-scale commands change. Every other command stays exact.

The source-bound normal `reference_layout` guard handles these formatting changes;
there is no new blanket command exception, speaker policy, or font edit. The echo
message keeps an explicit-formatting warning for later rendered-layout review.

## Verification and boundaries

Require all six complete source hashes, complete native controls, exact menus and
prize ranks, both offering branches, complete echoed words/colour spans/scales,
normal buffer validation, and explicit original-draft accounting. The conservative
expanded bounds in file order are 98, 166, 146, 175, 86, and 312 bytes. All six
fit the unchanged message buffer. Only the twin-speaker message has a conservative
layout warning. These checks do not establish normal storage swaps, raffle entry,
prize delivery, offering deductions, actor reachability, or final rendering.

Native loading and connected-message tests belong to the batched content check;
runtime/formatting implementation retains its separately recorded regressions.
No resident code, choice text, saved field, or font atlas changes in this batch.

Five focused tests and all 96 reference tests pass. The silent four-MiB native
batch passes 88 steps, seventeen calls, eleven declared expected returns, and
41 memory assertions: all six drafts, connected messages `0A0A/0A0C/0A0D/112D/112E`,
and six complete menu labels. Independent execution checks confirm every call
argument, return, complete memory read, guard, single checkpoint restoration,
graceful shutdown, and blank isolated FlashRAM/Pak. All 12,538 installed payloads
and full UPS reconstruction pass; all earlier full/basic candidates are unchanged.
This is cartridge-load evidence, not ordinary service or rendered-echo validation.
