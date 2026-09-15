# Aloha mannequin room scoring

The installed red and blue aloha displays require real clothing metadata in the
expanded HRA table. An enabled display must not retain an inactive series-63
placeholder: the evaluator can use that series as a completion-array index.

`tools/v3_aloha_scoring.py` binds the complete ABI-62 construction cartridge,
its build report, the actual installed display profiles, and the pinned donor
REL/symbols. The donor conversion's `17AC` base establishes these mannequin rows:

| Garment | Pocket | Display | Native index | Donor index | Native HRA |
| --- | --- | --- | ---: | ---: | --- |
| Red aloha | `341A` | `3868` | 1562 | 517 | `D4051000` |
| Blue aloha | `341B` | `386C` | 1563 | 518 | `D4051000` |

Both source rows are `D4050800`: OTHER series 53, group 5, clothing birth category
8. Repack the birth field for the N64 layout; retain native point weights. Both
actual donor feng shui records are neutral zero. The already-correct cherry
display remains unchanged. Exclusive status and zero donor prices remain;
scoring support does not create an ordinary shop acquisition route.

The installer changes exactly two four-byte HRA records in their existing
physical resource, also updating its shared blob backing and report hashes.
All executable code, relocations, file-directory entries, allocations, saved
profile, and format remain unchanged. Runtime ABI remains 62. The output is a
fresh ignored cartridge/UPS pair with complete reconstruction verification.

The local optional composer pins this corrected full source. Existing selection
predicates exclude disabled displays before scoring. Per-profile IDs and the
import-free V2 output remain unchanged.

The [checkpoint](../docs/checkpoints/V3_ALOHA_SCORING.md) records focused checks
and native execution of grouping and complete base-point evaluation. Ordinary
HRA mail delivery, garment acquisition, and original-hardware gameplay remain
separate work. Both served web patchers remain V2.
