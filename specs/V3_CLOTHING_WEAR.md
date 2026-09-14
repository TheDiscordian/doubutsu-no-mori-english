# V3 player clothing animation

The player's change-clothes animation converts the requested item at actor
offset `D1C` into a texture index at its texture-change frame. The native
`2400..24FF` bounds reject an imported `34BF`, leaving index zero even though
the shared player resource loader supports `10BF`.

ABI 35 replaces the complete nine-instruction decision at
`808DC378..808DC39B` with a guarded detour. The shared query's mode 3 returns
the original native index for `24xx`, the full `10BF` index for the selected
imported shirt, and zero for invalid or unselected clothing. Name/category
decisions and furniture range/index modes retain their meanings.

The detour preserves the native `v0 = item` and `at = item < 2500` outputs,
changes only the intended clothing-index result in `a3`, and retains full-width
other registers, HI/LO, and stack. The native caller initializes `a3` to zero
before this window. Its remaining animation timing, saved-item updates,
collection call, and double-buffered resource call remain untouched.

The player code is VROM `007AC420`, linked at `808B2D50`, with its unchanged
relocations at `007D9BA0`. The complete current translated owner, 160-byte
animation function, exact replaced instructions, relocation exclusions, and
incoming control flow are checked. The continuation uses the native player
owner's loaded address at `8010DD1C`; the complete descriptor is verified.
There is no new player allocation or persistent field.

The combined clothing query/menu/wear code occupies 672 bytes at
`80463C30..80463ECF`. All original player instructions outside the 36-byte
window remain intact. Existing tag helpers are relinked within the same
reservation, and the complete tag/name composition is retained. Save format,
actual garment artwork, collection code, and player resource loaders do not
change.

The [checkpoint](../docs/checkpoints/V3_CLOTHING_WEAR.md) records focused native
index-window verification and ordinary gameplay evidence separately. A copied
instruction window is not a complete player-animation or hardware test.
