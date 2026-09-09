.set noreorder
.set noat
.section .text.preparation, "ax"
move $t6, $a0
lui $t0, 0x2020
ori $t0, $t0, 0x2020
sw $t0, 0x1c($sp)
sw $t0, 0x20($sp)
lw $a1, 0x28($t6)
lw $a2, 0x2c($t6)
lw $a3, 0x30($t6)
addiu $a0, $sp, 0x1c
jal 0x800acf84
nop
.section .text.length, "ax"
addiu $a3, $zero, 8
.section .text.identity, "ax"
jal 0x800bb708
