# Mail metadata and selected storage paths

## Scope

The experimental split marker is separate from font/status, mail type, paper,
gift, and identities. `tools/audit_mail_storage.py` verifies eight complete
native functions and inventories their direct calls and aligned literal
pointers. `tools/mail_storage_test_scenario.py` exercises selected native paths
with both classic and composite catalog snapshots in a matching-ROM isolated
town. Neither audit is an exhaustive inline/computed-pointer reader proof.
Generation and release/save compatibility remain disabled or unproven.

## Status fields

The predicates at `8009C414`, `8009C89C`, and `8009C8C0` read only the font/status
byte at `Mail_c+26`. An unused slot has value `FF`; sending accepts one; attaching
a gift accepts one, three, or four. The snapshot split at `Mail_c+27` is not
consulted. Native tests compare ordinary split zero and snapshot split `80`
across nine status values, verifying all three predicate returns and unchanged
complete records. This is not a statement that every possible status is suitable
for generated mail; native metadata meaning must remain unchanged.

## Opaque record transfer

`mNpc_Mail2AnimalMail` preserves the full 122-byte text envelope, split, status,
gift, and paper. Its reverse preserves those same fields, but does not copy the
mail-type byte and only sets identities when supplied explicit identity inputs.
Callers still own those fields. The compact record's trailing date/padding is
not written by these conversion routines.

The native post-office queue begins at `80135E0C` with five 164-byte records.
The keep helper at `800B67C0` copies to the first free slot and clears its source
only on success. A full queue leaves the source intact. This helper alone does
not adjust receipt counters; the caller owns those updates.

The public receipt function's modes one and two copy to the distinct leaflet
records at `80136140` and `801361E4`. Only the corresponding sixteen-bit delivery
flag at `80136288` or `8013628A` is cleared. These modes retain their source.

The home-mailbox copy helper at `800B6AC8` uses ten 164-byte slots per home.
The first array is at `8012A8A0`, with home stride `B48`. It copies to the first
free slot, retains the source, and returns failure without changes when full.
Native tests cover every slot and the full condition for all four homes.
These are bounded native helper calls, not actual timed delivery or UI storage.

## Required Pelly failure handling

The lower-level [NPC receipt guard](MAIL_NPC_SEND.md) does not complete the
normal post-office interaction. The actor overlay at VROM `008A6C10`, linked
`809C3420`, contains a second unconditional-clear path:

1. `809C47C0` calls `mPO_receipt_proc` for the staged submenu letter.
2. `809C47C8..809C47D8` ignores the return, selects the successful receipt action,
   and branches to the common clear.
3. `809C4828` clears that staged letter, including when lower-level delivery fails.

The existing destination-refusal path at `809C47DC..809C4820` copies the letter
back to the selected player slot before clearing the staged copy. Its slot byte
is at submenu offset `DF`; the player-mail array is at current-private offset
`40A`. It resets status to one but does not normalize the split or text.

This failure path is **unfixed**. A complete fix must return a rejected staged
letter safely, propagate failure into the actor's state/message choice, and
retain the successful receipt behaviour. It must not misreport a corrupt letter
as a full mailbox or a missing recipient merely to reuse an existing refusal.
Normal player-pocket removal and rollback ownership require verification too.
Native snapshot generation must remain disabled while this path is unresolved.

The complete receive-handler range `809C471C..809C4884` has SHA-256
`c29e3901cf539f63a16043228bccc787ec14fbf4a58613db350a06f9618b0e73`.
The source overlay has SHA-256
`a2fe6daee4180fd7fdcbe04cb62e514a8d88067b74bf7e43506f17986c204db6`.
The audit and mutation tests retain this outstanding requirement explicitly.

## Validation limits

The selected native storage run passes 140 cases, 217 function calls, and 267
assertions. It checks complete copied fields, source ownership, selected slots,
post-office flags, neighbouring memory, and stack/module guards. It restores
all touched storage arrays locally and then restores the complete machine
checkpoint. FlashRAM stays blank. Actual save/reload, Controller Pak travel,
normal inventory/storage interactions, other readers, and original hardware
remain required. Exact run identifiers and hashes belong in the work log.
