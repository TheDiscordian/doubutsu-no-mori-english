# V2 keyboard playtest corrections

## Findings and scope

The user likes the N64-inspired keyboard's overall appearance. The first
hardware test requests directional stick tilt, a small leftward shift of the
Cursor label and a larger shift of its C-button cluster, consistently centred
key glyphs (including `1` and `0`), and leftward A/L/R lettering corrections.
The follow-up also requests visible held/released feedback on the button art.

Implementation is complete in `build/v2-keyboard-06`. Preserve the controls, sounds, complete editor
prefix, save formats, accepted V1 results, and previous private artifacts.
No public release is authorised.

## Cause of key alignment drift

The keycaps use RDP screen rectangles; their letters use the native font's
polygon projection. The submenu builds its orthographic matrix with horizontal
bounds ±2560. Converting its horizontal coefficient to 16.16 truncates 25.6 to
25, shrinking polygon X coordinates by 125/128 about screen X=160. Therefore
left-side glyphs drift right and right-side glyphs drift left, even with correct
individual ink-centred origins. This matches the reported `1` and `0` examples.

Local references: `upstream/af/src/overlays/submenu/submenu_ovl/m_submenu_ovl.c`
(`mSM_setup_view`), `upstream/af/lib/ultralib/src/gu/mtxutil.c` (`guMtxF2L`),
and `overlays/font_edges/draw.c` (font vertices in sixteenths of a pixel).

The keyboard-only text wrapper reverses that horizontal shrink for both X
positions and X scale. Global font pixels, per-character optical origins,
vertical placement, speech rendering, and editor character advances stay intact.

## Verification

- ROM: `build/v2-keyboard-06/Animal Forest English V2 Development.z64`.
- ROM SHA-256: `259543536db43733d4a73ede05949ba52b1ce4ac3c557fc1c8e97b205856ad12`.
- UPS SHA-256: `a68e330138fafda0b0a6f09ccaec9c3fc8ca1dfa3b8b44ff65930bededb88aa8`.
- Receipt SHA-256: `aad39c5fe11e4fda802ecfb266f3aa92fca2197dcd80f130f051054c2812162f`.
- Editor SHA-256: `74a81fd14005a48ab2a16a6f560aae48aee868066c76a57393352f1240ddd3ff`.
- Relocation SHA-256: `7890a5c797402f2ec7ac06df7f50eb1eccc3b3b6902089fa1c352be325eecda1`.

Six focused checks pass in 2.952 seconds: complete UPS reconstruction, all
unrelated resource retention, retained input/editor prefix at two relocation
bases, native artwork/font metrics, allocation bounds, compiled icon bindings,
and sanitised execution of the actual directional/projection helpers.
The editor is 38,432 bytes, using all 8,192 rounded suffix bytes. No pool growth.

`build/v2-feedback-native-01` reaches ordinary name entry using normal inputs.
Its captures cover eight native stick poses, D-pad-left, return to neutral,
upper/lowercase and symbols, and held A/B/L/R/Z and four C directions. The
screenshot skill guides close inspection of the isolated display: key text is
centred across the width, pressed artwork and lowered lettering are visible,
and the stick uses the correct pose/mirror. A read-only pixel estimate of the
ten displayed digit centres is within half a native pixel of the bubble
centres; this is screenshot evidence, not a universal optical-centre guarantee.

That sequence stops at an incorrect fixture assumption: after C-right pads
the blank field to six spaces and C-left returns the caret to zero, Backspace
cannot reduce the length from the beginning. The recorded state is cursor 0,
length 6, six ordinary spaces. This is not a ROM crash or a new editing defect.
The fixture now restores its own neutral checkpoint before the final Start
capture. The completed capture prefix is not repeated.

`build/v2-feedback-native-02` resumes that identical-ROM checkpoint, captures
Start held on the blank name and the released state, and passes eight-MiB,
resident-guard, and native-fault assertions, followed by graceful shutdown.
It records ten result entries. No user save is accessed or modified.

- First results SHA-256: `ca6286028b57ff79b43217906770b0ec81781d831bcfe6f8c6803ef0e306bb97`.
- Final results SHA-256: `d91f5e4ac861433742e7ca4c90bbe6abcc158174288fe65fb1d98aedb226a61b`.

## Handoff and limits

V1 Final and the preceding V2 save formats remain unchanged. Forward and
backward compatibility are expected without migration; cross-version loading
is not newly executed. Expansion Pak, 128-KiB FlashRAM, and RTC remain required.
Existing artifacts and saves stay intact. The private ZIP still targets
`v2-keyboard-05`; the current ROM and adjacent UPS contain these corrections.

Hardware acceptance of these specific fixes and other keyboard callers remain
playtest work. No exhaustive keyboard matrix, old-build replay, or unrelated
save testing is run. The next authorised task is the private trailer.
