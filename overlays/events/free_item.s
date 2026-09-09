# Independently assembled adapters, with their original argument expressions.
.set noreorder
.set noat
.section .text.letter,"ax",@progbits
.globl af_free_letter
af_free_letter:
    move $a0, $a1
    addiu $a2, $zero, 2
    jal 0x800BB700
    addiu $a1, $zero, 2
    .space 28
.section .text.reserve,"ax",@progbits
.globl af_free_reserve
af_free_reserve:
    lhu $a0, 0x5df8($a1)
    jal 0x800BB6F8
    addiu $a1, $zero, 0
    .space 24
.section .text.shrine,"ax",@progbits
.globl af_free_shrine
af_free_shrine:
    lhu $a0, 0xe0($t9)
    jal 0x800BB6F8
    addiu $a1, $zero, 0
    .space 16
.section .text.tail,"ax",@progbits
.globl af_free_boot_tail
af_free_boot_tail:
    jal 0x8009D6D0
    nop
    beq $v0, $zero, af_boot_failed
    nop
    lw $ra, 36($sp)
    lw $s0, 32($sp)
    lw $s1, 28($sp)
    jr $ra
    addiu $sp, $sp, 40
