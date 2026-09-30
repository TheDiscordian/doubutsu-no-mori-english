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
does not remove that support requirement. This record is prepared, not attached
to a live saved-town owner or installed in the current cartridge.

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
`build/v3-post-office-bank-frontend-prepared-09/prepared.json`. It retains the
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

`tools/v3_post_office.py` also compiles fifteen complete Pelly conversation
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

Whole current repayment-owner/relocation guards and seven whole native service
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

The combined relocatable MIPS object has 18,269 code bytes, 30 data bytes, and
1,056 BSS bytes, SHA-256
`7340e585f1fc74cfbeb2efd31d33cf9b523b660de6c002f4218f55de13937617`.
It is not linked or installed. Selection/home/current-player/account bindings,
official dialogue remapping, fixed message/menu services, April Fools control,
drawing roots, lifecycle hooks, and menu/save ownership remain unbound. No native
bank harness starts and no existing harness budget resets. The current ABI-386
ROM, format 20/wire 7, selections, and both patcher deployments are unchanged.

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
reviewed resident/loan/house/renovation admission. The exact next connections are
the official bank greeting/deposit/closing message and choice remapping, the real
saved-town account provider, and native menu/lifecycle installation. Bind the
compiled selection/admission adapters and checked wallet/pocket services only
through reviewed owners. Reserve and link complete code/state/art without assuming
the old packet's remaining space fits the larger frontend. Attach
`AFBA` to the whole saved-town transaction with a new supported envelope/wire,
forward migration preserving all existing card/golden/console/town data, player
deletion, town reset, preflight, and older-reader rejection. Account-required
saves must reject a build without account support rather than discard balances.
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
