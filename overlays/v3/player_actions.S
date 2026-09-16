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

#ifdef AF_V3_HELD_SELECTION
/* The native selector has already read the real or title-demo item into v1.
   Retain its original switch for the first 36 IDs. Its 24-byte stack frame
   supplies ABI call space and the original return address. */
.section .text.af_v3_player_equipment_select,"ax",@progbits
.globl af_v3_player_equipment_select
.ent af_v3_player_equipment_select
af_v3_player_equipment_select:
    sltiu $at, $t7, 36
    bnez $at, 2f
    li $v0, -1
    jal af_v3_player_selected_equipment
    move $a0, $v1
    lw $ra, 20($sp)
    jr $ra
    addiu $sp, $sp, 24
2:
    lui $t9, 0x808B
    ori $t9, $t9, 0xD43C
    j af_v3_player_action_t9
    nop
.end af_v3_player_equipment_select

/* This branch runs only after the native scene, hidden-item, force-visible,
   and all-items rules. Extend the passive-item rule without bypassing them. */
.section .text.af_v3_player_equipment_passive,"ax",@progbits
.globl af_v3_player_equipment_passive
.ent af_v3_player_equipment_passive
af_v3_player_equipment_passive:
    sw $a1, 24($sp)
    jal af_v3_player_passive_equipment
    move $a0, $a1
    lw $t0, 24($sp)
    bnez $v0, 3f
    li $v0, -1
    li $t0, -1
3:
    move $v0, $t0
    lw $ra, 20($sp)
    jr $ra
    addiu $sp, $sp, 32
.end af_v3_player_equipment_passive
#endif
