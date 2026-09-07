# Controller-specific English reference text

## Contract

Controller wording differs between the English GameCube release and N64 even
when the surrounding message has the same meaning and actor behaviour. Do not
import an unusable button instruction or apply global substitutions to unrelated
messages. Each approved change belongs to one hash-bound reference match.

The initial operation, `inventory_y_to_start`, replaces the complete highlighted
`Y Button` span with `START Button` at its approved encoded-byte offset. Keep the
GameCube colour, adjust only its highlighted character count from eight to twelve,
and preserve all surrounding text, manual line/page breaks, pauses, and controls.
The original N64 clothing and planting reminders explicitly use START to open
inventory. Their approvals use encoded offsets 84 and 80 respectively. The
planting reminder also retains both GameCube pixel-space commands; it requires
the resident runtime that implements that command.

An approval records the complete native-source hash, GameCube-reference hash,
encoded span offset, final adapted-text hash, and reviewed reason. Candidate
generation verifies the source and reference, requires the exact old span at the
declared offset, performs only the named operation, and still applies the normal
native actor-command and capacity checks. The ROM builder separately verifies
the final candidate hash, so a stale reference, missing button change, altered
layout, or partial adjustment cannot enter a build using that approved record.

Full GameCube text stays in ignored local extraction and candidate files. The
repository holds only original operation code and short, hash-bound approvals.
Further button operations require their own implementation and tests.

## Acceptance

Test wrong IDs, source/reference hashes, offsets, span bytes, operation names,
and final payloads. Confirm that only the approved span changes and that every
following line break, page break, and timing token remains in order. Verify native
message loading and ordinary clothing/planting/inventory gameplay before calling the
instructions complete. No controller mapping or save structure changes here.
