# Post-office reward: source review

## Verified donor

The complete pinned REL and symbols pass `verify_sources`. The actual
`l_mml_postoffice_info` resource at data offset `9178` contains four 16-byte
records: template u32, gift u16, paper u16, received-flag u32, balance u32.
Its 64-byte SHA-256 is
`d243cdb56951f56246bdede24c0b50b568b633eae9edcea539e0388fafefa648`.

| Template | Gift | Paper | Flag | Balance |
| --- | --- | --- | --- | ---: |
| `0246` | `1FB0` | `2000` | `04` | 1,000,000 |
| `0247` | `1FAC` | `2000` | `08` | 10,000,000 |
| `0248` | `3294` | `2000` | `10` | 100,000,000 |
| `0249` | `3020` | `2000` | `20` | 999,999,999 |

The mailbox is the third milestone, not an ordinary random postal gift.
`mMl_send_postoffice_mail`, text offset `4CE5C`, is 268 bytes, SHA-256
`b6066e945f2c289ac475cfc5fbda66873432f42eb305419da3af1f40880e236f`.
The pinned `src/game/m_mail.c` implementation checks each of four non-null
players, considers rewards in order, and stops after the first eligible reward
attempt for that player. It sets the received flag only when mail submission
succeeds. `mMl_start_send_mail` calls this routine.

The donor's `Private_c` names bank-account offset `122C` and state-flags offset
`2348`. These are **not N64 offsets**. Native `PrivateInfo` is only `BD0` bytes,
and its partially named definition does not establish corresponding fields.
Do not copy donor offsets, assume unknown native bytes are free, reuse an
unreviewed received flag, or substitute lifetime earnings for savings balance.

## Native account route

The original Pelly owner at VROM `008A6C10`, RAM `809C3420`, matches the
7,680-byte cached disassembly input. Its 104-byte status function at
`809C3708..809C376F` has SHA-256
`69f4cd5494efd6f494ee3b322f24db809e8ef33e7c858dbc2727ddb0a3ebfd1c`.
The current ABI-386 cartridge retains these instructions unchanged, checked from
its actual owner. Its complete disassembly is
`build/v3-post-office-category-prepared-03/native-pelly/code.asm`. The function
sets the mail-queue bit and, when the first-job check permits it, tests the loan
at `Now_Private + 3C` before setting the repayment bit. It has no bank-account
branch corresponding to the donor's `aPG_set_post_status`.

The pinned native submenu enum ends at catalogue entry 20; the donor adds music
at 21 and banking at 22. The donor Pelly constructor enables banking for a native
resident whose loan is paid, whose house size is at least three, and whose house
is not being renewed. The donor deposit path opens that added bank submenu.
Native repayment is not an existing equivalent of this savings route. These
facts establish a missing player-facing banking path, not that every unknown
native save byte has been identified.

## Connected category preparation

`tools/v3_post_office.py` prepares the shared category from the checked current
lock at `build/v3-holiday-card-prize-imports-01/password-destinations/build-lock.json`.
The complete preparation is `build/v3-post-office-category-prepared-04/`.
All sixteen bank functions, five Pelly owner functions, 55 conversation/action
functions, and the complete milestone function/resource have donor receipts.
Six complete bank numerical functions compile through a scoped source view:
initialisation, money-bag totals, digit selection, amount display, controller
input, and final redistribution. The complete frontend preparation below also
compiles the ten remaining frontend/lifecycle functions. A source view is not a
native struct; no native offset is inferred from its layout.

`overlays/v3/bank_account.c` owns a 48-byte, endian-neutral `AFBA` record:
a sixteen-byte header and four eight-byte rows. Each row has a big-endian balance,
the source receipt bits `04/08/10/20`, and three zero reserved bytes. Header byte
eight records required account support. Player clearing affects only its row and
does not remove that support requirement. The full saved-town owner below owns
this record in source; installation in the current cartridge remains pending.

