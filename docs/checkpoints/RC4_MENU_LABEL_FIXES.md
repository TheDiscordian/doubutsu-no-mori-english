# RC4 catalogue and repayment corrections

V1-21 through V1-23 have scoped corrections: catalogue Bells uses the complete
English GC image, zero-price items draw complete `Not for Sale`, and repayment
uses centred `Your Loan` and `OK`. All existing shop/service images, numeric
prices, transaction code, save readers/writers, and previous fixes are retained.
See [the specification](../../specs/RC4_MENU_LABELS.md) for exact source bindings.

## Construction and focused checks

Five focused checks pass in 9.913 seconds:

```sh
PYTHONPATH=tools:tests python3 -m unittest test_rc4_menu_labels -v
```

They independently compare complete GC currency pixels, restrict every changed
resource/range, preserve the native five-byte price buffer and paid-item path,
verify both assembled adapter routes, check new relocation records and parent
ends, verify repayment wording/length/centres, reject changed inputs, and apply
the complete UPS. The builder also checks relocation at three loaded addresses.
The added 96 bytes use 64 extra rounded pool bytes; the conservative requirement
is 271,168 of 274,560 bytes. The existing main-code pool constant is unchanged.

The first local build, `build/rc4-menu-labels-01`, stops at a source guard before
producing a cartridge: it expects the older embedded-warning pool word.
Inspection confirms RC4's later keyboard reservation uses `25CE7620`. The bound
current value and a conservative budget charging that later reservation in full
replace the stale assumption. This is a build-guard failure, not a game crash.
Its compiled adapter output is preserved separately.

The corrected development build is `build/rc4-menu-labels-02`:

- ROM SHA-256: `6ed7d636b953d24d4ad10ae8ea806deb133a752f4295ad79727c52336095dae4`.
- UPS SHA-256: `aaa8c3c35f6ea187f375906af789823235a06599cdc6ce50af4049727f037ec8`.
- Receipt SHA-256: `9d0134e10dc2392fbd1cc5fdfdfa49b41102029735ae48449879422f313f1030`.

The direct currency-image view reads Bells. This development receipt correctly
records an uncommitted worktree; the named handoff requires a committed replay
with the same cartridge/patch hashes.

## Native adapter check

`build/rc4-menu-labels-native-01` completes on its initial attempt with fifteen
recorded steps, four native calls, both requested cases, checkpoint restoration,
no faulted thread, and graceful shutdown. Audio is disabled; no screenshot or
FlashRAM/Controller Pak write operation is requested.

The test allocates 57,344 bytes through the native allocator, copies the complete
relocated candidate catalogue, and executes its actual appended adapter. A
temporary font-entry capture stub reports arguments instead of drawing pixels.
This is native CPU execution, not a native font render or ordinary catalogue entry.

- Price 12,345 retains its five numeric bytes, length, position, scales, colours,
  flags, caller buffer, and stack.
- Price zero selects all twelve bytes of `Not for Sale`, length twelve, origin
  `(48,167)`, and 0.875 scale. The original short buffer remains untouched.
- Catalogue code, capture code, owned guards, live save data, resident guard,
  and fault state pass. The original font entry is restored, the allocation is
  released, the complete checkpoint is restored, and the post-resume fault check passes.

Results SHA-256:
`0c82b25d708228b2219d27d679b81910094161cc9e7022d859e7669857c5b3fd`.
Run receipt SHA-256:
`0c0260eac0ff5daf9a5438eb50f46b1cdcd21e247d943c820e40c04d5177eb61`.
Fixture SHA-256:
`8fcdbb7f678ba558fbded85a19bfea58621016e2fc2ce91e29ec29fa2342fb8f`.
Scenario SHA-256:
`09d90cc867cf372774e4231a5982e75ca627352d2c4287e8557c089d87b5e08b`.

Do not repeat this passing adapter batch for unchanged code or describe it as
screen appearance, repayment transaction, existing-save loading, or save/restart
validation. No save migration is introduced. Ordinary hardware rechecking of
these specific labels and broader V1 acceptance remain pending.
