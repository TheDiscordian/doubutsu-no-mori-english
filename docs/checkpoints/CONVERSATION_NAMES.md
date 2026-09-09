# Complete conversation identity names

## Installed state

`build/conversation-names-pilot` connects three request/conversation fields and
the ordinary resident's other-villager field to complete eight-byte English
names. The [specification](../../specs/CONVERSATION_NAMES.md) records the exact
calls, existing destination capacities, and startup bridge. Saved names remain
six bytes. Selection, colour, timing, actor allocation, relocation, and the
complete secret-letter creator remain unchanged.

The startup-owned text extension adds a guarded identity-to-display adapter.
It uses the native six-byte result plus two spaces as fresh fallback and accepts
only IDs `E000..E0D7` for the full-name replacement. Its 3,568-byte blob requires
3,583 allocated bytes, 320 more than the choice-only variant. The resident module
does not grow; the actual cartridge configuration remains four MiB.

## Artifacts and reproduction

```sh
python3 tools/build_text_extension.py --choices --identities --output build/text-names
bash tools/build_conversation_names_pilot.sh
python3 -m unittest discover -s tests -p test_conversation_names.py -v
```

- ROM: 33,554,432 bytes, SHA-256
  `69b9174a2d09df5bfdb5a1fc62312eb789e4c7360fb73a86146a35eb7c3e6677`.
- UPS: 5,129,927 bytes, SHA-256
  `62126b0610217c13dd7df6138142804e5d0b34d2238587af84d4d211fa6417c3`.
- Startup blob: SHA-256
  `59b483326e2edd9ec49d820eb167c675371d788eae04ec1ad61c8281d9811e1e`.
- Conversation actor: SHA-256
  `a44601242da4ac2e788a4dd7bd32ca0572a6f06fe9aa7f0bdf7d846752ce73f0`.
- Resident actor: SHA-256
  `2c440b6b17e9138cea2c1171642d4cdebe47eb56a2a7cc4f47cd00255ce21318`.

Independent pinned-toolchain builds in `build/text-names` and
`build/text-names-rebuild` agree on code, relocation, blob, loader, and manifest.
All prior translation payloads remain apart from the exact approved caller and
startup-code changes and resulting DMA packing. Generated game assets stay ignored.

## Bounded verification

All six focused tests pass in 73.603 seconds. Host ASAN/UBSAN checks cover complete
names, fresh fallback, null and unsupported identities, destination guards,
initializer rejection before writes, cache synchronization, and repeat setup.
Source/assembly checks retain the original stack frames, BSS capacity, field
colours, fixed calls, and relocation at two allocation bases. All three startup
profiles remain independently valid. Cartridge checks verify installed callers,
the complete secret creator, prior translation retention, and UPS reconstruction.
The selected legacy secret-actor mutation test and twelve counter tests pass.

The silent native batch in `build/conversation-names-native-01` passes twenty-six
calls and thirty-six assertions, including the preceding twenty choice/field
cases and six new identity-bridge cases. Actual startup, a complete eight-letter
name, disabled-resource fallback and restoration, special/invalid/null identities,
null destination, adjacent guards, and the four-MiB configuration pass. The
checkpoint is restored, all isolated FlashRAM bytes remain blank, and shutdown
is graceful. No native testing-setup retry is needed.

- Scenario: `build/conversation-names-scenario.json`, SHA-256
  `ab1017aae88120e671758d9def15b07c25defdaf70ac1709f4e977a80875f2fe`.
- Native results: SHA-256
  `7364193483af1bc71c2c052f1c76295f8efa2bfdfe7aeac13a990eb3d4756967`.
- Native run record: SHA-256
  `d96b4e08ec6e9d7642b104a99ec38c6da17d70709e99465f1c3e1881a6be38e5`.

Ordinary conversation interaction, save/restart, and original hardware remain
unverified. The counter verifies this installed route without duplicating source
names; other unfinished readers still withhold name-family-only credit.

## Next implementation

Connect the villager house-sign reader. Its position-to-name helper at `800ACF84`
has one direct native caller, `80A9640C` in `ovl_Nameplate`; the actor already has
an eight-byte name temporary but passes six bytes to the dialogue setter.
The random-name generator's only remaining caller writes the fishing record and
must keep its saved six-byte contract. Continue remaining item readers,
borrowed-catchphrase ambiguity, residual text/letters, and accents, followed by
the combined v0 smoke.
