# Official credits title and text provenance

The credit title uses the supplied GameCube release's active `string:077B`,
`Animal Crossing`. Native `string:04EA` contains the Japanese game title. The
manual `Animal Forest` draft is removed; the older unused GameCube credit group
is not the localized-title authority. Only the bound decorative prefix is
omitted. The staff heading also uses its actual donor row. Supervisor, Shigeru
Miyamoto, and Hiroshi Yamauchi retain their existing displayed wording, now
credited to matching official rows instead of marked as original translations.
Different GameCube staff do not replace the native contributors.

The data-only correction adds two bytes to the general-string bank, inside
verified unused physical padding. It changes one text record, following offset
entries, and the bank's DMA end. Every other string and executable resource
is preserved, including the accepted K.K. performance fix. UPS reconstruction
passes; no emulator replay is required for unchanged code and a fifteen-byte
title within the existing twenty-five-byte row. Nine focused credits tests pass.
Two current-cartridge correction checks, six catalogue checks, and twelve
offline-composition checks also pass. All/empty composition remains exact for
the corrected V3 and unchanged stable V2 respectively. These checks do not
claim new gameplay, hardware, or save/restart verification.

- Local V2: `build/v2-official-credits-12/Animal Forest English V2.z64`.
- V2 SHA-256: `3f0788bfc9094b0fc380d8d76bfa5f86e9852f2a5f5e44bd61d848fd35f1fa05`.
- Current V3: `build/v3-official-credits-01/animal-forest-v3-asset-loader.z64`.
- V3 SHA-256: `dfac082b4a900711aedf19b2e0cc869ee8622e1eb110e04be66591a448ea1d4e`.
- V3 report SHA-256: `4a0d360e39e68bb9da6e20b79ee107b5e559b991705f2d78d22ef5300d4aa9fa`.

The offline composer uses the corrected V3 image. Its empty selection still
returns the exact stable served V2 baseline; neither served patcher changes.
No saved field, profile, or executable code changes. V2 save compatibility is
expected without migration, not newly playtested. Imported V3 saves still need
matching/superset import profiles and must not be loaded in V2.

The single [text-source catalogue](../../translations/provenance.json) records
per-text credits, donor identities, edit locations, and human-review state.
[Its guide](../TEXT_PROVENANCE.md) explains views of assistant-authored passages
and further-language entries. Its explicit coverage queue retains remaining
UI/artwork and other unindexed resources; resolved covered records are not
misrepresented as complete whole-ROM attribution.

Resume actual camper trade selection and selected camping rewards using this
V3 image, preserving the unresolved ABI-80 caller-dispatch diagnostic. The
data-only title change does not resolve or invalidate that diagnostic.
