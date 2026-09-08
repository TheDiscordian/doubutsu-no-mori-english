# Letter-style main-dialogue fragments

## Scope

The 76 native dialogue fragments in `1BFF..1C3E` and `1C53..1C5E` have empty
same-ID English main-message references. They are not empty native records.
Their corresponding native composite-letter parts provide a separately audited
route to complete English text:

| Native dialogue | Native/English mail reference | Treatment |
| --- | --- | --- |
| `1BFF..1C1E` | `maila:0020..003F` | Thirty complete references and two native originals |
| `1C1F..1C3E` | `mailb:0020..003F` | 32 complete references |
| `1C53..1C5E` | `mailc:0034..003F` | Twelve complete references |

This mapping is explicit, not a general numerical-ID or fuzzy-text rule.
The original same-bank resolver continues to reject cross-bank matches.
The separate approval file is `translations/reference_mail_fragments.json`;
it contains hashes and comparison notes, not extracted English game text.

## Native identity and fields

Sixty-six full native dialogue bodies equal the corresponding mail fragment
after removing only the final dialogue command `7F00` and outer spaces/newlines.
No internal character, space, newline, or field is discarded for this equality.
All compared fragments contain only text and the native free-string fields
`24..2D` and `36..3F`; their complete ordered native field streams must agree.
Any other command, glyph token, missing ending, or stale input is rejected.

Eight comparisons have individually reviewed native variations, with both full
native hashes bound separately:

- `1C01`: polite versus shorter equivalent greeting and a line break.
- `1C07`: an extra malformed particle following the recipient name.
- `1C22/1C29/1C2C/1C3A`: an internal space adjacent to the recipient phrase.
- `1C2E`: a manual newline before the recipient field.
- `1C33`: a missing small kana in the word for delicious and a final full stop.

The variation mode does not grant new fields or permit another donor. It must
not be used for equal bodies, and it still checks exact complete source hashes
and native field order. The caller must already supply every English field in
the original main message. A mail field number is not evidence that its value
exists in an unrelated dialogue caller.

## Complete English contract

The generator checks the complete encoded English reference hash and full legacy
agreement at the approved mail ID. The only output change is appending `7F00`.
Every English word, space, newline, and field remains; no trimming, reflow,
truncation, page addition, or other command adaptation occurs. Main-dialogue
`reference_text` validation checks the available fields and the ordinary
1,024-byte expanded-message bound. These are not native stored-letter buffers.

The builder independently loads the repository approvals and verifies both
native sources, the complete final output hash, the unchanged reference prefix
hash, English glyphs, field availability, and the required control policy. It
does not trust candidate status or provenance metadata. Changed wording, extra
commands, a different ending, or omitted provenance cannot bypass this check.
These approvals cannot overlap original overrides, ordinary reference matches,
or allocated sequences in generation. They cannot become implicit native-alias
donors; aliases would need their own complete reference audit.

All 74 reference fragments work with the basic native command table. They need
no additional runtime module, field storage, or punctuation glyph. Conservative
expansion bounds are at most 136 bytes. Width and manual-line warnings remain
visible for presentation review; they never trigger automatic reflow.

## Native originals

`translations/n64-letter-fragments.json` contains two native-complete drafts:

- `1C18` thanks the recipient and identifies the writer through native field
  `24`. The mail counterpart uses `25`, which is not available in this message.
- `1C1D` retains the greeting, home-loan question, and joking qualification.
  The qualification is absent from its mail counterpart.

Every native command and argument remains exact. These drafts need final wording
and presentation review, not a wider text or saved-record allocation.

## Review and validation boundary

Reference wording defects remain explicit polish tasks: `maila:0027` repeats
the pronoun across its first line break (`message:1C06`), and `mailb:002D`
omits the verb for needing the purchase (`message:1C2C`). Other awkward original
punctuation remains part of the complete-reference wording review. The importer
does not silently correct the reference, and these candidates are not marked
finally reviewed.

Host tests cover every approved retail mapping and complete output, strict
schema/duplicate checks, source/reference/inventory mutations, internal-spacing
comparison, field/action/glyph rejection, independent builder rejection without
provenance, and both native originals. Cartridge-loader tests compare complete
headers/text and memory guards while restoring an isolated checkpoint. A loader
check does not execute the fields, identify all normal callers, or establish
ordinary letter delivery, save behaviour, or hardware compatibility.

No stored mail-bank candidate, immutable mail catalog, mail-generation setting,
saved record, runtime code, font texture, or spacing metric is changed by this
text batch. Main-message coverage does not approve mail-template identities or
complete the separate [mail requirements](MAIL.md). Normal callers, dynamic
word/name values, final wording/layout, and hardware remain acceptance work.
Local generated artifacts and test evidence use `build/letter-fragments-*` and
`build/smoke-letter-fragments-*/`; completed results belong in `docs/WORK_LOG.md`.
