.set noreorder
.set noat
.text
.globl snowman_entry
snowman_entry:
    addiu $sp,$sp,-32
    sw $s0,24($sp)
    move $s0,$a0
    sw $ra,28($sp)
    lui $t6,0x8013
    lw $t6,0x6FD8($t6)
    jal 0x8002C9AC
    sw $t6,20($sp)
    lui $at,0x4140
    mtc1 $at,$f4
    move $a0,$s0
    lw $a1,20($sp)
    mul.s $f6,$f0,$f4
    trunc.w.s $f8,$f6
    mfc1 $a2,$f8
    nop
    lui $a3,%hi(af_mail_generation_capital)
    addiu $a3,$a3,%lo(af_mail_generation_capital)
    jal af_snowman_create
    nop
    lw $ra,28($sp)
    lw $s0,24($sp)
    jr $ra
    addiu $sp,$sp,32
    .space 112
.org 0x8096E2B4-0x8096E1A4
    jal snowman_entry
    move $a0,$s0
    beqz $v0,release_mail
    move $a0,$s0
    jal 0x800B6A3C
    move $a1,$zero
    nop
release_mail:
