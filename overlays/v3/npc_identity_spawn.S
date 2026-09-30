/* Shared registry lookup for both NPC controllers. Their ABI permits only
 * at/t1 to change, takes the special name in v1, and returns at original sp+56.
 * Preserve the original row pointer in t1 on every unmatched path. */
#include "npc_registry_limits.h"
.set noreorder
.set noat
.set nomacro
.text
.globl af_npc_identity_spawn
af_npc_identity_spawn:
    addiu $sp,$sp,-16
    sw $t0,0($sp)
    sw $t2,4($sp)
    lui $t0,%hi(af_v3_npc_extras)
    addiu $t0,$t0,%lo(af_v3_npc_extras)
    lw $t2,0($t0)
    lui $at,0x4146
    ori $at,$at,0x4e58
    bne $at,$t2,3f
     nop
    lw $t2,4($t0)
    addiu $at,$zero,1
    bne $at,$t2,3f
     nop
    lw $t2,12($t0)
    addiu $at,$zero,44
    bne $at,$t2,3f
     nop
    lw $t2,8($t0)
    sltiu $at,$t2,AF_NPC_EXTRA_CAPACITY+1
    beq $at,$zero,3f
     addiu $t0,$t0,16
1:  beq $t2,$zero,3f
     nop
    lhu $at,0($t0)
    beq $at,$v1,2f
     addiu $t2,$t2,-1
    b 1b
     addiu $t0,$t0,44
2:  lhu $t1,2($t0)
    lw $t0,0($sp)
    lw $t2,4($sp)
    addiu $sp,$sp,16
    jr $ra
     sh $t1,0x56($sp)
3:  lw $t0,0($sp)
    lw $t2,4($sp)
    addiu $sp,$sp,16
    j af_npc_previous_spawn
     nop
