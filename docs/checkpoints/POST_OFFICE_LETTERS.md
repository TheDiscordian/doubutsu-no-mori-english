# Catalogue-order and raffle-ticket checkpoint

## Installed translation

`build/post-office-letters-pilot/animal-forest-halfwidth.z64` installs all five
complete English postal templates `0049..004C/0057`, fifteen parts. Full GameCube
wording, manual breaks, article commands, and footers remain intact. Order names
come from the full sixteen-byte item resource; ticket month names reflect the
original gift's expiry month. No new date/RNG policy or saved layout is introduced.
The [specification](../../specs/POST_OFFICE_LETTERS.md) pins native/donor functions,
input fields, ownership, the descriptor, and receipt/retention semantics.

The creator's repeated overlap checks are consolidated into a read-only shared
guard. It rejects small control aliases before reading workspace fields. The
guard-only creator is 30,720 image/432 relocation bytes; the postal variant is
31,504/448 bytes. The full postal call requests 37,311 bytes including its unchanged
5,344-byte workspace and alignment. It retains 1,264 image bytes below its bound.
The resident remains exactly 24,576 linked bytes in the same 32 KiB reservation.
An Expansion Pak requirement is acceptable; this build does not require one.

## Executed verification

- All thirty host creator tests pass in 34.557 seconds, including every earlier
  dispatcher, all four shop templates and both capital states, three full item
  names, all twelve months/five ticket counts/both capitals, every catalogue-read
  fault, bad descriptor/alignment/overlap cases, and resource retry.
- The same thirty tests pass under AddressSanitizer/UndefinedBehaviorSanitizer
  in 46.586 seconds. Sanitizer execution uses the final simplified host test.
- Six installer/actual-ROM tests pass in 19.312 seconds. All fifteen supplied
  parts and their field sets are bound to both supported immutable catalogues;
  bad dependencies and every native guard reject atomically. The counter credits
  only the five installed source IDs across three banks, preserves every previous
  replacement, and keeps the source denominator unchanged.
- Thirty-five reader, record, loader, generation, and counting regressions pass
  in 4.164 seconds. No full-project regression claim is made: historical compiled
  creator manifests need regeneration after the shared source change.
- Three native-scenario tests pass in 5.797 seconds. The scenario retains every
  shop/capital pair and every ticket month/count, full expected fields, a single
  restored checkpoint, exact original cache helpers, and no screenshot actions.
- Independent Docker creator builds agree for image, relocation, and manifest.
  Independent assembly reproduces the complete 128-byte wrapper and both 28-byte
  gates. The original pending-order/ticket loops and native receipt remain intact.
- Compared with `build/mail-shared-guards-pilot`, only native code, the configured
  resident blob, creator blob, and DMA table change. Only two DMA words change:
  creator end and the following unchanged font blob's physical address. All
  13,393 ordinary edits, 2,783 wider item slots, previous letters, fonts, and other
  resources are retained. The original-ROM UPS reconstruction passes.

The native run `build/smoke-post-office-01` passes all 68 original-metadata
comparisons, complete creations, real sub-helper receipts, and full readbacks.
All ten pending-order/ticket loop cases pass: complete delivery, disabled-resource
retention/retry, full mailboxes, partial delivery, and absent players. Five invalid
template/gift cases preserve destination and capitalization. All 364 calls,
615 assertions, restored heap/global/save state, fixture and stack guards,
checkpoint reload/post-restore assertion, and graceful shutdown pass. FlashRAM
stays erased and the Pak retains its blank fixture. The run is silent, has no
screenshots, and requires no Expansion Pak. The 1,225-record log is completed,
not a partial or timed-out result. Native postal creation uses cartridge-loaded
code; only the 128 original comparison instructions are debugger-uploaded.
These injected native calls do not establish normal scheduling, save/reload,
editorial/presentation review, or original hardware acceptance.
The independent result audit passes in 2.645 seconds, binding the completed log
to the actual ROM, regenerated case inventory, all calls/stack returns, exact
save-file hashes, and the post-checkpoint assertion. The final three postal-only
host contracts also pass in 3.784 seconds after the test simplification.

