# Exact saved-name recovery for NPC reply capture

## Scope

Foreign reply metadata stores a six-byte sender name but no independently
verified complete actor ID. `tools/npc_mail_names.py` prepares a bounded exact-key
mapping to complete English display names for the 216 native villagers.
The original ROM is hash-verified, and the complete eight-byte display-name
resource is pinned by its full hash and reconstructed from its source-bound edits.

The map accepts two known saved-name forms: the original complete Japanese
six-byte field, and a complete English name only when that English name fits the
native six-byte field. The latter is space-padded to six bytes, not truncated.
There are 394 distinct keys, and every key identifies exactly one villager.
Long English prefixes are never added as keys. Names and saved identities are
not rewritten by this preparation.

This resource remains local and uninstalled. It provides a verified source for
generation-time capture, not a reader that regenerates names in existing letters.
The capture must store the full resolved literal name. Existing snapshot wording
must remain unchanged if reference name resources change later.

## Exact lookup and failure policy

`lookup` accepts an already validated sorted alias tuple and exactly six input
bytes. It returns the villager index and a literal eight-byte `Field` with article
zero. Complete English names and their padding match the existing display-name
resource. It does not trim or case-fold the key, perform prefix matching, query
current town residents, or infer a name from personality alone.

An unknown six-byte key returns no identity. Invalid input width is rejected.
The generation caller must treat an unresolved required name as failed capture;
it must not substitute an unrelated current NPC, retain an earlier captured name,
or claim that an unknown shortened name is complete. Modified or foreign-hack
save formats need separate compatibility evidence.

## Canonical resource

The current map occupies 6,368 bytes: a 64-byte header and 394 sorted sixteen-byte
rows. All integer fields are big endian. No cartridge VROM is assigned yet.

The header's eight words are magic `AFNA`, version one, row count, row width
sixteen, header width 64, villager count 216, key width six, and output width eight.
The remaining 32 header bytes hold the complete payload's SHA-256. A reader also
requires the separately verified complete-resource hash, not just this embedded
digest.

Each row contains the six-byte exact key, a two-byte villager index, and the
complete eight-byte display name. Keys are unique and strictly sorted. All
villager indices are in range and represented; multiple keys for one villager
must agree on the full name. Display values use only supported Latin glyphs.
Command bytes and extended-glyph prefixes are rejected in keys. Preparation
rejects ambiguous same-language or cross-language keys instead of choosing one.

## Verification and remaining integration

Six tests cover every original key and every fitting English key, full output,
canonical round trips, unknown values, case changes, long prefixes, duplicate
and cross-language collisions, ordering, complete identity coverage, malformed
names, resource changes, altered source edits, and a modified display-name blob
with a recalculated manifest hash.

The [scoped capture consumer](NPC_MAIL_CAPTURE.md) validates the complete resource
and resolves full names during isolated native local/visitor reply creation.
Its host tests cover all 394 aliases, and native tests cover complete-name lookup,
unknown-key rejection, and real creator-selected names. Cartridge loading,
whole-creator ownership, and unresolved-name failure propagation through actual
delivery remain. The resource does not establish normal travel or old-save
compatibility.
