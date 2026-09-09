# Remaining spotlight-item and reopening letters

## Source-approved scope

`tools/audit_shop_notice_letters.py` binds nine templates and all 27 complete
supplied header/body/footer parts. It verifies native creator/owner functions,
both selection tables, corresponding GameCube functions/tables, immutable
catalogue identity, complete wording, and exact free-field sets. The source audit
does not install hooks or receive translation credit.

Spotlight-item templates `0012..0017` use table
`{12,12,13,13,15,14,17,16}` at `8010DC3C` (hexadecimal IDs). The four native shop
levels and low type bit select the same complete parts as the supplied English
table. Only `0014..0017` capture an item name in field seven; the first two
templates do not mention the selected item. Preserve the original type selection,
not an invented sale category or random draw.

Reopening-day templates `001B..001D` have no free fields. Native table
`{1D,1B,1C,1D}` at `8010DC5C` differs from the GameCube `{1B,1B,1C,1D}` in the
level-zero slot. Preserve the native selector unless reachability and text
meaning establish a required correction. Equal template IDs are supported by
the complete source functions and parts, not assumed to prove all shop behaviour
identical.

## Actual native owners

`800C0E98..800C1070` creates and publishes the spotlight letter. Its 240-byte
frame has a ten-byte item temporary at offset 228 and a 164-byte letter at
offset 60. It checks the home owner, available home slot, and working-player
eligibility, loads the item into native field seven, and sets font zero, type
two, and paper 55. The fifth argument selects mode-one saved-leaflet receipt
when zero, or direct home mailbox copy otherwise. Capture the full sixteen-byte
item before the native ten-byte clamp. Complete preparation must precede either
publication path.

`800C1070..800C1230` is the original spotlight selection caller. Its eligibility
and all four home iterations remain relevant to failure/retry design; source
approval alone does not establish retained publication after a resource failure.

`800C1230..800C1428` sends reopening-day letters to eligible home mailboxes.
It uses a 288-byte frame, a letter at offset 120, original shop-level selection,
home-to-player mapping, owner checks, free slots, and working-player exclusions.
The saved notification at `80135C12`, bit `20`, clears after the loop. Complete
preparation must succeed before this clear; do not confuse this bit with the
earlier renovation notice's bit `10` in the same byte.

## Implementation and acceptance queue

Reuse the complete immutable catalogue and full snapshot reader. The museum
creator has only 544 image bytes free, so establish a checked code/allocation
strategy for these main-code owners. A larger on-demand creator requires all
loader/build/relocation bounds to agree; Expansion Pak permission does not by
itself change runtime bounds or memory ownership. Fixed no-field templates can
use prevalidated snapshots, but the four item-bearing templates need complete
selected-name capture and safe failed-preparation handling.

Acceptance covers all nine complete texts, both capitalization states, every
shop/type combination, full sixteen-byte item fields, both publication modes,
home eligibility and capacity, failed-preparation retention, notification-bit
handling, restored save/global/heap/checkpoint state, and unchanged earlier
translations. Normal scheduling, save/reload, presentation review, and hardware
remain explicit validation work.
