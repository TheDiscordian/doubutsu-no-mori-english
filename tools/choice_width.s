# Replacement mChoice_Get_MaxStringDotWidth, linked at 0x80065348.
# Keep o32 argument space and every used saved register intact.
.set noreorder
.set noat
.section .patch,"ax",@progbits
.balign 4
    addiu $sp, $sp, -40
    sw $ra, 36($sp)
    sw $s0, 32($sp)
    sw $s1, 28($sp)
    sw $s2, 24($sp)
    sw $s3, 20($sp)
    lw $s2, 0x7c($a0)
    addiu $s0, $a0, 0x5c
    lui $s1, 0x800a
    addiu $s1, $s1, -2888 # 0x8009f4b8
    blez $s2, done
    or $s3, $zero, $zero
row:
    lw $a1, 0($s0)
    or $a0, $s1, $zero
    jal 0x800902cc
    or $a2, $zero, $zero
    slt $at, $s3, $v0
    beq $at, $zero, next
    addiu $s0, $s0, 4
    or $s3, $v0, $zero
next:
    addiu $s2, $s2, -1
    bne $s2, $zero, row
    addiu $s1, $s1, 16
done:
    or $v0, $s3, $zero
    lw $ra, 36($sp)
    lw $s0, 32($sp)
    lw $s1, 28($sp)
    lw $s2, 24($sp)
    lw $s3, 20($sp)
    jr $ra
    addiu $sp, $sp, 40
    nop
    nop
