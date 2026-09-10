# V1 camera, cash, and idle-clock fixes

The combined intermediate cartridge is
`build/v1-hud-label-fix-02/animal-forest-title-preview.z64`.
SHA-256: `e8635188fc182cb9f7b735a96b2c71aa1e3e72792be49f4e5d2cda2b9cc9a844`.
UPS: `48d817752c82423737e970bd5fd0dfc1494a9753124c803c0c6de65059832be9`.
It retains the corrected Press Start tiles, proportional draft editors, native
keyboard navigation feedback calls, and every preceding translation/artwork fix.
It is 32 MiB and requires an Expansion Pak; hardware rechecking is pending.

`tools/hud_label_fix.py` implements V1-04/05/11 using the
[HUD contract](../../specs/V1_PLAYTEST_FIXES.md). Only asset `00A22000` changes,
to SHA-256 `eb3717446a97c9970c9e87084ec694908789c618687f8ab639af8886880e4e01`.
The bank remains 57,136 bytes. CPU code, memory allocations, N64 control icons,
timekeeping, and save formats stay unchanged.

Four focused checks pass in 8.718 seconds: exact decoded English source pixels,
source-model/vertex/load bindings, clock order/unchanged footprint, full resource
retention, UPS reconstruction, and rejection of changed inputs. The native GBI
load is compiled in the pinned public Docker toolchain. Data-only changes do not
rerun the passing unchanged editor/loader harness. Ordinary house/shop/clock
appearance remains original-hardware playtest work.

The first build attempt stopped at a title-only symbol helper that excluded the
HUD region; no ROM was emitted. The corrected builder uses the existing complete
object-symbol parser. The second attempt and all focused checks pass.
