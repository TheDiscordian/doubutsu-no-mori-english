# English rendering and sound diagnostics

Four source-bound originals in `translations/n64-rendering-diagnostics.json`
translate message IDs `0005`, `000F`, `0010`, and `0011`. They cover alternating
music-note samples, colour/offset tests, character/line scale tests, and voiced
speech samples. These are complete translations, not replacement reserve labels.
No claim of unreachable code follows from their diagnostic content.

Keep every original command and argument in exact order: waits, clears, pauses,
colour spans, offsets, anchor types, scale values, inner-voice mode, BGM IDs,
sound IDs, voice resets, cancellation state, player-name substitutions, and
terminators. Keep all original newline and page boundaries. The numbered colour
spans remain literal length tests, including the blue label under a green test
command. Do not silently expand a tested span to colour a whole English word.

Romanise kana syllable probes and adapt elongated speech into English without
discarding notes, hearts, repetitions, or syllable pauses. Single-vowel offset
probes remain single characters. `ka/ki/ku/ke/ko` retain their complete syllables;
their halfwidth spelling has two bytes. Keep sustained-vowel note positions and
all extreme scale arguments. Those intentional diagnostics are not ordinary
dialogue that should be reflowed to remove width warnings.

The stored byte lengths are 330, 389, 835, and 584. Conservative expanded bounds
are 346, 405, 851, and 750 bytes. Each remains within the existing 1,024-byte
message buffer. No font, reader, resident code, save format, or memory bound
changes. All previously applied edits and runtime resources must remain intact.

Acceptance checks the actual Japanese source hashes, complete command streams,
line and page counts, all music-note/heart positions, the known English labels,
absence of remaining Japanese, runtime expansion budgets, candidate retention,
actual compiled ROM entries, unchanged other DMA contents, and the original-ROM
UPS round trip. The native batch loads each entire record with neighbouring
guards, then restores its checkpoint. It does not execute state-changing or
audible diagnostic commands, draw the extreme-scale examples, or claim a normal
gameplay or hardware test.

The `0004` diagnostic includes embedded letter text, multiple item/free fields,
date/name fields, random-number generation, and a player-state test. Its complete
English version uses the [guarded diagnostic sequence](MESSAGE_DIAGNOSTIC_SEQUENCE.md).
Additional page clears inside one record do not reduce the loader's expansion
bound. Do not trim its instructions or remove functional commands to make a
shorter candidate pass.
