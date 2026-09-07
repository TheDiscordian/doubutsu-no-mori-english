.set noreorder
.section .text
.balign 16
/* Only these three gate instructions replace native words. The gaps belong
 * to unchanged native instructions and are not replacement payloads.
 */
.org 0x4C
    jal 0x802F8010
    nop
    beq $v0, $zero, failed
    move $a0, $v0
.org 0x6C
failed:
    nop

.section .fixture,"ax"
.balign 16
/* Isolated test creator; this never assembles a letter. */
    lui $t0, 0x802F
    ori $t0, $t0, 0x8010
    sw $a0, 0($t0)
    sw $a1, 4($t0)
    sw $a2, 8($t0)
    sw $a3, 12($t0)
    lw $t1, 16($sp)
    sw $t1, 16($t0)
    lw $t1, 20($sp)
    sw $t1, 20($t0)
    lw $t1, 24($t0)
    addiu $t1, $t1, 1
    sw $t1, 24($t0)
    lw $v0, 28($t0)
    jr $ra
    ori $v1, $zero, 0x5A5A
