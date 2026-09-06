# English date and time substitutions

## Scope

The resident module replaces the seven formatter calls inside the native message
field-copy routines. Other UI and actor callers retain their native formatters
until their own destination capacities and surrounding punctuation are verified.
No RTC representation, game clock, event scheduling, or saved date changes.

| Message field | Native call | English destination | Result |
| --- | --- | --- | --- |
| Year | `8009EEA4` | Six bytes | Four decimal digits |
| Month | `8009EF2C` | Nine bytes | January through December |
| Weekday | `8009EFB4` | Nine bytes | Sunday through Saturday |
| Day | `8009F03C` | Four bytes | Ordinal day, including 11th–13th |
| Hour | `8009F0C4` | Two bytes | 1–12; midnight and noon both 12 |
| Minute | `8009F14C` | Two bytes | Two zero-padded decimal digits |
| Second | `8009F1D4` | Two bytes | Two zero-padded decimal digits |

The English GameCube implementation in the pinned CC0 reference supplies the
semantics. Calendar words and ordinals are checked against the supplied English
disc's string bank: weekdays `0009..000F`, days `064E..066C`, and months
`066D..0678`. Invalid input uses the original fallback date component: year 2000,
January, Sunday, day one, or zero hours/minutes/seconds.

The formatter writes space-padded game bytes without a C-string terminator and
returns the actual length. An insufficient destination or unknown field returns
minus one without writing. All production wrapper capacities accommodate every
valid result. The separate GameCube AM/PM insertion is implemented through the
[English command dispatcher](ENGLISH_COMMANDS.md), retaining the hour-time latch.

## Native stack safety

`mMsg_CopyMonth` at `8009EF00..8009EF87` and `mMsg_CopyWeek` at
`8009EF88..8009F00F` each reserve a 56-byte frame with an eight-byte local region
at `sp+2C`, a command-length temporary at `sp+34`, and incoming arguments at
`sp+38..40`. Each frame grows by eight bytes. The command temporary and incoming
arguments move upward; saved registers, outgoing arguments, and the local array
start stay unchanged. Nine-byte names therefore cannot overwrite the temporary.

Other wrappers fit the original local regions. The native insertion/move logic,
message control codes, manual newlines, and timing stay in place. No bank content
is reflowed or silently shortened.

## Validation

Portable C tests cover every sixteen-bit year and every byte value for other
components, ordinal exceptions, padding, undersized destinations, and surrounding
memory guards. Module insertion verifies source instructions and linked function
addresses. MIPS execution, field insertion, calendar UI, controlled RTC boundaries,
and original hardware require separate recorded evidence.
