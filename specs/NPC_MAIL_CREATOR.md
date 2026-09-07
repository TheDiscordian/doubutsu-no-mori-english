# Whole NPC reply creation transaction

## Implemented boundary

`af_npc_mail_create` owns the synchronous capture-to-publication transaction
within caller-supplied transient memory. Allocation/loading and optional gameplay
hook installation belong to the implemented [resident loader](NPC_MAIL_LOADER.md).

The caller supplies a sixteen-byte-aligned `AfNpcMailCreateWork`, a separate
164-byte output letter, the resident active-session pointer, and the shared
capitalization word. Only the session's player/animal/visitor pointers and
condition/origin are inputs; caller-supplied event, stage, phase, source state,
captured fields, and initial-capital values cannot be reused as new state.

Native workspace layout:

| Offset, decimal | Contents | Bytes |
| --- | --- | --- |
| 0 | Scoped capture state, including the 32-byte session prefix | 444 |
| 444 | Alignment padding | 4 |
| 448 | Private complete native letter | 164 |
| 612 | Alignment padding | 12 |
| 624 | Complete generation/restoration scratch | 4,720 |
| 5,344 | End of allocation-owned workspace | — |

Compile-time assertions pin the native size and both offsets. The host tests
use compiler-reported host offsets rather than assuming 32-bit pointer layout.

## Ownership and validation

Before mutation, the creator rejects null or misaligned control objects, a
nonempty active-session pointer, invalid capitalization, missing identity
inputs, invalid condition/origin, inconsistent visitor/origin arguments, and
out-of-range personalities. Work, output, active pointer, and capital word must
not intersect each other, any input identity, or either embedded immutable
source resource. Output letters do not require word alignment.

The creator preserves the five input arguments but clears the rest of the
entire workspace. It supplies its own callback/staging pointers and copies the
shared initial capital state. Both embedded complete resources must pass their
approved whole-content digests before any native metadata or RNG routine runs.
The native clear routine initializes the private letter after complete workspace
zeroing, so native structure padding cannot retain an older allocation's data.

The active-session pointer is set only around the original six-argument native
metadata routine. Original preparation, random selections, gifts, stationery,
identity/status writes, and the tested capture adapters execute synchronously.
Nested whole-creator requests fail without replacing the outer session. The
scope is detached before formatting/publication; unexpected lost ownership
also causes failure and cannot leave a pointer to freed work behind.

Only final capture phase three with no recorded failure reaches full generation.
All selected parts, exact fields, native storage capacity, source CRCs, formatting,
and complete output must pass the existing generation transaction. Success copies
all 164 private letter bytes to the caller and advances the shared capital word.
Every rejection preserves the complete caller letter and shared capital state.
Transient workspace contents are disposable on failure; original RNG draws are
not replayed or rolled back.

## Tests and remaining integration

Six host tests, also passing with AddressSanitizer and UndefinedBehaviorSanitizer,
exercise all 48 personality/origin/condition/initial-capital
combinations, complete metadata and English text, all padding, input/resource
retention, reused dirty workspace, sixteen successive generations, missing
preparation or selection, unknown identities, lost ownership, nested requests,
source corruption, disabled catalog, unavailable selected footer, every catalog
read failure, invalid requests, alignment, and intersecting objects. The mock
native metadata routine tests ownership, not fidelity of the original RNG.

Small control objects aliased to the workspace are rejected before any alleged
session fields are read. A compiler-instrumented stack fixture checks this
ordering with real four-byte/eight-byte control objects, not oversized buffers.

The native fixture compares original metadata creation against the complete
transaction using the original routines and identical random seeds. It also
requires full-save retention, immutable source/code retention, original hook
restoration with cache maintenance, memory guards, free, and checkpoint restore.
All 48 original-versus-whole-creator comparisons pass, including full metadata,
native fields, original RNG state, complete English text, and thirteen gifts.
Eight further successive letters preserve the shared capital state without
using stale workspace inputs. Six native rejection cases cover altered sources,
disabled catalog, unknown visitor name, an existing scope, and workspace aliases
to both control objects. Each retains the caller letter/capital state; source,
scope, and control-alias rejections also retain both native RNG words.

The final run passes 163 native calls and 898 assertions across 2,101 steps,
including complete save retention, unchanged sources/code, hook/global restoration,
guards, allocation free, and checkpoint restoration. FlashRAM remains blank and
the Controller Pak unchanged. That fixture uses debugger-loaded code/resources;
the separate resident-loader fixture verifies actual cartridge loading.

The loader supplies cartridge loading, allocation-failure handling, resident
sticky-state ownership, and the submission-gate connection. Pending-loop
behaviour, normal delivery/read/edit and save flows, semantic approval, and
hardware validation remain. This API alone
does not enable ordinary gameplay generation.
