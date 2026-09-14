# V3 speed-bag room scoring

## Implemented work

ABI 47 installs the actual `E8050000` HRA properties for item `3350` / runtime
index 1236. The native evaluator now has 59 series definitions, ten-byte name
keys, and completion masks, with boxing at its donor series 58. All original
55 definitions/name keys remain exact, and the original search storage is not
overwritten. Series 55–57 are disabled reserved rows, not silently installed
western, backyard, or harvest themes.

The converter checks all 27 relocated series-resource references and seven
count constants. Native necessity and theme matching use unrolled loops with
equality termination; 59 preserves those loops, whereas a direct change to the
GameCube count 60 would run past the arrays. No point formula changes.
The full metadata table still holds 2,051 rows; boxing grouping and its
ordinary-acquisition point weight are independent of construction/clothing.

The donor boxing surfaces have no mapping in this profile. The descriptor
uses an explicit no-match value, preventing unrelated native wallpaper/flooring
from awarding completion or generating an unavailable recommendation.

## Private artifact and compatibility

`build/v3-speed-bag-hra-01/animal-forest-v3-asset-loader.z64`

- ROM SHA-256: `e98ffd4b040a0fc664d7dff80f68ef46ecbcc9f35faeeb47793fc678343e442f`.
- UPS SHA-256: `9077122b76cb5d63f78d9d161efb23ec41a28463d259db09bd89c42771fdaf56`.
- HRA image SHA-256: `70e4a14f785e8d504ec814facdcaf69a1a1f080e2067ea40b954fb86c36b77c8`.
- HRA relocation SHA-256: `27b4b01b9b24e3bf81f4e95ff61166b645fd8f0a5f76898fcbd230d98d9c5ea1`.
- HRA image: 31,296 bytes; relocation: 1,184 bytes. The image has 1,472 bytes
  spare within its existing 32-KiB bound. The scheduler uses the actual new size.
- Added resources: 177 descriptor bytes, 590 name bytes, and 236 mask bytes,
  plus five bytes of alignment. No new suffix executable text is required.
- Linked descriptor/name/search addresses: `8092D024`, `8092D0D8`, `8092D328`.
- ROM: 32 MiB; Expansion Pak: required; permanent V3 prefix: unchanged 48 KiB.

The speed-bag row remains disabled and absent from the selected save profile.
The complete 192-byte profile and format 2 are unchanged from ABI 46. This is
not an ordinary cross-build reload test. Preserve backups; V3 saves must not be
loaded in V2 or incompatible earlier V3 builds. Existing user saves and previous
artifacts are untouched.

## Executed verification

`build/v3-speed-bag-hra-tests-01.log`: **four checks pass**. They verify pinned
donor/native definitions, disabled reserved rows, actual boxing metadata,
unchanged import-free conversion, source-damage rejection, complete checked
owner reconstruction, all count/reference patches, allocation bounds, current
cartridge composition, UPS reconstruction, disabled runtime eligibility, and
unchanged selected save profile. The builder also relocates independently at
three load addresses and checks all untouched original code/data/BSS.

`build/v3-speed-bag-hra-native-01/`: the **first run passes all 68 records /
37 assertions**, including graceful shutdown. The existing silent, isolated
HRA helper executes the current cartridge with a temporary private item flag:

- Complete native owner load/relocation and group initialization of all 2,051
  metadata rows and 59 definitions.
- Mixed-layer construction/boxing masks, and the clothing scoring path.
- All four expanded scoring functions: necessities, base series, themes,
  and sets. Both unrolled loops finish without a spurious bonus.
- The actual ten-byte `boxing` name; no false completed theme or surface
  recommendation with native surfaces.
- Seven missing-item calls, including speed-bag acceptance when temporarily
  enabled and rejection when disabled; the original five cases remain intact.
- Actual native birth weights, the safe one-past-native marker, original
  descriptor/search retention, complete resident-prefix retention, memory
  guards, no faulted thread, checkpoint restoration, and cleanup.

The result summary's legacy `native_missing_item_selections` field says five;
its recorded calls include the two new boxing calls as well. The helper's
summary field is corrected to seven without replaying a passed run. Only
reporting labels change after verification; the checked cartridge is preserved.

No historical build is executed, no physical audio is emitted, and no user save
is modified. The unchanged range/index detours retain their prior evidence;
this run targets the newly expanded scoring paths instead of replaying them.

## Remaining work

The score-letter creator has a separate original-name translation table that
does not yet recognise boxing. Extend it before enabling normal play; the
native scoring name alone is not full English mail support. Catalogue/group-A
acquisition, the selected save dependency, Punchy's house, and ordinary
interaction/persistence remain required. Matching boxing surfaces are optional
future item imports, not a prerequisite for the standalone speed bag.

This is a component build, not a playable V3 release or hardware-acceptance
claim. Source may be pushed on `v3/optional-imports`. Main, public/local V2
patchers, deployment, services, visibility, and the released trailer remain
unchanged until the user tests V3 and explicitly approves the patcher switch.