The account transaction runs the complete donor controls and transfer algorithm,
including all four money-bag denominations, condition-aware pockets, withdrawal
capacity, account cap, crossing the opening balance, and B/Start/A priority.
Preview and cancellation do not write the account or inventory. Confirmation
requires the same player, balance, receipts, wallet, and pocket snapshot, and
checks total Bells before publishing. Unknown items and protected conditions
remain untouched. Sound requests are returned to the future frontend, never
played by a host check.

The shared reward driver reads all four actual source rows. Optional selection
filters unsupported gifts before the first eligible attempt. Each non-null
player gets at most one attempt per invocation, including a failed queue receipt;
only exact submission success sets its source bit. A scoped guard rejects
re-entrant account mutation during submission. Native identity, template
creation, mailbox/post-office submission, and scheduling are not yet bound.

Two focused checks pass: complete-source/generated-resource comparison and a
sanitized C transaction fixture using the actual generated donor functions.
The fixture covers four-player ownership, record rejection, all money bags,
protected pockets, cancellation, capacity/cap limits, stale-state refusal,
first-attempt ordering, null players, excluded rewards, queue failure/retry,
exact-success-only acknowledgement, and re-entrant mutation rejection. The
numerical functions are real donor code; native inventory and mail I/O remain
unbound. MIPS compilation produces 4,760 code bytes and 68 BSS bytes. The
relocatable object still needs the ordinary native `memcpy`/`memset` bindings.
The numerical preparation alone does not install a frontend. No native gameplay,
physical persistence, or hardware result is claimed.

### Complete frontend and checked native adapters

`tools/v3_bank_frontend.py` prepares all sixteen complete bank functions and the
three complete source integer-formatting functions at
`build/v3-post-office-bank-frontend-prepared-20/prepared.json`. It retains the
genuine title, OK label, complete frame, cash/Bell/balance labels, and complete
128-by-32 deposit/withdrawal textures. The shared UI converter preserves both
source CI palette slots and checked tile-one replacement without overwriting
the tile-zero background. Seven official-text/bitmap entries are checked in the
single provenance catalogue. The 24,224-byte art packet has SHA-256
`fa557558e2619f18bd64dd59e5a9337e5ef1c0c0098e64af80f6935752153de8`.
Strict `--reuse-art` comparison reuses the complete unchanged packet and drawing
receipts; this preparation does not reconvert artwork.

`overlays/v3/bank_frontend_source.c` wraps actual donor Play dispatch in the
existing checked transaction. A refused native commit restores preview state
without closing or mutating the live wallet/account. Complete source drawing and
lifecycle dispatch use explicit native motion/font/matrix services, checked
phase/position values, graph headroom, and re-entry guards. The compiled donor
formatter avoids substituting the incompatible native formatter ABI. The
native integer string-width return is converted explicitly for the donor view.

`overlays/v3/bank_native.c` reads actual N64 pockets at `14`, packed conditions at
`34`, and wallet at `38`, never a cast of the source view. It rejects stale
snapshots and protected-item changes before the reviewed native pocket setter
and account publication. Loan `3C`, unused packed-condition bits, receipts, and
other residents remain unchanged. Banking requests may own repayment submenu
seven only explicitly; an unowned request leaves original repayment untouched.
The adapter uses verified native menu/callback offsets and passes the actual
game argument to the original pre-draw callback. An owned construction failure
must reject the bank path, not fall through into repayment.

`overlays/v3/bank_admission.c` checks the actual resident, paid loan, matched
sixteen-byte personal/home identity, house-arrangement byte, largest native
house size, and renovation bit. Complete native house-arrangement, home-pointer,
and renovation-owner guards establish these distinct fields. The donor requires
size three (its upper-floor house); the native house upgrade owner provides floor
sizes zero through two and treats next-size three separately. The GameCube bank
mode therefore admits the completed largest native house (size two), with no
loan or renovation. This platform adaptation must be stated in the eventual
N64/GameCube bank choice; N64 mode keeps banking disabled. No upper-floor building
or guessed house field is introduced.

