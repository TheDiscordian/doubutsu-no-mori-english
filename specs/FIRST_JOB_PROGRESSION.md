# First-job furniture conversation progression

## Defect and correction

The native first-job dispatcher retains reward step seven after granting the
delivery reward and selecting the complete-end advice. Native advice ends with
`00`, so the ordinary wait does not dispatch that step again. Complete English
furniture advice needs extra message records for lazy, cranky, and snooty
residents. Their intermediate `01` endings trigger the ordinary wait, which
dispatches step seven again, queues another handoff, and replaces the explicit
English continuation with the advice's root message. This prevents completion
of the whole conversation, not merely correct reward counting.

Advance the reward handler to the existing no-operation step eleven. The first
reward still clears quest progress and recipient identity, writes the same item
to the same inventory slot, requests the native takeout animation, and selects
the same personality-specific advice. Subsequent English continuation boundaries
dispatch no operation: the text's explicit next record remains selected. Final
`00` uses normal conversation closure and the quest manager's existing cleanup.

## Native patch ownership

The exact native owner is VROM `00814FA0`, linked RAM `8091CB30`, with unchanged
2,864-byte file, 176-byte BSS, 160-byte relocation file, and allocation bounds.
Three instructions change:

| Address | Native operation | Replacement |
| --- | --- | --- |
| `8091D2E0` | Read manager inventory index into `t6` | Set `t6` to step eleven |
| `8091D2E4` | Save inventory index at stack `24` | Store step at manager `186` |
| `8091D320` | Read inventory index from stack `24` | Read manager index at `1D4` |

Between the old and new inventory-index read, the handler clears registered
quest progress and calls `mNpc_ClearAnimalPersonalID` on that quest's recipient.
Neither modifies the manager's target inventory index. The live manager and
registered quest/recipient are distinct objects. The same register and argument
reach the unchanged inventory writer. No change depends on a caller-clobbered
register surviving a call. All jumps, relocation entries, stack frame size,
other owner handlers, dialogue records, and persistent formats remain unchanged.

## Related letter-advice completion

The post-letter-view handler at `8091D484` completes the quest and selects
`0908 + looks*2`. Its native complete-end message uses `00`. Added English
continuations `0910 → 0A26` and `0912 → 2B47` can instead dispatch its pending
step twelve, which clears all talk information and then sets the continuation
to the cleared message number zero. This loses the remaining advice and leaves
the intended tutorial conversation. It is a separate consequence of the same
added actor-visible message boundary.

The `letter_advice` variant changes only `8091D4C8` from `addiu t0, zero, 12`
to `addiu t0, zero, 11`. After completing the quest and reopening the message,
the owner waits without prematurely clearing it. Normal conversation closure
retains the existing shared cleanup. The letter viewer, letter storage, quest
completion, appearance request, selected root, and every English word remain.
The combined owner changes four instructions in total; its allocation is still
the exact native size.

## Focused verification

Independently assemble the three instructions, reject changed source/owner
identities, check complete relocation at two heap bases, retain every other
installed v0 resource, and reconstruct the complete ROM from the UPS patch.
Native owner verification must reproduce the original continuation overwrite,
then execute the corrected dispatcher and its full remaining English records
through final termination. Verify one handoff request, unchanged delivered item,
completed quest state, buffer and heap guards, and restored isolated checkpoint.
Synthetic owner fixtures do not establish normal actor animation, walking back
to Nook, ordinary saving, or original-hardware acceptance of the correction.
