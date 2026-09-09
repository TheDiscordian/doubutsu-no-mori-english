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

## Complete creator and delivery integration

`shop_notice_creator.c` dispatches an `AFSN` descriptor through the shared
creator. It retains all nine complete catalogue parts, captures full sixteen-byte
item field seven only where the original template uses it, and publishes a
complete 164-byte snapshot only after formatter/reader agreement. The descriptor
contains the template and selected item as big-endian halfwords, paper 55,
recipient flag zero/one, a reserved zero byte, and marker `F7`. Flag zero retains
the original cleared leaflet identity; flag one copies the supplied player.
Sender, gift zero, font zero, type two, and paper 55 retain native meanings.
Failures preserve destination, input identities, and capitalization.

`shop_notice_entry.s` replaces only the two original delivery functions, within
their original 472-byte and 504-byte slots. The 448-byte rare-item selection
caller and both native tables remain unchanged. The spotlight wrapper keeps
native home/working checks, original template selection, saved-leaflet mode one,
and direct home publication. The complete creator replaces the ten-byte clamp.
The wrapper's stack is 304 bytes; reopening retains a 288-byte stack.

Reopening prepares one complete no-field letter before any home copy, then
uses the original home mapping, capacity/owner/working exclusions, and identity
copy. All three templates preserve capitalization across repeated copies.
Failed preparation returns before any delivery or notification-bit clear.
After successful preparation, original all-full/all-absent/all-working policy
still clears the pending bit. No partial catalogue reads remain inside the
publication loop, so a failed read cannot produce some letters and later
duplicate them on retry.

The spotlight selector has no durable retry receipt contract. A failed creator
leaves the saved leaflet and home mailboxes untouched, but that alone does not
prove eventual delivery of the selected notice. Source-approved scheduling and
resource-failure recovery beyond that call remain acceptance work; do not claim
a new persistent retry mechanism.

The shared creator is 33,008 image bytes plus 480 relocation bytes. Its checked
image limit is 65,536 in C, Python, and every linker script. It requests 38,847
temporary heap bytes including work/alignment, with no saved-layout change.
The resident image still uses 24,576 linked bytes and a 32,768-byte reservation.
Only the maximum-image instruction changes; exports and bootstrap are unchanged.
Expansion Pak permission does not itself change the implemented four-MiB bounds.

Build the creator with `--shop-notices` after all preceding dispatchers. Build
both owners using `tools/build_shop_notice_owners.py` and install with
`tools/build.py --english-shop-notices <owners-directory>`. Every dependency,
source approval, native function/table, and compiled image must validate before
installation. The combined counter credits all 27 parts only through the
verified installed route. The [checkpoint](../docs/checkpoints/SHOP_NOTICE_LETTERS.md)
records the complete build recipe, actual artifacts, and test evidence.

## Acceptance queue

Acceptance covers all nine complete texts, both capitalization states, every
shop/type combination, full sixteen-byte item fields, both publication modes,
home eligibility and capacity, failed-preparation retention, notification-bit
handling, restored save/global/heap/checkpoint state, and unchanged earlier
translations. Normal scheduling, save/reload, presentation review, and hardware
remain explicit validation work.
