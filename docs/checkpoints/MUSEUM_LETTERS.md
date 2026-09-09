# Museum notices and fossil letters checkpoint

## Installed translation

`build/museum-letters-pilot/animal-forest-halfwidth.z64` installs all 27 complete
museum templates: introduction `00BD`, non-fossil reply `00BE`, and fossil results
`010E..0126`. All 81 supplied English parts retain complete wording, punctuation,
manual breaks, and fossil descriptions. No free fields or new saved fields are
needed. The [specification](../../specs/MUSEUM_LETTERS.md) records native/donor
approvals, all 100 valid fossil item variants, canonical sender identity, and
the complete creator and two publication gates.

The combined creator is 32,224 image/464 relocation bytes, requesting 38,047 bytes
with its unchanged workspace and alignment. It retains 544 image bytes below
the current bound. The resident remains 24,576 linked bytes in the same 32 KiB
reservation. Four-MiB memory bounds remain enforced. The permitted Expansion Pak
requirement is not needed by this build and does not silently change memory use.

## Executed verification

- Thirty-three host creator tests pass in 41.493 seconds. They include all
  earlier dispatchers, every museum template in both capital states, all 100
  fossil variants, invalid/mismatched descriptors, overlap and alignment guards,
  every catalogue-read failure and retry, and irrelevant item-resource failure.
- The same thirty-three tests pass under AddressSanitizer and
  UndefinedBehaviorSanitizer in 56.872 seconds.
- Six installer/actual-ROM/accounting tests pass in 16.302 seconds. All 81 parts
  agree with both supported immutable catalogues. Dependencies and source/patch
  guards reject atomically. Only the three specified native ranges change.
  The complete ROM retains every earlier text/resource and the same counting
  denominator. Installed museum IDs receive credit once. UPS reconstruction
  from the original ROM passes.
- Three scenario tests pass in 11.060 seconds. Every template appears in both
  capitalization states, all 100 fossil variants produce exact field-free host
  records, invalid pairs reject, original cache helpers are bound, and the
  scenario has one checkpoint, restore, and no screenshots.
- Thirty-two record, formatter, generation, loader, and combined-counter
  regressions pass in 4.397 seconds. The initial regression command contained
  the wrong module name `test_mail_generation`; that import error is recorded
  in `build/museum-regressions.log`. The corrected complete command uses
  `test_mail_generate` and passes in `build/museum-regressions-final.log`.
  No full-project regression claim is made from this focused batch.
- Independent Docker builds agree for image, relocation, and manifest.
  Independent assembly agrees for the 140-byte creator wrapper, 52-byte home
  gate, and 20-byte queue gate. The queue gate relies on the wrapper's explicitly
  cleared `a1`, and returns the native receipt result on both branches.
- Compared with the postal build, only native code, configured resident,
  creator, and self-DMA data change. The creator grows 736 stored bytes. Only
  the creator end and following unchanged font resource's physical start change
  in the DMA table. All 13,393 ordinary edits and 2,783 wider item slots remain.

The silent native run `build/smoke-museum-01` completes successfully with 54
original metadata/complete creation/home delivery combinations and 75 complete
readbacks. All five fallback cases and twenty introduction/wrong-item/fossil/
combined pending-loop cases pass, including the maximum 31-fossil saved count,
partial delivery, retained failed eligibility/counts, resource retries, and
duplicate-notice prevention. Five invalid requests retain destination and capital.
Native fossil selection/RNG, sender identity, gift, type, and paper remain intact.
All 313 calls and 666 assertions pass. The creator is cartridge-loaded; only
140 original comparison bytes are debugger-uploaded. The fixture deliberately
supplies another initial player index to exercise successful native fallback;
that does not establish a naturally occurring scheduling path.

