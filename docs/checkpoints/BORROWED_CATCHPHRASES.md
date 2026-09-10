# Complete ambiguous borrowed-catchphrase display

## Applied build

`build/borrowed-catchphrases-pilot` retains every earlier translation payload and
adds the display-only adapter specified in
[BORROWED_CATCHPHRASES](../../specs/BORROWED_CATCHPHRASES.md). Dozer retains
`zzzzzz`, Bea retains `bingo`, and an unrelated villager with their shared native
key receives the explicit canonical `zzzzzz` fallback. This does not identify a
donor. Custom text and all saved four-byte fields remain unchanged.

- ROM: 33,554,432 bytes, SHA-256
  `e402156a7993113d4c1a8a739bdf88ba91eb2aaa949114dd3f8cbf404bb8fb5a`.
- UPS: 5,132,864 bytes, SHA-256
  `90383da0cf3b68f2140f096209b528b133887bf7290b6608ac4acd33f434c007`.
- Text-extension blob: 4,032 bytes, SHA-256
  `988be57c76de3d72435818fe27cd384a6f42366fa52fb6d28031ac0ed7851c96`.
- Startup loader: 216 bytes, SHA-256
  `4cd298af8b749b2e5773280c1f5b8a5163f5c45a9412e6b21919ea80b195e769`.

Startup allocation is 4,047 bytes, 464 more than the identity-only variant.
Resident ROM code, the existing catchphrase resource, earlier field/name/choice
sources, save layout, and actual four-MiB configuration remain unchanged.
The resident call at `801953C4` is redirected in RAM with its delay instruction
retained. Both main dialogue and full choices use that insertion routine.

## Bounded evidence

All five focused checks pass: the real-loader ASan/UBSan host check (0.265 s),
two artifact checks (0.020 s), and two cartridge checks (104.351 s). They cover
all 216 valid owner/borrower identities, complete/default/custom/invalid cases,
disabled and malformed resources, unchanged saved sources, destination guards,
atomic initialization, all prior compiled variants, exact resource policy,
retained cartridge payloads, UPS reconstruction, and combined accounting.
All twelve counter unit checks also pass. Two independent builds agree for
blob, loader, and metadata.

The first combined build rejected the new exact profile at the house-sign
dependency guard. The guard now accepts either verified complete identity
profile with its matching loader; the corrected build passes. The selected
house dependency regression also passes. No guard is disabled.

The silent native run `build/borrowed-catchphrases-native-01` passes on its first
attempt: 75 actions, ten calls, 35 assertions, and 76 result steps. It checks
actual startup, both owners and a borrower through main and choice insertion,
custom English, disabled fallback, null actor, source/destination/stack guards,
checkpoint restoration, resumed execution, and graceful shutdown. The actual
patched JAL is `0C0677FB`, targeting `8019DFEC`; the original delay remains
`02C02025`. Actual RAM reports `00400000`.

- Results SHA-256:
  `e165e4614f9a227a82324ad637f114c6cbe81a9db84a4eb1846dda5523d60da5`.
- Run metadata SHA-256:
  `68bb23c7548ae0f7816125d1747524f8843000973fe82b8ef83308047b732d77`.
- Scenario SHA-256:
  `dfbefd001b28f1d0742a2e2bc6349298ea57520347b3ea3c04a9d0039e86f6d6`.

Audio, screenshots, Expansion Pak, and test save writes are disabled. Isolated
flash remains entirely `FF`; the controller-pak file hash is
`ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51`.
Restoring
the emulator checkpoint is not normal game-save validation. Ordinary borrowing,
editor use, and save/restart remain in the combined v0 check; original hardware
and the human playthrough are not claimed.

The counter requires the installed borrowed variant before crediting complete
catchphrase resources. It retains the original 751,284-character denominator
and counts each source only once. Other untranslated records remain uncredited.

## Next work

Apply residual general/interface strings, remaining letters, accented item names,
and the required apology-symbol input. Then assemble the v0 candidate for bounded
combined gameplay/save checks and patch-only playtest handoff.
