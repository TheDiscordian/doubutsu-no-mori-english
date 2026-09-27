.set noreorder
.set noat
.text
/* Each entry is called from a checked instruction span in the native owner.
 * Return-address differences track its actual relocated base; no heap address
 * is assumed. The installer must remove the replaced owner's relocations. */
.globl af_insect_hook_ctor
.type af_insect_hook_ctor,@function
af_insect_hook_ctor:
    addiu $sp,$sp,-32
    sw $ra,28($sp)
    sw $a0,24($sp)
    addiu $t9,$ra,0x748        /* original clip init: 109A4 - 1025C */
    jalr $t9
    nop
    jal af_v3_insect_bind_controller
    lw $a0,24($sp)
    jal af_v3_insect_spawn_reset
    nop
    jal af_insect_colony_reset
    nop
    lw $ra,28($sp)
    jr $ra
    addiu $sp,$sp,32

.globl af_insect_hook_dtor
.type af_insect_hook_dtor,@function
af_insect_hook_dtor:
    addiu $sp,$sp,-32
    sw $ra,28($sp)
    jal af_v3_insect_unbind_controller
    lw $a0,0x13E8($ra)        /* native controller global: 11690 - 102A8 */
    jal af_insect_colony_reset
    nop
    lw $ra,28($sp)
    addiu $t9,$ra,0x768       /* original clip destructor */
    jalr $t9
    nop
    lw $ra,28($sp)
    jr $ra
    addiu $sp,$sp,32

.globl af_insect_hook_init
.type af_insect_hook_init,@function
af_insect_hook_init:
    lw $t6,0x1CC($s0)
    sltiu $t7,$t6,32
    beq $t7,$zero,1f
    nop
    /* Replay the complete two-table lookup, including both relocated HI/LO
     * pairs. Replaying only their original LUI words would use the wrong base. */
    addiu $v1,$ra,0x12B8      /* native program-type table */
    sll $t7,$t6,2
    addu $v1,$v1,$t7
    lw $v1,0($v1)
    addiu $t9,$ra,0x1218      /* native program descriptor table */
    addiu $ra,$ra,0x14
    jr $ra
    nop
1:
    addiu $sp,$sp,-32
    sw $ra,28($sp)
    move $a0,$s0
    jal af_v3_insect_init
    lw $a1,0x94($sp)         /* native setup frame's saved game at +74 */
    addiu $t0,$zero,1
    bne $v0,$t0,af_insect_hook_fault
    nop
    lw $ra,28($sp)
    addiu $ra,$ra,0x74       /* skip the original bounded program table */
    jr $ra
    addiu $sp,$sp,32

.globl af_insect_hook_slot
.type af_insect_hook_slot,@function
af_insect_hook_slot:
    lw $t6,0x1CC($s0)
    sltiu $t7,$t6,32
    beq $t7,$zero,2f
    nop
    lw $t7,0x20($s0)
    jr $ra
    lui $at,0xFEFF
2:
    addiu $sp,$sp,-32
    sw $ra,28($sp)
    move $a0,$s0
    jal af_v3_insect_slot
    move $a1,$s4
    addiu $t0,$zero,1
    bne $v0,$t0,af_insect_hook_fault
    nop
    lw $ra,28($sp)
    addiu $ra,$ra,0x188      /* next slot; imported culling is already done */
    jr $ra
    addiu $sp,$sp,32

.globl af_insect_hook_end
.type af_insect_hook_end,@function
af_insect_hook_end:
    addiu $sp,$sp,-32
    sw $ra,28($sp)
    jal af_insect_controller_end
    move $a0,$s4
    lw $t9,28($sp)
    addiu $sp,$sp,32
    lw $ra,0x54($sp)         /* restore the native caller, not this hook */
    ldc1 $f20,0x20($sp)
    jr $t9
    nop

af_insect_hook_fault:
    break 7                  /* invalid imported identity/owner: fail closed */
    b af_insect_hook_fault
    nop

/* Set_Manager loads the insect manager into actor+178. Replay the two
 * displaced prologue instructions, then continue the real original manager.
 */
.globl af_insect_spawn_original
.type af_insect_spawn_original,@function
af_insect_spawn_original:
    addiu $t9,$a0,(0x178+0x8092AF14-0x8092A030)
    addiu $sp,$sp,-64
    jr $t9
    sw $ra,36($sp)
.size af_insect_spawn_original,.-af_insect_spawn_original

/* Pull-net setup must identify a colony before its next background update
 * transfers the catch label to an individual ant. Native bees retain index 8. */
.globl af_insect_hook_net_index
.type af_insect_hook_net_index,@function
af_insect_hook_net_index:
    addiu $sp,$sp,-32
    sw $ra,28($sp)
    sw $a0,24($sp)
    lb $a1,0xE6C($a0)
    lw $a2,0xF24($a0)
    jal af_insect_net_index
    lw $a0,0xE68($a0)
    move $v1,$v0
    lw $a0,24($sp)
    lw $ra,28($sp)
    jr $ra
    addiu $sp,$sp,32
.size af_insect_hook_net_index,.-af_insect_hook_net_index

/* Retain the existing tree query's a0-preserving contract. Native seasonal
 * callers still use that item in their ordinary drop/bee path after this call.
 * Tile coordinates are still live in a1/a2 at all four guarded call sites. */
.globl af_insect_hook_tree
.type af_insect_hook_tree,@function
af_insect_hook_tree:
    addiu $sp,$sp,-32
    sw $ra,28($sp)
    sw $a0,24($sp)
    jal af_insect_player_tree
    nop
    lw $a0,24($sp)
    lw $ra,28($sp)
    jr $ra
    addiu $sp,$sp,32
.size af_insect_hook_tree,.-af_insect_hook_tree
