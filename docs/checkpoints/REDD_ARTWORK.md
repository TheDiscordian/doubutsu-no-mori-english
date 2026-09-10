# Redd's English summer sign

`build/redd-artwork-01/animal-forest-halfwidth.z64` adds the exact GameCube
BLACK MARKET sign to the complete police/shop/Nookington/grid candidate. ROM:
`7cba9ed279dd90b8fa903cd3ab1745aacf7bd0383c5b43347cadc1bf6fecc39a`.
UPS: `5f6f00508ad98a9fb5c92807f3dbf4d139271adbec1e69800c213dd5f9f0b6cd`.
It remains 32 MiB with four-MiB RAM use and unchanged code, allocations, doors,
models, and saves. The [specification](../../specs/REDD_SIGN.md) binds the source.

The 128×32 summer texture and two previously unused summer palette entries are
replaced. All 31 native model vertex uses match the donor. The palette has one
exclusive summer reader; neither new index changes any existing native summer
pixel colour. Winter's snow-covered sign, its palette, all police resources,
and the appended Nookington signs remain unchanged. Both building-object copies
receive the English summer texture.

All three focused checks pass. Two source/ownership and whole-cartridge checks
pass in the initial 6.769-second suite; the corrected visible-colour assertion
passes in 0.089 seconds. That assertion preserves native hidden RGB under fully
transparent pixels, while requiring exact alpha and every visible colour.
The checks also cover exclusive palette ownership, unchanged existing colours,
the source-sized texture, rejected region/resource/size/boot changes, all prior
resources, and complete UPS reconstruction. Ordinary scene/hardware acceptance
remains pending.

`build/title-redd-combined-01/animal-forest-title-preview.z64` adds the unchanged
English title and Expansion Pak warning. ROM:
`b37f9ecf3ccde2344df6c6cad8e39baea73a7c2eaa6ea3f7cad865eeb8aebc9b`.
UPS: `f31303a9d3ffac208beb6439330251fdbd1aade7eae56ebb74102216ffb4b65b`.
One focused combination check passes in 8.040 seconds, covering full rebuild,
UPS reconstruction, every retained artwork/text resource, corrected grid
ownership, and identical tested title/boot/warning components.
This combined candidate requires an Expansion Pak. It is not a new recommended
handoff; later keyboard input, ordinary scenes, save/restart, and hardware checks
remain pending. Continue remaining decorative art and the bounded remaining
input checks using a matching checkpoint and controlled emulated frames.
