# English fallback for ambiguous borrowed catchphrases

## Translation policy

The single saved default key `D0902020` (`グー`) maps to two GameCube phrases:
Dozer (`E014`) has `zzzzzz`, and Bea (`E0C5`) has `bingo`. The four-byte native
save and propagation copies contain no donor identity. Display keeps each
original villager's exact reference. An unrelated villager holding that key
uses `zzzzzz`, the complete reference of the first native owner by ID.

This is an explicit canonical fallback, not a claim that Dozer donated a
particular copy. Every other unambiguous borrowed/default phrase keeps its
existing exact resolution. Custom English input, saved keys, reset/copy logic,
original identity, and GameCube line/page/timing commands remain unchanged.
No saved field is expanded, and no new opaque keys are introduced.

## Scoped runtime

The persistent text extension adds a display adapter around the unchanged
resident `af_get_catchphrase`. It first obtains the normal result. Only a valid
unrelated villager with the exact ambiguous saved key and unchanged Japanese
fallback may perform the canonical lookup. That lookup uses the original
bounded `af_load_catchphrase`, retaining disabled/header/lookup failure guards
and complete ten-byte output. Missing actors/animals, invalid IDs, the two
original owners, nonmatching keys, and already resolved English stay untouched.

The original `af_copy_catchphrase` calls the getter at `801953C4`, with delay
instruction `02C02025` at `801953C8`. Startup checks both words before invoking
the preceding names/choices/fields initializer. Only that JAL is redirected;
the delay instruction and resident ROM image stay unchanged. Cache maintenance
publishes the four-byte runtime change before normal game threads start.
Both main dialogue and full dynamic choices use this same insertion routine.

The new text-extension variant requires choices and identity names. Its source,
full code/resource profile, symbols, relocation, startup loader, and original
resident call must verify independently. Earlier variants remain valid with
their original sources and hashes. No unchecked mutable lookup cache is added.

## Bounded verification

Host checks cover both owners, an unrelated borrower, all nonmatching and custom
fallbacks, disabled/malformed resources, invalid/missing actors, destination and
saved-source guards, and atomic startup rejection. Compiled checks bind the
single call, import addresses, relocation, complete prior initializer chain,
resource identity, and retained previous cartridge payloads. One focused native
startup/main/choice check confirms the installed call rather than repeating all
216 default translations. Ordinary borrowing and save/restart remain part of
combined v0 gameplay; the unchanged four-byte save API remains native.
