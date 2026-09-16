/* The extended tables retain native linked pointers, not stale heap pointers.
   Resolve them against the actual loaded player owner at every dispatch. The
   call-register variants preserve arguments, stack, and the caller's RA.
   t0/t1/t9 are caller-saved. Imported callbacks already use resident addresses. */
.set noreorder
.set noat
.section .text.af_v3_player_action_v0,"ax",@progbits
.globl af_v3_player_action_v0
.ent af_v3_player_action_v0
af_v3_player_action_v0:
    move $t9, $v0
.globl af_v3_player_action_t9
af_v3_player_action_t9:
    lui $t0, 0x808B
    ori $t0, $t0, 0x2D50
    subu $t1, $t9, $t0
    lui $t0, 0x0002
    ori $t0, $t0, 0xAF00
    sltu $t0, $t1, $t0
    beqz $t0, 1f
    nop
    lui $t0, 0x8014
    lw $t0, 0x3900($t0)
    /* Constructor offset: 808DD748 - 808B2D50 = 2A9F8. */
    lui $t9, 0x0002
    ori $t9, $t9, 0xA9F8
    subu $t0, $t0, $t9
    addu $t9, $t0, $t1
1:
    jr $t9
    nop
.end af_v3_player_action_v0

/* Held-item main dispatch uses v1; retain both existing entry addresses. */
.section .text.af_v3_player_action_v1,"ax",@progbits
.globl af_v3_player_action_v1
.ent af_v3_player_action_v1
af_v3_player_action_v1:
    move $t9, $v1
    j af_v3_player_action_t9
    nop
.end af_v3_player_action_v1
