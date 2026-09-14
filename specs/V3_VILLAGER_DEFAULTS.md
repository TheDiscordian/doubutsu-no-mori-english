# V3 villager initial defaults

## Installed scope

The `--villager-text` development variant includes bounded personality lookup
for both pilots and Cheri's initial identity, personality, clothing, catchphrase
reference, and hometown. It does not enable move-ins. House data, selection,
remaining identity readers, and save/profile handling remain required.

Punchy's starting cherry shirt requires a clothing import. His initializers
therefore leave the destination untouched; they must not install the different
native artwork at the same item number. His name, full phrase, draw record,
audio, and personality lookup remain available for component development.

## Clothing identity

The verified donor `forest_1st.arc` contains 256 32×32 CI4 clothing textures in
`data/tex_boy.bin` and 256 sixteen-colour palettes in `data/pallet_boy.bin`.
Native clothing uses VROM `00B68000` and `00B88000`, respectively. Decode GX
tiling and convert RGB5A3 palettes to native RGBA16 before comparing all 1,024
pixels. Compare against all 256 native candidates, not only the same item ID.

- Cheri's `2498`, yellow bar shirt, has exactly one complete native colour-image
  match: `2498`. Both complete converted texture and palette also match that
  native record. Native shirt `2497` shares indices but has different colours;
  comparing texture indices alone would incorrectly identify it as equivalent.
- Punchy's `24BF`, cherry shirt, matches no native colour image. Do not replace
  an existing native shirt globally or use a superficially similar shirt. Add
  its real clothing/item support as a selectable import dependency.

The builder pins complete input sources and the reviewed mappings. Build reports
record donor/converted/bank hashes. The native shared loader at `800B1EDC`
accepts a clothing index below 256 and transfers 512 texture bytes and 32 palette
bytes; Cheri uses index `98`. No clothing bank changes or new item ID is installed
by this batch. Clothing artwork identity does not establish every shop/price/
catalogue property of a later standalone item import.

## Native initialization

| Entry | Adapter |
| --- | --- |
| `800AA1E0`, personality lookup | Resolve present import metadata; retain native/test IDs 0–217; return zero for missing/invalid IDs |
| `800AA29C`, defaults from a full table | Initialize a verified import without indexing beyond the native array |
| `800AA218`, defaults from one record | Use the import's verified defaults, not the caller's native record or phrase index |
| `800AD8C4`, defaults from a villager index | Retain native indices 0–215 and resolve installed import indices independently |

Full-table and single-record routes retain native test IDs 216/217. The indexed
route keeps its original exclusion of those test entries. The original defaults
resource has **218 six-byte rows and four trailing zero bytes**, not 216 rows
followed solely by padding. The final eight-byte read is therefore safe. The
native personality table has corresponding test rows. Original data is retained.

Imported initialization writes exactly the original initializer's fields:

- `Animal+000..001`: sixteen-bit actor ID.
- `+002..003`: current land ID from `80129E08`.
- `+004..009`: six-byte current land name from `80129E00`.
- `+00B`: personality; peppy is 1, lazy is 2 in both games.
- `+4E5..4E8`: the full-phrase adapter's four-byte V3 default reference.
- `+520..521`: verified native clothing ID.

Other fields, including name ID at `+00A`, follow their existing later
initialization paths. This is not a replacement for full saved identity creation.
N64 `Animal` has no GameCube-style saved umbrella byte. Do not write the donor's
umbrella into native padding. Draw-record umbrella routing is a separate reader;
its asset correspondence and ordinary rain behaviour remain to be verified.

Null destinations, missing imports, incomplete outfits, and invalid indices are
no-write. Original defaults/record pointers are used only for bounded native IDs.
Present metadata and a verified outfit do not grant roster eligibility.

## Memory and compatibility

The existing 32-byte metadata row now uses offsets 30–31 for a sixteen-bit
verified native clothing ID. Zero means the outfit/initial-default dependency
is pending. All other fields and the ABI-4 32-KiB reservation remain unchanged.
Four additional return bridges use `80462F40..80462F7F`, before audio data at
`80463000`. Text/default code occupies the existing region from `80464000`.
Patch entries require exact displaced instructions; bridges contain no copied
PC-relative instructions. Original/default table resources and ordinary heap
allocations do not grow.

V3 phrase references still require compatible V3 metadata. Save layouts do not
grow, but these new saved values are not safe to load in V2. Imported ordinary
save/reload and profile handling remain unverified. Use disposable saves only.
The web patcher stays V2 until user testing and explicit approval.

The [checkpoint](../docs/checkpoints/V3_VILLAGER_DEFAULTS.md) records the exact
current build, focused checks, native results, and remaining work.
