# English police-station artwork

`build/police-artwork-01/animal-forest-halfwidth.z64` installs the supplied
English POLICE sign and wanted poster in both seasons, retains the complete
English shop/keyboard/Nookington/screen work, and keeps all conversation fixes.
ROM SHA-256:
`7ec5ba6eb5a68e15a3c89ab37111cf758a5b02241a1f51291cebf174b64ef6ad`.
UPS SHA-256:
`cfca7ddef8bdff34fd90bd23f595b41053127aa3a99de97df808cfadcd041265`.
The cartridge remains 32 MiB with four-MiB RAM use, unchanged saves, and no new
allocation. See the [specification](../../specs/POLICE_STATION_ARTWORK.md).

Four 128×32 CI4 textures are imported exactly. The donor's removal of the small
Japanese plaque is included, and two triangles belonging to the separate
Japanese notice sign are removed in each season. Every remaining triangle's
native positions, winding, and lighting match its predecessor. Twenty-three
used vertices fit in the existing 27-/24-vertex summer/winter loads. Native
winter roof lighting is retained when shared corners are duplicated for UVs.
Both the original and actually streamed building copies contain the changes;
the appended Nookington slices remain unchanged.

Three focused checks pass in 7.292 seconds. They cover independent native GBI
compilation, exact donor textures and visible colours, actual palette/model
bindings, retained oriented geometry, rejected source/region/command changes,
all 92 seasonal building streams, complete previous resources, and UPS
reconstruction. No native scene or hardware acceptance is claimed.

`build/title-police-combined-01/animal-forest-title-preview.z64` adds the
unchanged English title and warning. ROM SHA-256:
`aa0978ff0efd992face36276e02e867f64c618b1469326ad4904013793e71f95`.
UPS SHA-256:
`308e5bbc276de0b3336b4ba6b2192b50e9e46d435dba1692afcd2510c4098108`.
One focused combination check passes in 8.106 seconds, verifying complete
rebuild/UPS reconstruction, all retained police/shop/text resources, strict
corrected-grid ownership, and identical tested title/boot/warning components.
The combined candidate requires an Expansion Pak. It is not a new recommended
handoff; the recorded keyboard test limits still apply.

Continue Redd's summer sign, other remaining decorative art, and final scene
acceptance. The winter Redd sign is covered in snow and already matches the
English GameCube donor, so copying summer's lettering over it would be wrong.
The summer donor introduces red palette entries 13/14 that are unused by the
native summer tent. Bind the tent's exclusive summer palette before applying
those colours; preserve all winter and other-building colours.
