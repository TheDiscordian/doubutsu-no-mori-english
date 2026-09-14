# V3 imported villager audio checkpoint

## Result

Cheri and Punchy's actual donor melody programs are installed in the experimental
V3 cartridge, with full voice IDs 285/286 preserved through the native entry
points. All four instruments and their complete sample dependencies match the
original N64 assets. Five focused checks and a combined silent native audio/draw
scenario pass. This does not enable the villagers in ordinary gameplay or the
web patcher.

## Exact artifacts

- Build: `build/v3-audio-runtime-02/animal-forest-v3-asset-loader.z64`.
- ROM SHA-256: `388dc6abc60767ec22a30130995e9f18afc58d0414600d470aec0154d75f4169`.
- Patch: `build/v3-audio-runtime-02/asset-loader.ups`.
- UPS SHA-256: `a6f19218b92bf3ea45447b6c51302d23ad1f2283697b96772fd76d2ba206251e`.
- ABI-3 blob SHA-256: `e7d53d1f9d4a97ef1b07928dfb09d08d200839c6f7c3015e63b9c1d5b24e6987`.
- Cheri fragment: 448 bytes, SHA-256
  `08904f38c5a7f1706e847a2824a4c763e0c4d6a0f7e9e44afcafc4750420ab8d`.
- Punchy fragment: 288 bytes, SHA-256
  `78cea967daa7d12a0aba57ca0e6dfe9dc39eff1baeaab11b003d7a1b5ef2a7ce`.

`build.json` binds converter/runtime sources, donor resources, installed writes,
toolchain, stack usage, and preserved assets. Startup code is 432 bytes; combined
asset/draw/voice/melody code is 2,032 bytes. The blob remains 16 KiB. Melody start
uses a 64-byte stack frame; native draw uses 136 bytes. Ordinary heap bounds and
saved layouts remain unchanged. The import-free composer returns the exact
pinned V2-11.

During assembly review, the first untested audio build was found to pass RAM
medium 0 to native `Nas_FastCopy`. That helper only completes PI transfers and
would block forever. Build 02 uses a bounded CPU copy for imported resident
programs, retaining cart DMA for original voices. The host fixture now rejects
medium 0 and checks both distinct paths. Build 01 is not a playable handoff.

## Focused verification

`python3 -m unittest tests.test_v3_villager_audio -v`: five tests pass, no skips.

- DOL address mapping, malformed sections, and bounds.
- Melody offsets, relative targets, terminators, and reserved-slot limits.
- Host runtime with address/undefined-behaviour sanitizers: command ordering,
  native cart versus imported CPU copies, every relocated pointer, unchanged
  neighbouring bytes, native/imported full IDs, low-byte aliases in both
  directions, missing IDs, invalid tracks/pointers, and sequence invalidation
  during audio wait.
- Actual installed programs, all four shared instrument dependencies, mutable
  state initialization, absent slots, and blob guard.
- Actual widened instructions/hooks, all 256 original source ranges fitting
  native slots, unchanged original audio resources, source hashes, exact UPS
  reconstruction, and unchanged import-free output.

## Native verification

`build/v3-audio-native-01/`: current build 02, Expansion Pak enabled, audio
output disabled, private Xvfb, no initial screenshot, no seed save, no FlashRAM
or Controller Pak write opt-in. The first combined attempt completes with
121 recorded steps and exit status 0; no retry is needed.

- Results SHA-256:
  `49afbb41c5b50af5359e5e7be6dbcb9c8084ade8adfcaf64f8ac599a91debc43`.
- Run record SHA-256:
  `aa5ba145b5fbabc7b1eeb42eed9c9aaea2811045ca79fa4d68f16f8c057fe2fd`.
- Scenario SHA-256:
  `7c39d53dc333700033133569743b1e4d6e83708cb35bb85b37507fb9c3fe91f4`.
- Audio fixture SHA-256:
  `93b157bde3a9750e65ead6311a510d32b52066c4146cd4efe37cc331daa85888`.
- Draw fixture SHA-256:
  `48aef779139fcd0a29ee1c7cee47e7e2673ba7fafa791f4aff112c62e28c0dd2`.

The real `Na_Inst` loads Cheri on track 15; `Na_MelodyVoice` loads Punchy on
track 6; `Na_Inst` then loads original voice 29 on track 15. Each complete melody
pool matches the expected fragment plus all nineteen relocated offsets, leaving
other slots untouched. The complete V3 blob changes only at the intended
full-ID state words. After two ordinary graph frames, native audio ports report
tags 29/30/29 and note count 1. The count helper rejects the wrong full ID in
both directions of the 29/285 low-byte alias. No audio helper is mocked.

After checkpoint restoration, both actual NPC overlays load through the native
loader with complete relocation/BSS comparison. Four rows per owner—native
ordinary, native test, Cheri, and Punchy—pass actual draw and constructor-tail
checks, sixteen assertions total. The destination intentionally has only
four-byte alignment. Missing imported identity `E0DA` leaves it unchanged.
Actor bytes change only at the voice field. Fixture guards, the complete V3
blob, translation guard, and fault pointer pass. A final checkpoint restoration
returns to ordinary execution without a fault.

This closes the deeper draw/tail test left incomplete in the preceding batch.
It uses the corrected existing fixture; no old cartridge is replayed.

## Remaining scope

Native playback-entry/sequence processing is verified, not listening quality,
complete conversation, NPC construction/animation, move-in, house use, or saving
an imported identity. Original hardware remains untested for V3. Existing V2
saves and cartridges remain preserved. Use disposable saves: imported-profile
and cross-version compatibility are not established by unchanged field widths.

Next work is the ordinary-villager name/default/house/selection and gameplay/save
paths, followed by the complete furniture pilot and broader import batches.
The full goal, browser selections, and e/e+ adapters remain open. Stable V2,
the public/local patchers, and the released trailer are unchanged.

## Next-batch starting evidence

The donor inventory identifies Cheri as peppy, with clothing `2498`, umbrella
index 3, and catchphrase string `072B` (`tralala`, seven bytes). Punchy is lazy,
with clothing `24BF`, umbrella 13, and string `072C` (`mrmpht`, six bytes).
The donor strings are present in the extracted reference bank. Clothing IDs and
house-layer IDs still need native identity/asset checks; shared numeric values
are not sufficient evidence. Neither full catchphrase fits the native four-byte
saved field, so its default/reset/borrowed-display handling needs an explicit
V3 key/profile design, not silent truncation.

Native defaults use six-byte rows at VROM `00E03000`. `mNpc_GetLooks` is
`800AA1E0`, `mNpc_SetDefAnimalInfo` is `800AA218`, `mNpc_SetDefAnimal` is
`800AA29C`, and `mNpc_SetAnimalInfoNpcIdx` is `800AD8C4`. The personality table
is `8010AF58`. `mNpc_SetNpcList` loads the complete house resource at VROM
`00E02000`, then directly indexes by actor low twelve bits. The donor
`npc_house_list` is 1,904 bytes: 238 eight-byte records, including its test slots.
Native initial selection and later move-ins remain bounded to 216.

Existing V2 display APIs also enforce native capacity: `af_load_display_name`
and `af_get_display_name` distinguish 216 villagers from special actors;
`af_load_catchphrase` rejects imported actors. Additional explicit bounds occur
in `overlays/text_names/names.c`, `overlays/letter_names/names.c`,
`overlays/letter_ui/address.c`, and the villager-event, quest, departure,
treasure, and NPC-capture creators under `overlays/mail_generation/`.
Extending one shared name table does not connect these readers. Preserve their
player/special-character distinctions and saved capacities while adding imports.