Save/globals, heap/stack/module guards, checkpoint restoration and post-restore
assertion, erased FlashRAM, unchanged blank Pak, and graceful shutdown pass.
The 1,226-record result is complete, not a partial/timed-out run. There is no
audio, screenshot, Expansion Pak, real save write, or claim of normal scheduling,
actual save/reload, editorial/presentation review, or original-hardware acceptance.
The independent native-result audit passes in 2.206 seconds. It binds the exact
ROM, regenerated scenarios, helper source, complete case/call/assertion counts,
checkpoint restoration, and unchanged isolated save hashes.

## Artifact identities

| Artifact | SHA-256 |
| --- | --- |
| Complete ROM | `c357c13e9886072d4ae12fe1aa4ae8dbd715131aead2e788e5afcdca013ada86` |
| UPS | `4ffd1e329ec5f3095391f7db668bf8092ef363676b7a48d1ac2caecaad6de7ae` |
| Creator image | `8caa8333ab2f3023df7d8beb3edc308fc09ba3c466664b930bb346ece7a20d81` |
| Creator relocation | `3ced3f5917255bfb19a4b12f9781d55b3b735c2b3394cdcd6e21d596be558d9d` |
| Host tests | `0c8227870f6be7efa714e329567537b7ed4168010577bb3d14a5b55ad56ada72` |
| Sanitizer tests | `6a3668bd2a41ae023da1303bd450d7ce9321e61973d58286073de353739301fc` |
| Installer tests | `ca0e825a259b1d0fdcc85ec43670a9d366c8368332f1c09573db1784e377e290` |
| Assembly report | `93403fdced68d2647fe1b3be5c1c83986d1d5557f2d251aa835073112f82a071` |
| Reader/loader regressions | `e025a96a3ae5855ba1f3d956a14f021f757967ac134a21770575ffa397f10ad1` |
| Scenario tests | `237c78ad741cf1b4c33b8e2a98c71873db8bab4f84f2f22e66eade142aeeb145` |
| Native scenario | `0de640f0240be9389357b31001d9338e07bfb2dc2458395f050afab803570de6` |
| Native results | `e947e22d0013c41317e1695826b11e5c8a26e2d0de9c2722a8267eaa52b346ee` |
| Restored native checkpoint | `4bad251a18c595cdc91b4ee8c51b8579bba6c6cb0cbc3ef5f7f80d19067be323` |
| Native helper source | `8ed848a5f3721279b9a94d7909819a9ae026658c5916ee313fc3b38d911efdf7` |
| Native scenario source | `1a45d0f1d7056db8d8c399ad59c4802abcf862a10e84e749d265db353d9cd494` |
| Native result audit | `1985d0c51c0de1f86dc2136760ff937bbeb7c50cf2bae75d4984f4d18ead5d0c` |

## Reproduction and continuation

Use the postal creator/full-ROM recipes with `--museum` added to creator build,
output `build/museum-mail-creator`, and `--english-museum-letters` added to the
complete ROM build, output `build/museum-letters-pilot`. All earlier English
options remain enabled. Generate `tools/museum_scenario.py --output
build/museum-scenario.json --boot-output build/museum-boot.json`. The silent
emulator runner uses this ROM, the two scenarios, a fresh isolated output,
the existing Xvfb, `--no-initial-screenshot`, and a 900-second bound.

Continue remaining letter consumers,
names and wider callers, general text, and diagnostic scripts. The museum's
canonical saved sender key must remain intact; its ordinary English display
label needs its own verified consumer mapping. Normal scheduling, real saving
and reloading, travel, editorial/presentation review, available original-hardware
acceptance, patch-only release preparation, title-first English artwork, and the
GameCube-style keyboard remain. The complete project goal stays active.

The next [Snowman group](../../specs/SNOWMAN_LETTERS.md) has source approval for
all twelve templates/36 parts and all twelve complete item names. Its three audit
tests pass in 1.127 seconds, including changed-name, source, and malformed-resource
rejection. The audit report has SHA-256
`a1b773d101f023d068888b13a31483323ff4943f9314da66a2ac14a006238b92`,
and its test log has
`6a7811ac322eaf3c341b66862b2bd0aae74afdf5391a1a561274ee5b3c3dcde5`.
Snowman creation/receipt/reward retry remain unimplemented and uncredited.
