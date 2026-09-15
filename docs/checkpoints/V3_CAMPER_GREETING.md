# Summer greeting selection and last-gift state

## Implemented

ABI 80 selects the actual installed summer messages for masked camper `D08F`.
First introductions retain the donor's six personalities, four time classes,
and three alternatives per class, using the native time/RNG helpers and the
complete message group beginning at 11754. Repeat bases are 11826, 11856,
11887, 11917, 11947, and 11977. The actual donor REL's six-entry table and
complete selection function are hash-bound, not inferred from translated names.

Repeat offers preserve the donor's conditions: an empty pocket and at least
3,000 Bells enable the money game; ordinary, non-wrapped/non-quest furniture,
carpet, or wallpaper enables item games. Enabled imported furniture participates
through the existing checked item classifier. Unsupported imports and clothing
do not qualify as furniture. If both offers are possible, the existing random
source chooses one. The full last-given item identity is excluded from subsequent
offers, including when a later pocket still contains another eligible item.

Two native normal-conversation callbacks retain their original full item stores,
arguments, delay slots, and return addresses. A 36-byte resident adapter records
the item before tail-calling the actual callback. The native quest constructor
resets this field before its original five-byte `bzero`, matching the donor's
transient `give_item` lifecycle. The field is the previously unused halfword at
`804A1A12`; the code occupies `804A2F30..804A2F53`. No saved field or permanent
reservation grows. Actual item selection/award filtering remains work.

The greeting owner grows from 3,552 to 4,064 bytes. Its existing native code and
data remain in their original positions; only the 48-byte dispatch window changes.
Native winter and ordinary dispatch retain their complete original selectors.
The 512-byte suffix fits the existing `8800`-byte shared conversation buffer.
The flattened relocation header retains every original target outside dispatch,
converts seven data-section offsets explicitly, and contains 55 entries in
256 bytes. Full owner comparisons at two relocation bases pass.

The complete greeting/relocation resources move from virtual `824500`/`8252E0`
to `03A10000`/`03A14000`, retaining their two adjacent DMA slots and original
compressed physical bytes. Checked raw copies append to existing import storage.
The manager's loader arguments change together; its initializer address and
shared buffer stay fixed. The complete current English normal/quest owners and
their existing relocations retain all other changes, including English mail.

## Artifacts

- Full: `build/v3-camper-greeting-runtime-02/animal-forest-v3-asset-loader.z64`.
- ROM SHA-256: `22293297ece2547c93f26d038fb74396163943ad548dab53b3b9ded9af9fdf39`.
- UPS SHA-256: `c3e1c231728a59d28fff447e7d71ae3c04876b2434ec0121c835cd03975f133e`.
- Report SHA-256: `31c5d19fcedfcf2852d9b584f07c130d336a007bdb61109fd983a6dee73602cc`.
- Greeting owner SHA-256: `59c8cb3d133f3392918f84611eacd20e8175544e9faac577ba6683460108b823`.
- Gift adapter SHA-256: `2c8832a742bc91ea9c9fd7d09cb74e5bd84aa1394fdea73cef0ed9a7d291e5fc`.
- Ten-item subset: `build/v3-optional-camper-greeting-01/animal-forest-v3-asset-loader.z64`.
- Subset SHA-256: `ca4baf84a6f7fc31b4080dfc04ee6ba4325831d5b978b59a13ce1ee36745e361`.

## Focused checks

Seventeen current focused/composition checks pass:
`python3 -m unittest tests.test_v3_camper_greeting tests.test_v3_optional_composition -v`.
They cover actual donor bindings, complete current owner preservation and
relocation, independently encoded gift/reset instructions, native delay slots,
source rejection, safe physical/virtual ranges, package CRC, header checksum,
unchanged saved profiles, and exact full/V2 output for all/empty selection.
All 59 experimental selections remain in the offline composer. UPS reconstruction
passes. Neither served patcher changes.

## Native evidence and unresolved stop

The first fixture attempt is rejected before executing the boot loader because
it omits the existing required complete boot-code proof. The corrected attempt
uses that proof and the established paused model-pool borrowing method; it does
not raise the ordinary heap or debugger's permitted direct-call address range.

`build/v3-camper-greeting-native-02/results.json` records 87 entries, 33 calls,
and 68 passing assertions before timing out. Result SHA-256:
`3c868651937a3180fa05d6cb327b4b1eef7b40df05a7ce2a1237668001c6919b`.
Actual native loading and full relocation of both English owners pass. The
changed **real quest caller** loads the complete extended greeting owner and
matches its independently relocated image. All six first-introduction
personalities, four time classes, six selected English message reads, six repeat
bases, and thirteen item/Bell/condition/exclusion cases pass. These are component
calls with borrowed fixtures, not ordinary conversations or handovers.

The later instruction-window check does not reach its expected stop at
`80584C88`. A remaining-only diagnostic avoids replaying the successful cases:
`build/v3-camper-greeting-native-remaining-01/results.json`, SHA-256
`9c297a4fd241bbf0053f3b24d015fe40dc802d90dea7914a69ddfce64bb76074`.
It records thirteen entries and six passing assertions, then the same timeout.
Captured `v0`/`v1` both contain expected message 11947 (`2EAB`), no faulted thread
is recorded, and the graph thread is waiting at `8002F13C` rather than stopped
at the requested boundary. This is insufficient to distinguish a debugger-stop
problem from a caller/control-flow defect. The result remains unresolved.

No complete native pass, final guard/restoration pass, actual gift/reset-window
execution, ordinary conversation, persistence, or hardware result is claimed.
The existing fixture contains the later gift/reset checks, but those are not
reached. Do not reinterpret that absence as success. Preserve this failure for
a focused dispatch/return trace or the combined native conversation batch;
do not keep replaying the successful prefix or change game code solely to make
a debugger breakpoint easier to catch. A credible game defect must be resolved
before a playable handoff.

Runtime-02 contains the same ROM/UPS as runtime-01; its builder strengthens
source/storage checks and refreshes the current quest-owner hash in the report.
The recorded execution therefore tests the final cartridge content, not a
different build labelled as equivalent without comparison.

## Next work and boundary

Continue actual trade selection and selected camping rewards. The donor's
`aQMgr_order_decide_trade_common_item` chooses the tent list with a 20% chance
inside the tent; do not add ordinary shop stock or substitute an unrelated gift
route. Its random furniture/carpet/wall picker also excludes `give_item`; that
reader needs the new full-ID state as well as greeting eligibility. Preserve the
native winter behaviour and other categories. The actual native common body has
no winter-special stock roll; its 10% branch selects house furniture. See the
current [trade checkpoint](V3_CAMPER_TRADE.md) for implementation and executed
full greeting return/gift/reset checks. Finish remaining masked readers and
lighting/floor sounds, then combine ordinary construction, conversation/award,
entry/exit, and persistence checks, retaining the dispatch failure above.

This is not a complete-import playtest handoff. Saved format 2 and selected
identities are unchanged; imported saves need matching/superset profiles and
must not be loaded in V2. GitHub development source is allowed. Both served
patchers stay on V2 until the user tests V3 and explicitly approves the switch.
