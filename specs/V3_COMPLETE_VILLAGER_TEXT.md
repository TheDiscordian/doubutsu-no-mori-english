# Complete English-donor villager text

## Installed scope

`tools/v3_all_villager_text.py` installs all twenty donor-only names, complete
default catchphrases, personality values, and source-default references in ABI 54.
The existing name, conversation, map, recipient, letter-header, and generated-mail
readers consume these records without new code or larger saved fields. All
ordinary move-in flags remain off. This text installation does not supply
islander houses, schedules, or their missing clothes.

The build verifies the original N64 image, GAFE01 revision 0 disc, both donor
archives, decoded REL, symbols, and decoder through the existing source-bound
extractors. It retains exact donor wording and punctuation, including Bliss,
Elina, Plucky's `chicky poo`, and Dobie's `ohmmm...`. It does not substitute
later-series names or phrases.

## Metadata and starting dependencies

The existing twenty 32-byte rows at `80462C00..80462E7F` hold the complete roster.
Registry version 1 maps donor indices 216–235 to native indices 218–237. Names
remain eight bytes, phrases ten bytes, and saved references four bytes.
Cheri and Punchy's complete installed rows remain unchanged.

| Villager | N64 actor | Catchphrase | Donor starting shirt |
| --- | --- | --- | --- |
| Maelle | `E0DA` | duckling | `241A` |
| O'Hare | `E0DB` | amigo | `241B` |
| Bliss | `E0DC` | hulaaaa | `241A` |
| Drift | `E0DD` | brah | `241B` |
| Bud | `E0DE` | dood | `241B` |
| Boomer | `E0DF` | human | `241B` |
| Elina | `E0E0` | shrimp | `241A` |
| Flash | `E0E1` | babe | `241B` |
| Dobie | `E0E2` | ohmmm... | `241B` |
| Flossie | `E0E3` | squeaker | `241A` |
| Annalise | `E0E4` | nipper | `241A` |
| Plucky | `E0E5` | chicky poo | `241A` |
| Faith | `E0E6` | aloha | `241A` |
| Yodel | `E0E7` | odelay | `241B` |
| Rowan | `E0E8` | mango | `241B` |
| June | `E0E9` | rainbow | `241A` |
| Cheri | `E0EA` | tralala | `2498` |
| Pigleg | `E0EB` | arrrn | `241B` |
| Ankha | `E0EC` | me meow | `241A` |
| Punchy | `E0ED` | mrmpht | `24BF` |

The donor clothing names identify `241A` as red aloha shirt and `241B` as blue
aloha shirt. All eighteen islanders retain donor growth permission 2. No row is silently
changed to ordinary-villager permission 0. Both aloha-shirt images, `241A` and
`241B`, are compared against all 256 original N64 garments, including every
pixel's converted colour. Neither matches. The text-only stage keeps their
applied outfit fields zero and refuses to write partial defaults.
The two complete pilots retain native `2498` and additive `34BF` respectively.
The [aloha outfit runtime](V3_ALOHA_OUTFITS.md) supplies the actual garments and
connects all eighteen initialisers without changing names, phrases, personality,
donor growth permission, or the disabled move-in flags.

## Complete names and saved aliases

The existing native compatibility-name reader writes exactly six bytes.
Flossie and Annalise therefore use `Flossi` and `Annali` as saved compatibility
keys; the shared display readers and generated-mail alias reader recover the
complete seven/eight-byte name. These keys are not displayed as shortened names
by the integrated readers.

Before installation, compare all twenty keys against each other, all 394 actual
installed Japanese/English mail aliases, and the original game's current saved
name records. Reject collisions rather than selecting an arbitrary identity.
The native alias table remains unchanged, including its search precedence.
Names disabled in the metadata cannot resolve through an imported alias.

Saved phrases retain `FE F3 ii 20`, with the stable native identity byte `ii`.
The original speaker and imported speakers can borrow any installed phrase
through the existing four-byte setter and full-text reader. Saved fields do
not contain truncated catchphrases.

## Saved profile and compatibility

The first 32 bytes of the existing 192-byte profile include all twenty text
dependencies. Furniture and clothing selections remain unchanged. This guards
borrowed phrases and generated names even when no imported villager lives in the
town. The profile is deliberately conservative; it is not a move-in permission.

The format-2 save codec, its allocation, and saved field widths remain unchanged.
It accepts the preceding pilot-only profile as a subset and preserves catalogue
ownership. Saves written with the expanded profile are rejected by earlier
pilot-only builds. V2 must not load imported saves. Keep backups; ordinary
cross-build save/reload is not established by the focused codec checks.

## Cartridge and evidence

Only metadata, selected villager profile bits, the ABI header, startup/configuration,
and cartridge checksums change from ABI 53. All physical resource locations,
native code, audio data/code, accessory objects/code, text-reader instructions,
ordinary heaps, and resident allocation sizes remain unchanged. The startup
remains 880 bytes and checks the full resident prefix CRC.

The [checkpoint](../docs/checkpoints/V3_COMPLETE_VILLAGER_TEXT.md) records actual
donor reconstruction, sanitized text/alias execution, profile acceptance/rejection,
and native verification limits. Both served patchers stay on V2 until the user
tests V3 and explicitly approves the switch.
