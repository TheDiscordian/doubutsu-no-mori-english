# Native development labels

## Scope and meaning

The original main bank contains 360 exact development-label records: 48 dummy
labels, 207 fixed reserve labels, ten train-demo reserve labels, and 95 numbered
reserve labels. `tools/placeholder_text.py` contains the complete recognised
wordings and their original English translations. Recognition normalises only
whitespace and fullwidth/ASCII decimal numbering. It requires the entire visible
source to match; ordinary words containing `よび`, such as calling someone over,
do not qualify. Unknown encoded data or glyphs remain separate review items.

These labels are not conversations. Translating a label does not prove that its
record is unreachable, semantically reviewed, or safe to allocate to new text.
The coverage report identifies the source category independently of candidate
presence and retains the control-flow review requirement.

## Reference fidelity and continuation protection

Fourteen recognised labels belong to complete, individually approved reference
sequences: `0486`, `0838..083E`, `0921`, `0A26`, `2AE9`, `2AEA`, `2B05`, and
`2B06`. Their complete English pages remain unchanged. The generator excludes
all registered sequence members from label fallback, including whole groups
withheld when their runtime is absent. Explicit reference identity approvals
also retain their own validation path and cannot silently become label drafts.

The other 346 records receive English labels: 55 complete valid reference labels
and 291 original label drafts. Valid reference labels and unanimous native
aliases take precedence, retaining their exact wording and layout. Approved
label alternatives include GameCube `extra` for event-announcement reserves,
`Train Demo Extra Space`, and the compact numbered form `Dummy7`.

Native `07DA`, `2AFF..2B04`, and `2B42` contain only the generic reserve label.
Their same-number GameCube records instead describe shop hours, six sleeping
signs, and connecting a Game Boy Advance to call Kapp'n. Identical record numbers
and a compatible final command do not establish these meanings in the N64 game.
All eight receive the original label translation `Reserved`. This does not add
or remove a native shop-hours, sleeping-sign, or dock interaction.

## Guarded generation and building

`native_placeholder_fallback` accepts only the verified native record and its
matching inventory hash. It runs after ordinary references and confirmed aliases,
so valid supplied English labels are not replaced needlessly. A fallback keeps
the exact native ending, either `00` or `01`, and its optional leading expression
reset `09 0000 FF`. All other command structures fail the fallback.

The 63 numbered normal/peppy conversation reserves retain that leading reset.
The nine numbered dummy records `1B42..1B4A` and trash reserves `19C3/19C4` retain
continuing end `01`; the fallback does not substitute final end `00`.
All generated labels fit the unchanged native capacity and approved font metrics
without layout warnings. Their short explicit English lines are original label
layout, not automatic reflow of GameCube dialogue.

The shared validator also runs independently in the ROM builder. A recognised
native label must become its complete English label or an independently
hash-bound approved sequence member. Exact command sequences are required for
label translations. Unrelated dialogue, changed numbering, added fields/actions,
altered endings, and unsupported visible data are rejected. Edit metadata such
as `status: reviewed` does not bypass the guard; declaring sequence policy
without a real complete approval also fails.

Fallback drafts retain original-translation provenance, their native source
hash, label kind, and an explicit non-reachability note. Generated candidate
files stay local; the catalog, guards, and tests are versioned. Reference alias
conflicts resolved by an exact label translation leave the unresolved alias
queue; no conflicting conversation donor is chosen.

## Audit and evidence

`tools/audit_placeholders.py` records every recognised source hash, label kind,
English wording, sequence allocation, candidate hash/status, and incoming
native message-script targets. It validates complete installed sequences and
ordinary label controls independently of generator counts. The full resident
candidate audit contains 346 English labels and fourteen approved continuation
members, with no missing or invalid label candidate.

No original message script targets any of the 360 labels. This scan covers only
the arguments of message-target commands `0E..15`, not executable callers,
tables, indirect flow, or normal gameplay. A separate scan for the eight
corrected slot numbers finds one instruction-immediate lead and 24 aligned data
halfword leads. These numerical matches are not established message callers;
neither their presence nor the script result proves reachability. No new
continuation allocation is made by this work.

Host checks cover the complete label catalog, all 346 unallocated translations,
exact control retention, both terminators, numbering, prefixes, capacity,
layout, unknown data, stale inventory, false-positive wording, builder rejection,
all 32 complete approved sequence payloads, and runtime exclusions. The silent
four-MiB emulator sample checks 52 complete cartridge loads across all 31 generated
label families, all eight corrections, both ends of the two numbered reset
ranges, and all eleven continuing-ending labels. Its 158 assertions cover
complete native headers/text, adjacent/module guards, and checkpoint restoration.
The 269-step run shuts down normally with blank isolated FlashRAM and Pak data.

The UPS reconstructs the built ROM from the verified original. Compared with
the resident-topic checkpoint, only main-message content, its pointer table,
and the DMA directory change. Code, font assets/metrics, resident resources,
saved structures, and all other candidate translations remain unchanged.
Normal gameplay, final wording/presentation review, and hardware acceptance
remain separate requirements. Artifact hashes and test logs are recorded in
`docs/WORK_LOG.md`.