`tools/v3_post_office.py` also compiles sixteen complete Pelly conversation
functions, including greeting, business selection, status, deposit, menu waiting,
closing balance display, and recovery/continuation. The source declaration's
eight-byte balance buffer is corrected to the formatter's actual eleven-byte
output. `overlays/v3/bank_pelly_native.c` uses the actual N64 actor fields and
submenu/open flag, not the GameCube layout. Source bank actions 24–28 map to
additive native actions 33–37; existing native letter/card actions at 24–28 remain
intact. Non-bank choices return to the original native setup callback. Banking
status stays in the borrowed view, avoiding the original native four-row status
tables. A resident change or actor release requests ordinary bank closing without
publishing a preview. Menu ownership lasts until the real native destructor;
cancelled pending construction returns an owned failure, never original repayment.

Whole current repayment-owner/relocation guards and nine whole native service
guards pass. Four focused frontend checks pass: complete donor/generated/art
comparison with reuse/provenance, current native contract and mutation rejection,
sanitized source lifecycle/transaction/drawing, and sanitized native-menu/pocket
adapters, now including the complete Pelly route, greeting variants, largest
balance, house/identity/renovation admission, stale residents, action restoration,
and pending/active cancellation ownership. Complete Pelly-owner/relocation and
house-service guards also pass. Native callbacks, menu opening, and pocket services
are doubles in these host tests; this is not native execution. The two original
numerical checks pass against unchanged generated numerical functions. The two
affected diary resource/state checks retain passing unchanged evidence.

The current combined MIPS preparation and complete packet are described below.
Native services, shared saved ownership, source April callbacks, art roots, and
configuration storage have real linked addresses. Calendar/actor registration
and cartridge menu/save ownership remain unfinished. No native bank harness
starts and no existing harness budget resets. The current ABI-386 ROM, format
20/wire 7, selections, and both patcher deployments are unchanged.

### Official dialogue and saved account owner

`tools/v3_bank_dialogue.py` prepares all twelve complete official bank greeting,
continuation, deposit, and balance messages plus four official choices at
`build/v3-post-office-bank-dialogue-01/dialogue.json`. Additive native message IDs
are `33B2..33BD`; choices are `0220..0223`. Wording, pages, pauses, and source demo
orders are retained. The largest expanded message is 183 bytes. Every existing
message and choice remains intact. Eight checked native mail/Pak/exit destinations
retain their exact current text and action identities, including the N64
Controller Pak letter-save interaction instead of the GameCube Memory Card menu.
The single provenance catalogue contains exact official-source credits for all
sixteen additions. The generated bidirectional map is compiled into preparation
14; its complete source Pelly host check uses that map, not arithmetic message
IDs. Actual text-bank installation/bounds and native services remain pending.

`AF_V3_BANK_STORAGE` connects `AFBA` to `console_storage.c` and
`save_compressed.c`, including ordinary pack/check/adoption, diary capacity
preflight, player deletion, town reset/change, and `af_bank_native_account`.
The account allocation is independent of native player padding and card bytes.
Format 21 appends 48 bytes after the complete 64-byte format-20 card record;
the card wire remains seven. CRCs and capacity measurement include the new tail.
Older compressed/canonical towns and format-14..20 envelopes initialise empty
accounts while retaining their existing data. Account-support requirements
survive deletion of all residents. Removing banking rejects a required-account
save before caller state, live accounts, or device writes change.

`tools/v3_bank_storage.py` checks a separate 64-byte account/guard reservation at
`807E9080..807E90BF` against all retained owners. Save scratch at `80682000`
requires 120,416 bytes including its existing sixteen-byte guard, an increase
of exactly 48 bytes. These reservations are checked preparation, not installed
memory. MIPS compilation requires an explicit account reservation; the existing
event-storage linker still forbids unowned data/BSS growth.

