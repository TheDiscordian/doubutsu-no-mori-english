# Text sources and human review

[`translations/provenance.json`](../translations/provenance.json) is the single
per-text source and authorship catalogue. Review status, contributor credits,
source corrections, and additional languages belong in that file. There is no
separately maintained list of assistant translations. This document explains the
catalogue; it does not duplicate its entries.

## Reading an entry

Each stable `id` identifies text, independently of its wording or language.
`native_sha256` binds its original Japanese record when applicable. Under
`locales.en`, `credit` identifies authorship, `source` records the existing
evidence and donor IDs/hashes, `locator` points to the editable input or builder,
and `encoded_sha256` identifies the inspected installed text. `evidence_id`
records the originating identity when an exact native/text alias is used.

- `official`: existing Nintendo English wording, with its recorded source.
- `fan`: an identified fan-translation source. Legacy agreement used only to
  match identities is not authorship and does not receive this credit.
- `assistant`: project-written English without a recorded human translation
  source. These entries include their English `text` for direct review.
- `human`: a project translation with named `contributors` on that locale.
- `original`: the installed backing record retains the original N64 contents.
  This does not assert that those contents are English or still displayed;
  complete letter resources have their own entries and identities.
- `blank`: retained empty/padding-only text.
- `unresolved`: attribution is not established. Never turn this into an
  assistant, fan, or official credit merely from similar wording.

`assistant` means no human translation source is recorded for that wording,
not proof that no suitable translation exists anywhere. Prefer the matching
official translation; otherwise seek an identified human fan translation.
Preserve real N64 people, roles, objects, and locations when matching identities.
Never substitute different GameCube staff or a different landmark just to reuse
a label. A required platform adaptation must identify its source and the
assistant/human contribution separately.

Mechanical validation is not human review. Set `human_review` to `approved`
only with a named public `reviewer`; retain contributor and source credits.
Use public names, not private personal information.

## Views of the same catalogue

From the repository root:

```sh
python3 tools/text_provenance.py --author assistant --text
python3 tools/text_provenance.py --id string:04EA
python3 tools/text_provenance.py --author unresolved
python3 tools/text_provenance.py --check
```

These commands read the canonical file and print views; they do not create
another maintained list. Nintendo scripts and original Japanese text remain
in the user's local ROM/extractions. The recorded IDs locate them without
committing another extracted script. `build/inventory/<bank>.jsonl` supplies
the original Japanese for native IDs when local source extraction is available.

## Coverage and remaining attribution work

The catalogue binds an explicit inspection ROM; it does not choose a build by
timestamp or claim to describe every subsequent cartridge automatically.
It includes all stored native text-bank records, full item/character names,
default catchphrases, all available parts of the complete glyph-aware mail
catalogue, all appended summer dialogue/choices, imported villager/item names and
phrases, embedded editor confirmations and warning lines, control captions,
and the Shrine label. Short backing names are not
substituted for the installed full English-name route.

The catalogue's `coverage.unresolved_work` is the authoritative queue for
remaining coverage: other inline UI/bitmap text and differing
older mail-resource variants still need individual attribution entries. No
claim of complete whole-ROM provenance follows from the covered entries having
resolved credits. Add these entries to the same catalogue, not another list.
Unused/debug records stay identified rather than being silently discarded.

The seed command is a one-time migration from source-bound project records and
actual installed bytes. It refuses to overwrite the catalogue. Do not rerun it
over human edits. Candidate status alone does not prove installation: this
migration requires matching source and installed text, or an explicit checked
resource mapping. It does not run the translation-percentage tool or emulate
older builds.

## Other languages

Keep the same identity and Japanese source hash. Add another BCP-47 language
key alongside `en`, with that translation's credit, source, contributor,
edit locator, and review state. A compiled locale records its actual encoded
hash; these English hashes cannot be reused as proof for another language.
Do not copy English authorship onto a new translation. The catalogue prepares
source tracking for other languages; it does not claim that their fonts,
encoding, layout, or runtime integration are already implemented.
