# Three replacement instructions, in patch-table order (not contiguous code).
# The native handler already completes the quest and queues the advice. Leave
# its dispatcher in WAIT_NOTHING so English continuation pages cannot repeat it.
.set noreorder
.set noat
.text
.globl af_first_job_reward_words
af_first_job_reward_words:
    addiu $t6, $zero, 11          # 8091D2E0: WAIT_NOTHING
    sb    $t6, 0x186($s0)        # 8091D2E4: manager->talk_step
    lw    $a1, 0x1d4($s0)        # 8091D320: item index, directly from manager
