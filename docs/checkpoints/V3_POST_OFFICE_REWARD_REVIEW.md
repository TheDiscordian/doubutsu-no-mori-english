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
The ABI-64 garden cartridge retains these instructions unchanged. The function
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

## Next implementation checks

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

The other three donor gifts are not implemented by merely adding this table.
Review their identities and actual assets separately. Do not stop unrelated
donor conversion work while the account/reward integration is investigated.
The mailbox's runtime, scoring, catalogue exclusion, and profile are installed
in ABI 64; reward delivery remains unimplemented. Both patchers remain V2.
