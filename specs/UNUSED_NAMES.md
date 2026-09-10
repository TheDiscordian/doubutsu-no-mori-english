# Retained general-string names

## Text and identity scope

The 200 entries `string:009C..0163` form a retained name list, separate from the
216 live animal names and the special-character table. Their native source group
SHA-256, including each two-byte length, is
`c89c7daa27119317a730777b4b6beccf286e4bbab2e01ee1272f371142d7d41e`.
The supplied GameCube disc retains exactly the same native encoded names. Its
English character decoder produces unrelated symbols, not an English reference.

`translations/n64-unused-names.json` supplies original readable loanword spellings
and romanizations for every entry. It does not assert a correspondence to live
localized villagers. For example, the retained name `Bouquet` is not replaced
with `Rosie` merely because a live villager has the same Japanese spelling.
No live animal name, special-character identity, saved name, default phrase,
selector, or random sequence changes.

## Storage and callers

All complete English values fit thirteen bytes and the unchanged general loader's
64-byte entry limit and 80-byte aligned-DMA temporary. The data bank remains at
`02600000`, the offsets remain at `00D18000`, and all 1,562 indices remain.

The existing 34 direct-loader-call inventory is pinned. The generic getter has
one direct caller, the bounded loader at `800C3F9C`. Native default-catchphrase
selectors and all 64 special-character table rows exclude this name range.
Other known callers select date suffixes/weekdays, shop-level names, the gyroid
default, town suffix, the eleven 32-entry mail-word families, ordinary resident
word families, Resetti replies/apologies, shop counters, Katrina phrases, fortune
slips, or credits. None selects `009C..0163`. The generic number/unit helper
receives the existing date, fishing, and notice units; no selector is redirected
into the retained names.

This is a data-only translation of currently unselected records, not a new
thirteen-byte saved-name or generic caller capability. Any future use of these
records must provide enough destination storage. Do not shorten full words to
an obsolete Japanese byte length, expand every general string, or claim these
records appear in ordinary gameplay.

## Installation and verification

`tools/unused_names.py` binds the complete original cartridge, native bank,
loader/caller inventory, exact 200-entry source group, approved translation
manifest, and complete accent predecessor. It rebuilds only the general-string
data and offsets, preserving every unrelated entry and all runtime resources.
The complete cartridge is independently reconstructed from the original ROM,
so changed DMA metadata cannot hide an unrelated update.

Combined accounting first verifies the exact two-file installation and all
retained predecessor payloads, then verifies the predecessor's unchanged strict
accent profile. This grants no exception for altered accent code or resources.
The new native-bank values count once in the existing text inventory.

Focused tests cover all names, source/donor identity, complete spelling,
stale/partial/duplicate/overlong/command-bearing manifest rejection, every
unrelated bank entry, complete cartridge/resource/index retention, patch
reconstruction, and combined accounting. Reuse passing native generic-loader
evidence: there is no new runtime code or additional native harness in this batch.
Ordinary gameplay and normal save/restart belong to the assembled v0 smoke.
