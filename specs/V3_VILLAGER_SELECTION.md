# V3 subset-aware town selection

## Scope

The selection adapter replaces the four native procedures that directly scan
the 216-villager personality table or use native-only selection arrays:
unseen personality counts, appearance-history reset, initial town population,
and subsequent personality-balanced move-ins. The installed build keeps all
twenty import-eligibility flags disabled until remaining native integration and
house loading are checked. Content availability is not itself permission to
put an unfinished villager into an ordinary town.

Shared personality and default/indexed initialization already use the bounded
V3 adapters. Saved appearance history is already 32 bytes at `8013670C`; no save
expansion is needed for indices through 237. Native actor-name IDs, home addresses,
personal identities, and town capacity remain unchanged.

## Memory and identities

- Selection code: `80463400..80463FFF`, after the two installed melodies and
  before the shared villager reader. The builder rejects overlap.
- Native initial-growth permissions: `80461D80..80461E5F`, an exact copy of the
  verified 224-byte `00E0D000` resource.
- Import-eligibility flags: twenty bytes at `80461E60`, indexed by fixed actor
  index minus 218. All are zero in the integration build.
- Transient candidate bits: 32 bytes at `80464700`.
- Transient shuffle array: 238 signed 32-bit entries at `80464800`.

The new transient arrays do not overwrite the original 27-byte candidate array
at `80142E58` or the original 216-entry shuffle at `80143028`. Native test indices
216/217 and unavailable imports are excluded. An imported candidate additionally
requires its exact installed metadata identity, ordinary growth role, valid
personality, and implemented starting outfit. The complete variant accepts
imported clothing only through the shared predicate that checks the actual
clothing reader. Both pilot house/default dependencies are installed, but
eligibility flags remain off. House availability is checked by
the installer before any eligibility can be enabled in a later integration step.

## Selection behaviour

Unseen counts and history reset consider every eligible native/imported identity.
Normal move-in selection retains the native personality, already-resident, and
appearance-history conditions. It forms the complete candidate bitset, consumes
one native random float, and selects that ordinal in increasing fixed-ID order.

Initial population uses the original shuffle routine and swap count. With no
imports enabled, both remain 216 and preserve the original random sequence.
When imports are enabled, transient shuffle positions after 215 map to eligible
imports in increasing fixed-ID order; those positions are never saved as IDs.
Native growth exclusions, one starter per personality, already-filled slots,
and appearance marking retain their order. The loop is bounded by its actual
shuffle capacity rather than reading beyond the array if no candidate exists.

Starting defaults use the existing checked indexed initializer. It reads each
native default through the ordinary eight-byte DMA route and uses imported
metadata for a new villager. This removes the initial selector's two temporary
whole-table allocations; the allocator-choice parameter has no remaining work.
The saved default fields and their meanings do not change.

## Native entries

The installer verifies each complete original function before replacing its
first two instructions with an external resident jump and a no-op delay slot:

| Native entry | Replacement |
| --- | --- |
| `800AA3A4` | Unseen count by personality |
| `800AA49C` | Appearance-history reset |
| `800AA51C` | Initial population |
| `800AD6D4` | Subsequent move-in candidate selection |

The remaining native sex/sound readers index the existing six personalities or
special-character records, not the extended villager roster. Personality and
default adapters guard the other direct `npc_looks_table` reads in `m_npc.c`.
These facts do not replace checking remaining data-driven native owners before
enabling ordinary imported gameplay.