Nine focused bank/frontend/dialogue/account/storage checks pass. Actual MIPS
storage compilation retains every current format-20 compiler define. Sanitized
full-town host checks cover both banking modes, both physical-bank reads with
device I/O doubled, all four residents, maximum balances/receipts, probe-only
reads, adoption, deletion, new towns, formats 14–20, older compressed/canonical
migration, required-mode rejection, guard corruption, and capacity preflight.
The unchanged format-20 golden/card transaction also passes in both paper modes.
No emulator bank/save or original-hardware verification is claimed.

**Compatibility warning for the prospective installation:** supported older
saves migrate forward with empty bank accounts. Format-21 saves cannot be loaded
by format-20-or-earlier V3 or V2 readers, even when banking is disabled. A save
requiring banking also needs banking enabled in its current profile. Preserve
separate saves and builds; ordinary forward/backward compatibility is unverified.
The current format-20 cartridge and existing saves are not modified.

### Queued opening and native lifecycle entry plan

Native `mSM_open_submenu` at `800C4D8C` calls `800C4DD8`, which queues the
program/arguments without changing the open flag. Both complete service bodies
have hash guards. Pelly holds its menu-wait action while the owned queued program
awaits ordinary linking. Pending cancellation remains an owned rejection. An
admitted construction that fails or sees a stale resident installs closing-only
callbacks; subsequent native set-proc cannot reinstate repayment. Native closing
queues status zero/next four; the rejection handler advances ordinary slide-out
motion before invoking the end callback. The native
destructor releases ownership before its original cleanup. Host fixtures retain
the actual delayed opening rather than raising the flag inside the opening double.

`overlays/v3/bank_entries.c` provides all six resident lifecycle wrappers:
menu construction/destruction/set-proc and Pelly business/greeting/destruction.
Original menu construction supplies the native common callbacks and retained
numerical state without a wallet/loan transfer. Unrequested menus still run
ordinary repayment. Greeting refreshes actual native mail/loan status before
adding banking only to its borrowed source view.

`tools/v3_post_office_install.py` prepares the complete native consumers together.
Appended local shims pass relocated original function pointers, not nominal
overlay RAM addresses, to the resident wrappers. Original code, data, BSS, and
local fixups remain; the full native Pelly business/process, greeting callback,
and destructor destinations are connected. Repayment's complete descriptor
points to its local lifecycle shims. Its aligned allocation requires 64 additional
submenu bytes, retaining the current complete arena contribution rather than
replacing earlier growth. Whole owner/relocation guards and comparisons at two
load addresses preserve every unrelated loaded byte, including the common menu.

Eleven current frontend/dialogue/entry/packet checks pass, with sanitized native-I/O
doubles and exact original-function/entry-address checks at both load bases.
Entry-plan tests use distinct fixture destinations and actual linked packet
entries; no installed cartridge is implied. The compiled frontend reuses the
complete art packet.
The unchanged saved-town and numerical evidence remains retained. Native
banking, physical save I/O, ordinary gameplay, and hardware are unverified.
The enlarged owners still require ordinary VROM/physical resource relocation,
Pelly's complete allocation descriptor, and startup transfer ownership.

### Checked services and shared saved-object bindings

The complete prepared MIPS object is
`build/v3-post-office-bank-frontend-prepared-20/post-office.o`, SHA-256
`fd526b9c5b59e1cdb412551308fba618e2fb82d443748c47d2f81deac61a1c23`.
It contains 37,057 text/constant bytes, 118 data bytes, and 1,076 BSS bytes before
final layout. These object dimensions do not prove a final memory allocation.
The 24,224-byte artwork packet is reused without conversion. The object binds
42 real native APIs/globals and 23 retained saved-owner services; linker bindings
only resolve genuine undefined references and never override compiled definitions.
Every fixed native service has a complete body guard. The actual message-number
getter is `8009DBB0`, not the continuation-terminal check at `8009DD8C`.

