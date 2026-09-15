# Extended acquisition scoring

## Native contract

The HRA base-point evaluator at `809274F8` uses two 19-word stack arrays:
occurrence counts and weighted products. Birth category 19 would overwrite its
saved output pointer, not merely receive the wrong score. Do not enable donor
reward categories against that original counter layout.

`tools/v3_hra_birth.py` extends the actual installed evaluator to **23 categories**.
Its original loops process three entries and then groups of four; 23 retains
those termination rules. Keep all nineteen original weights, including N64's
lottery value 2,951 rather than the donor's 1,029. Append the actual donor values
for post office (19), HRA rewards (20), mayor rewards (21), and Gulliver (22):
1,111, 1,111, 1,111, and 412. This does not install those acquisition mechanisms.

The frame grows from 232 to 264 bytes. Products occupy offsets `50..AB`, counts
occupy `AC..107`, and original caller arguments begin at `108`. Validate all 28
SP-based instructions and update the 18 affected words, retaining saved `s0`,
all caller-argument offsets, both full arrays, and frame restoration. The three
native room-range/index bridges and all other control flow remain unchanged.

Retarget all five existing relocated point-table references to the appended
23-word table at `8092D424`. Preserve every relocation record; update only the
image-size header. No unrelated metadata, series masks, native wall/floor table,
mail generation, or earlier English code changes.

## Memory and installation

The HRA image grows from 31,296 to 31,392 bytes, within its 32-KiB bound. The
relocation resource stays 1,184 bytes. Four bytes before the appended table keep
the existing series-mask padding separate from live weights. The scheduler's
allocation, linked-end, and ROM-end operands all use the actual new image size.
Permanent RAM allocation is unchanged; the evaluator uses 32 extra stack bytes
and 96 extra on-demand image bytes.

Install as ABI 63 on the pinned complete aloha-corrected cartridge. Append the
revised on-demand resources to verified free backing storage, preserve all prior
object/audio positions, and recalculate the checked startup/prefix configuration
and N64 checksum. Validate complete UPS reconstruction. The saved format/profile
stays unchanged; no new item is enabled by this prerequisite adapter.

The garden integration retains this prerequisite in its ABI-64 cartridge and
offline composer. Neither served web patcher changes.

## Verification and limits

The [checkpoint](../docs/checkpoints/V3_HRA_BIRTH.md) records three focused checks
and one passing current native run. Native tests exercise all four added
categories, unchanged ordinary/clothing/lottery categories, complete products and
counters, mixed layers, the far corner, null layers, and stack/owner guards.
Synthetic metadata selects new scoring categories; this is not evidence that a
mailbox reward, catalogue order, or other new item is acquired in gameplay.

Only categories 0–22 are supported by this layout. Later donor birth categories
need explicit mapping and bounds work, including those beyond the native
five-bit field. Do not raise a metadata limit without adapting every consumer.
