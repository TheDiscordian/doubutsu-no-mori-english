.set noreorder
.set noat
.section .text.guide_name,"ax",@progbits
.global af_guide_name
af_guide_name:
    addiu $sp, $sp, -32
    sw $ra, 28($sp)
    sw $s0, 24($sp)
    sw $s1, 20($sp)
    move $s1, $a1
    jal 0x800ACD18
    move $s0, $a0
    li $t0, 32
    sb $t0, 6($s0)
    sb $t0, 7($s0)
    beq $s1, $zero, done
    nop
    lhu $a2, 0($s1)
    addiu $t0, $a2, 0x2000
    andi $t0, $t0, 0xFFFF
    sltiu $t0, $t0, 216
    beq $t0, $zero, done
    move $a0, $s0
    jal 0x80196044
    li $a1, 8
done:
    lw $ra, 28($sp)
    lw $s1, 20($sp)
    lw $s0, 24($sp)
    jr $ra
    addiu $sp, $sp, 32
    .space 12