The preceding guard checkpoint also passes 53 final host contracts and 27
sanitizer contracts, with independent builds. The new postal tests include those
dispatcher contracts rather than treating the old artifacts as current-source
approvals. The current HRA scheduler failure remains in the later combined bug
pass; completed old template groups are not rerun in this postal native batch.

## Artifact identities

| Artifact | SHA-256 |
| --- | --- |
| Complete ROM | `44d3ecea7bf4688eb35afe66c918b4bf10fd5ee6be3ce577b2221d1969947ff8` |
| UPS | `36133eaf41325777e61b78401b0b0b3f1c0b7efad1cfffb3c2efbcb74e0cd2ff` |
| Creator image | `4ba189f23c4c2333aa2b9c8d0aa08448e80c2dea52424a0d2217b743251ecac6` |
| Creator relocation | `019ea87f345781a9817c2f5854d7db6e90f2e05913d7a36aa280efd96fa1ace3` |
| Host tests | `5b294546ca966820d004da16d21ac3b8bcec85d468ef988d9f9d6a1732a5d76a` |
| Sanitizer tests | `4b4ec80b458a69a3384017ab6f04df6b0747e708c7821540e06cfd04f1e25770` |
| Installer tests | `d647e7d5aed8caeb83001f66e192da28b6cc0bff3508922bc1dd55904bc00a22` |
| Assembly report | `76f3f0d57297f267703dfa0cfcc5d211a873ff89e52e25fd0d44d61b4e74f594` |
| Native scenario | `03d957a108eaf69fae84d20220b18fc9eea6a42c83f955682e660a10c15fae54` |
| Native results | `0fb0275f9c52a9abc2f61b1258e103d8b3d6ce7950f29c831123c5c608084798` |
| Restored native checkpoint | `1cabba6691206d22d6db8c56917ba7f2a35be9269c035edc55364ba59ec3a874` |
| Reader/loader regressions | `296a0a4ceddaeafaae47abdfd2c476475a59fcba36d0945541de7f03ea636280` |
| Scenario tests | `2350d177c040417f08a753f982c6100ce04928c999dd9bc4f99db304b446815c` |
| Final three postal contracts | `21ffb2419b1280c159ad7bbe1f4cf6a8adbf1d0402049747f3d070a66824a77f` |
| Native result audit | `e990f729e85ed3120cff856cf07dd0e541f89fae3db53763ba29c6b8b68cd9ac` |
| Native helper source | `2b2138a1232412195075a6839c15446d16c8aaf3100e37494f98d3dae4a2dc44` |
| Native scenario source | `65c2f7d9700d6bede4499b16e455e26f8634434191fa84621951e00b251a643e` |

## Reproduction and continuation

Build `tools/build_npc_mail_capture.py` with `--mother-letters`,
`--departed-letters`, `--villager-events`, `--academy-letters`, `--academy-scores`,
`--mail-glyphs`, and `--post-office`, outputting `build/post-office-creator`.
Use the [floor/wall full-build recipe](FLOOR_WALL_NAMES.md), selecting that creator,
adding `--english-post-office-letters`, and outputting
`build/post-office-letters-pilot`. All earlier English options remain enabled.

Generate `tools/post_office_scenario.py --output build/post-office-scenario.json
--boot-output build/post-office-boot.json`. The silent emulator runner uses
the postal ROM, this boot scenario, the postal post-scenario, a fresh isolated
output, the existing Xvfb binary, and `--no-initial-screenshot`.

Continue with the 27 museum letters identified in the completion queue, then
other letter consumers, remaining names,
wider destinations, general text, and diagnostic scripts. Complete review,
save/travel/gameplay and available hardware acceptance, patch-only release
preparation, title-first English artwork, and the GameCube-style keyboard.
Current four-MiB bounds remain real until an explicit validated change; the
user permits an Expansion Pak requirement. The full project goal remains active.
