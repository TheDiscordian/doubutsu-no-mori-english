# Garden runtime and optional selection

## Completed batch

Six complete garden objects have fixed IDs/profiles, full English names/prices,
placement readers, collected-item catalogue entries, HRA/feng shui properties,
and saved-profile dependencies. Four use their original ordinary stock groups;
the gnome uses native lottery stock and remains catalogue-orderable. The mailbox
is not for sale, and its post-office reward delivery remains unfinished.

Backyard series 56 and its English score-letter name are installed. The full
catalogue has 452 furniture entries and retains all 248 clothing entries. The
offline composer supplies 39 experimental options, exact select-all/empty
outputs, and dependency-safe per-item choices. Neither web patcher changes.
See the [runtime specification](../../specs/V3_GARDEN_ITEMS.md).

Full artifact: `build/v3-garden-runtime-02/animal-forest-v3-asset-loader.z64`.

- ROM SHA-256: `436c5cec2aeb1d9f34d1fb71217ec62a6ef232d91573e0112d7055c65345f1d0`.
- UPS SHA-256: `77fb2291e92534f9ccf53fb1df31aef5bc954a1cb263817fc301bbd67211ad01`.
- Report SHA-256: `e931376f12e03eb3adbff213227c144c39d0debcff5cdf00f399f10ad4279cda`.
- Blob SHA-256: `3a24cd81f7a5df21fecb5b4f882aeef6451dbc4e344af0c2a98d50f97965f257`.

ABI 64, 64-MiB cartridge, Expansion Pak required. Blob storage is 1,620,672
bytes. Permanent RAM and the existing menu reservation do not grow. Catalogue
image growth is 64 bytes; English score-letter image growth is 32 bytes.
The latter uses 62,688 image bytes and 960 relocation bytes. The HRA counter
image and all its applied ABI-63 instructions remain unchanged in size.

Saved format 2 remains; six selected furniture bits are added. Older profiles
must reject new-profile saves. The actual codec accepts equal/superset profiles
and rejects missing dependencies without writes. Ordinary cross-build reload
is not established. Keep backups; do not load imported saves in V2. This is an
integration cartridge, not a complete-import playtest handoff.

## Verification

Four focused integration checks pass, covering every actual model/profile/seed,
all sixteen item records, exact scoring/letter changes, retained native stock,
catalogue identities/capacity, complete relocation retention, CRCs, save bits,
and whole-cartridge change scope. One expected stock-order assertion is corrected
to account for the builder's existing sorted imported suffix, then only that
failed check is retried; the corrected check passes in 0.105 seconds.

The initial build fails safely on a lottery-list assertion: its first zero is
at `334`, with alignment padding at `336`. The corrected builder binds the
complete thirty-item list and inserts before `334`; no unreachable item is
installed. The fresh completed output passes full UPS reconstruction.

The initial native run, `build/v3-garden-native-01/`, passes **187 records**,
including 73 explicit memory assertions and 104 native calls. Results SHA-256:
`e40f8b7af2b281b4d83577d0adccf60ad1f3d73c74b387b1a3d52e323aece36e`.

Checks include all six actual name/price/type readers; complete moved tables;
placement cells; retained static, animated, and clothing readers; disabled
rejection; actual catalogue-owner relocation; ordinary/lottery/not-for-sale
decisions; native lottery selection and gnome pocket/ownership insertion;
complete HRA grouping, five-member backyard completion, all 23 counters, and
real lottery/post-office point values. Birdhouse and Mrs. Flamingo pass paired
native model-bank loading, reuse, rotations, cleanup, and guard checks. Complete
save state is restored, the checkpoint is restored, and shutdown is graceful.
No native retry is needed. Audio is disabled, with no game save writes.

## Individual selections

Nine focused composer checks pass in 4.282 seconds. These include the exact
all/empty cartridges, derived house/outfit dependencies, independent IDs,
selected catalogue packing, all enabled words and both CRCs, order independence,
actual C codec compatibility, and the final garden profile row.

The selection checks identify and fix an existing HRA issue: disabled furniture
metadata still inflated complete-series requirements and recommendations.
Composition now replaces only unselected imported records with the existing
inert metadata value. Code, native records, selected properties, and names stay.
One selected flamingo yields one backyard member; unselected boxing has none.

Local mailbox/Mrs. Flamingo subset: `build/v3-optional-garden-01/`.

- ROM SHA-256: `88c21ebcc7a3866aaff0ed3edf3505648ac6ddec57d05272127cadea626aaaa3`.
- UPS SHA-256: `5ec02b3761d0d87c972ec516fddb947458da793eb4cf1156ca1b5aafcf7d3d91`.
- Report SHA-256: `819c81db92fc53d9e18c66a4602190552adc9490645abdb04ce703af45678038`.
- Profile SHA-256: `f8da1755c4b5cb707ebc99d5614ea66809b534ad5de710829b4479db4465b334`.

Its initial changed native grouping check, `build/v3-optional-garden-native-01/`,
passes **35 records**, including 20 explicit memory assertions and seven native
calls. Results SHA-256:
`049b818ba33bdd9e46c3da78c4a6ede199f5c35089c018aa40c14ad2618128bf`.
The actual relocated evaluator counts one selected backyard member, excludes
all boxing members, completes the one-member theme, and applies the mailbox's
real reward category without incorrect counters or guard writes. Complete save
state and checkpoint restoration pass, with graceful shutdown and no audio or
game save writes. No retry is needed. Unchanged selector/catalogue packing
evidence is reused, not represented as a fresh full-menu playthrough.

## Remaining work

Implement the mailbox's faithful post-office reward path. Complete ordinary
purchase/reward, placement, persistence, and player testing. Continue remaining
donor item families, villager gameplay/persistence, and offline browser work.
Keep both served patchers on V2 until the user tests and explicitly approves V3.