The setter entry `8009D6D0` contains a one-shot loader in the cartridge. Its
entire loader, actual owner CRC, complete 4,032-byte extended-text owner, and
retained sixteen-byte setter initialization are checked before binding it.
The 11-character balance therefore uses the installed extended field provider,
not the original ten-character setter. Native message selection at `8007B5C0`
has a complete 52-byte guard and retains its real redirect to the installed
6,096-byte shared announcement owner. The actual resident owner and destination
are checked in their current physical packet; an obsolete native body is not
restored or substituted.

All sixteen selected Pelly functions compile, including the complete donor loan
formatter and complete source message-length helper. Its two-byte decompiler
local is corrected to the declared seven-byte loan field without changing source
operations or either message field. Sanitized source checks cover both split
fields at 100, 999,999, 1,000,000, and 999,999,999 Bells. No external loan stub
is needed.

The same object includes the full town/console/diary/card/golden saved owner and
format-21 codec, preserving every current storage compiler define and the checked
separate account/scratch reservations. Its account provider and save operations
resolve to this object's single account/transaction implementation. No second
account busy flag or synthetic account-function addresses are linked. This is
combined MIPS compilation; its final linked placement is described below.
Cartridge save installation and fresh native persistence evidence remain absent.

### Complete April callbacks and bounded final packet

`tools/v3_bank_april.py` compiles the complete six-function source controller,
eleven NPC identities/messages, and full four-pointer clip. The bank uses a
distinct two-callback borrowed view, never a cast of the larger clip. The adapter
maps source event 17 to reserved additive type 115, checks its real native daily
row, and uses the genuine five-slot event cache. Each native slot has an eight-byte
header and forty-byte payload; the four source talk bitfields occupy eight
payload bytes, not private saved padding or another account record. All five
native services have whole-body guards, including the actual expanded-index/day
addresses read by reservation.

Construction preflights allocation before the donor constructor's unchecked
clear. Inactive/unregistered/error rows, wrong dates, exhausted slots, changed
cache ownership, and stale/invalid residents cannot expose callbacks. Existing
saved talk flags survive reconstruction; deletion clears only the selected row.
Calendar registration, actual actor creation/destruction, personal deletion, and
official April message installation remain unbound. The source-numbered profile
is provenance data, not a native registration; install the guarded lifecycle
wrappers. Sanitized tests cover all eleven identities/messages for all four
residents, visitor suppression, repeat talk, allocation failure, reconstruction,
and actual Pelly/Phyllis source greeting calls. Phyllis uses `D012`, not the
borrowed view's incorrect `D004`. Native event I/O remains doubled.

`tools/v3_bank_link.py` fully links the combined bank/save/controller packet at
`807D8040..807E8040`, rejecting every retained-memory overlap. The original
unbound objects must reproduce the authenticated partially bound preview; fixed
native services are then applied only once. Re-linking the preview itself would
apply absolute MIPS call addends twice and overflow call relocations. No
truncated-relocation warning is ignored or bypassed.

`build/v3-post-office-bank-linked-02/linked.json` owns the complete 65,536-byte
packet, SHA-256
`55201c6e81d29c4405d62abd9a3f2c22183d6261b3e0a1cab3e8f4cbf15e928b`.
Initialized code/data occupies 37,168 bytes, SHA-256
`6bb88c3d1aa9ab446e59793de89bd21c453a28b98388f326c16229b3e5bea390`.
Complete code/state uses 38,256 bytes; BSS `807E1170..807E15B0` is zeroed in the
packet. The owned mode byte at `807E15A4` initially retains N64 mode, without an
installed profile control. Code and art each have a sixteen-byte guard.

