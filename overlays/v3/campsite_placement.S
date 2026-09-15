/* Preserve each native lookup, including its delay-slot result. Only the new
 * tent needs an explicit class: GC class 10 is native class 8 (3x3, restore lot).
 * Do not index 5849 through the original 5800..5843 table: it is past its end. */
.set noreorder
.set noat
.set nomacro
.text
.globl af_v3_tent_set_class
af_v3_tent_set_class:
    addiu $at, $zero, 0x5849
    bne $t1, $at, 1f
     nop
    addiu $v1, $zero, 8
    beq $zero, $zero, 2f
     nop
1:  lbu $v1, 0x119c($v1)
2:  lw $t2, 0x64($sp)
    j 0x8008d4b0
     nop

.globl af_v3_tent_area_class
af_v3_tent_area_class:
    addiu $at, $zero, 0x5849
    bne $a2, $at, 1f
     nop
    addiu $a0, $zero, 8
    beq $zero, $zero, 2f
     nop
1:  lbu $a0, 0x119c($a0)
2:  lui $t3, 0x8010
    j 0x8008d5c4
     nop
