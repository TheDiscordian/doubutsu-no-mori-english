# Aloha scoring integration

## Completed change

Both enabled aloha mannequins had inactive HRA placeholders despite their
installed model/item readers. The correction supplies the actual donor clothing
properties in native format, preventing invalid series-63 grouping. Exactly two
four-byte records change; no code, RAM allocation, saved format/profile, or ABI
changes. Neutral feng shui metadata and exclusive acquisition status remain.
See the [specification](../../specs/V3_ALOHA_SCORING.md).

## Artifacts

Full integration: `build/v3-aloha-scoring-01/animal-forest-v3-asset-loader.z64`.

- ROM SHA-256: `e6a890c37e972422fe44cbbfb322dcccd17805186baa96ed7c20a45a2d4022f3`.
- UPS SHA-256: `2eca38ba7841970120e3b8021dc20e7b6e97629cb9306a58911d484716ab0807`.
- Report SHA-256: `33959d0d3224ace91e14cedf5215eeffa3cd7e15c1f7d067fea0290a9b5c4c6b`.

The local O'Hare/detour-sign/saw-horse subset, including its blue aloha dependency,
is `build/v3-optional-construction-02/animal-forest-v3-asset-loader.z64`.

- ROM SHA-256: `16c793afc30f36be06449e7cbcd9c84dcde075aa088fd9c93e2f68c58a507f28`.
- UPS SHA-256: `4f33fd563b2996da2454f81d74b502304e6390bf4c2b01f1c946f061a7d5566f`.
- Report SHA-256: `31c701f218bc81b460715db7180a38ced11a6a1be665ccd66f3d898a448bc5f4`.
- Profile SHA-256: `104758e16fbc274946c31776bc1c223b03ffd4d1120777094dbe41c476798fc1`.

Both remain ABI 62, 64 MiB, Expansion Pak required, and experimental rather than
complete V3 playtest handoffs. Neither patcher changes.

## Verification

Three focused scoring checks pass in 2.826 seconds: actual donor/display binding,
complete table preservation except the two reviewed records, unchanged image
and relocation resources, and full-cartridge reverse comparison/checksum.
Seven composer checks pass against the corrected source in 5.285 seconds.

`build/v3-aloha-scoring-native-02/` passes 52 records, including 28 explicit
memory assertions and 16 native calls. Result SHA-256:
`d351933ef9f090437346fe8dcec27d815c9c49c7247dcf29a3f9a38c05b609d1`.

The first setup stops before overlay loading because the harness omits the
required entry proof for loader `800262D0`. One correction supplies the existing
boot proof; the retry passes. The game code is unchanged by that correction.

The actual relocated HRA owner executes complete grouping and base-point
evaluation. All 2,051 metadata assignments and 59 group counts/masks match.
Red/blue base and rotated IDs receive the native clothing-point increment, with
cherry as the unchanged control. Disabling red returns the empty-room baseline.
Completion-array-end guards, temporary allocation guards, original native code,
restored owner/profile state, checkpoint restoration, and graceful shutdown pass.
Audio is disabled; no game save is written.

The corrected subset differs from the previously tested subset only in these
two HRA words. The 122-record subset catalogue/selector evidence in
[its checkpoint](V3_OPTIONAL_CONSTRUCTION.md) therefore remains evidence for
those unchanged consumers, not fresh native execution of this artifact. The
new 52-record run covers the actual changed scoring rows. No redundant menu
replay is performed.

Ordinary house evaluation/mail delivery, acquisition, persistence, remaining
donor conversion, and unserved browser integration remain work. This change
does not establish ordinary cross-build save compatibility; preserve backups.