All 24,224 prepared art bytes are reused. The 51 texture/palette/vertex pointers
relocate to physical packet addresses without taking native segment six or
changing resource contents. Linked art SHA-256 is
`05678195fb0197779738bdc9d6184f6163183179a2f592f3ab73eead1c26f595`.
All six native Pelly/menu entry shims use actual linked functions. Two packet
checks verify full resources, pointer bounds, collision rejection, initialized
state/guards, original-object matching, and the complete native entry plan.
These are not native rendering or gameplay/save evidence. Startup transfer and
enlarged resource relocation, text/full saved-owner redirects, April native
lifecycle, real mail scheduling, and profile controls remain required. Failed
preparation `19` and final link `01` retain their diagnostics; preparation `20`
and linked packet `02` are current.

## Remaining connected consumers

Implement a real deposit/withdrawal route and reviewed per-player saved balance
and reward acknowledgement before enabling the savings milestone. Preserve
the loan-payment route and the donor's account eligibility. Bind actual native
money transfers, save ownership, and ordinary mail scheduling before changing
them. Unknown saved fields are not available storage without review.

Extract and integrate the complete English `0248` reward template, preserving
town/player fields, its genuine sender, paper mapping, and attached `3294` ID.
Keep selected-profile gating, successful-delivery-only acknowledgement, full
queue retry, and one-time persistence. The existing catalogue-order/ticket
wrapper in `POST_OFFICE_LETTERS.md` is not this savings-reward mechanism.

Install the prepared complete bank/Pelly route, preserving repayment and the
reviewed resident/loan/house/renovation admission. Bind source April event 17 as
additive native type 115 without shifting retained identities. Connect actual
April 1 calendar admission, manager start/stop, guarded actor construction and
destruction, personal deletion, and complete official Pelly/Phyllis messages.
Then attach the linked packet's startup transfer and native resource relocation,
followed by text-bank and full
saved-owner installation, using the prepared native entry planner,
official dialogue and account provider above. Bind the
compiled selection/admission adapters and checked wallet/pocket services only
through reviewed owners. Retain the checked complete packet and guards. Attach
the format-21 saved owner and its checked account/scratch reservations to all
current save entry points, retaining forward migration, complete existing
card/golden/console/town data, and older-reader rejection. Do not discard balances
or remove the required banking profile when installing the compiled providers.
Publish real mechanic controls and independent milestone selections only after
these native owners and the actual mail delivery/acknowledgement path are installed.

All four gift models/behaviours are already complete. The three staged savings
items reuse their installed banks; the existing mailbox retains its complete
runtime, scoring, catalogue exclusion, and profile. Artwork installation is not
reward delivery. Both patchers remain stable V2-14.

The current staged acquisition map has 23 entries; use this map rather than
rescanning unrelated conversion categories:

| Source route | Complete staged entries | Current source evidence |
| --- | --- | --- |
| Savings | post model, piggy bank, tissue | `ftr_listPostoffice`, complete milestone owner/table; mailbox is also a milestone consumer |
| HRA | house model, manor model | `mMkRm_DecideLetterNo`, source 70,000/100,000-point thresholds and successful-mail flags |
| Museum reward | museum model | Source birth category 29; complete donor museum delivery needs a real native policy |
| Mayor lighthouse quest | lighthouse model, chocolates | Source birth category 30; not ordinary event-table gifts or fabricated Valentine stock |
| Special presents | Ice Climber, Mario Bros, Super Mario Bros, Legend of Zelda | Complete `ftr_listSpecialPresent` |
| Island | nine furniture rewards, Baseball, Wario's Woods | Complete `ftr_listIsland` and `ftr_listIslandFamicom`; absent-system policy remains explicit |

The Museum building remains V4; preparing its model does not authorise building
that facility or inventing a replacement reward. Island acquisition needs an
explicit choice for its absent system. These decisions do not block connecting
the real post-office account and other established native mail routes.
