# Complete bounded choice substitutions

The shared choice formatter `80065CF8` receives a padded destination, its capacity,
and an actor. The resident English choice implementation supplies twenty-byte
destinations, including complete actor staging. The original formatter dispatches
commands in place and rescans the same position after substitution. A rejected or
unknown command can leave the prefix unchanged and prevent that loop advancing;
unbounded message helpers can also exceed the smaller choice destination.

The choice-capable persistent text extension replaces the formatter as a whole.
The existing general fields and main-message readers remain in the same startup
allocation; no separate per-choice allocation or saved-layout change is needed.
The baseline extension profile remains available and verifiable independently.

## Construction and capacity

The formatter accepts a destination capacity from zero through twenty bytes.
It stages the entire output and publishes only a complete fitting result.
Leading and internal spaces remain literal. Trailing padding is available for
substitution growth and the completed output is space-padded back to capacity.
Plain command-free choices remain unchanged, including every original space.
There is no reflow, abbreviated text, or insertion into a neighbouring row.
Padding detection walks complete tokens: the day command `7F20` remains a
two-byte command even though its argument equals the space-padding byte.

The native table supports only two-byte substitutions `1A..3F`. Complete actor
names use the existing eight-byte display resolver; default catchphrases use the
existing ten-byte resolver and unchanged saved keys. Item fields use complete
sixteen-byte resident rows, and general fields use the persistent sixteen-byte
rows. Selected-answer insertion validates its live length against twenty bytes
and reads the existing selected-answer row. Player/town names, dates, and the
native random-number command retain their original helper semantics.

Each substitution is prepared as an isolated two-byte command, without a suffix,
in a thirty-two-byte temporary. Approved native helper output is at most ten
bytes; complete resource-backed output is at most twenty bytes. Unknown or
incomplete commands, oversized results, and recursive control bytes reject the
entire update without destination writes. No partial prefix becomes visible.
Native random-number generation retains its own state effects if a later field
does not fit; the destination update alone is transactional.

## Startup and verification

The choice-capable initializer checks the original formatter prologue and all
four resident choice-layout words before calling the general-field initializer.
It then installs the formatter jump with data/instruction cache maintenance.
The builder must verify complete twenty-byte row/actor/draw integration, all
selected-name resource imports, native helper/table source, formatter references,
relocations, and exact installed image ownership.

The approved variant contains a 3,040-byte image and 208-byte relocation. Its
3,263-byte startup allocation includes fifteen alignment bytes. The loader stays
216 bytes, and the existing four-MiB heap bounds, resident module, actor adapters,
font, and saved structures are unchanged. The baseline artifact profile remains
separate. The variant accepts only the approved name/catchphrase resources and
resident imports; its native dependency comparison includes the existing English
month/weekday stack growth as well as the date-format calls.

Current translated choice-bank entries are command-free. This integration does
not enable new command-bearing imports without build-time expansion validation.
It connects the existing substitution API to complete English values; ordinary
actor and main-message names still need their remaining independent callers.
Host checks cover complete substitutions, padding, multiple fields, empty values,
invalid controls, overflow, and untouched guards. One bounded native combined
check should exercise installed choice/main-field sharing and retain a checkpoint.
