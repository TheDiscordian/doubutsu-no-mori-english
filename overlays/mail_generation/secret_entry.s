.set noreorder
.text
.global secret_entry
secret_entry:
    addiu $sp,$sp,-32
    sw $ra,28($sp)
    sw $s0,24($sp)
    sw $s1,20($sp)
    move $s0,$a0
    jal 0x8002C9AC
    nop
    lui $at,0x4170
    mtc1 $at,$f4
    mul.s $f6,$f0,$f4
    trunc.w.s $f8,$f6
    mfc1 $a2,$f8
    nop
    lui $s1,0x8092
    addiu $s1,$s1,0x1B54
    move $a0,$s1
    move $a1,$s0
    lui $a3,%hi(af_mail_generation_capital)
    addiu $a3,$a3,%lo(af_mail_generation_capital)
    jal af_secret_create
    nop
    beqz $v0,done
    nop
    jal 0x800A9364
    nop
    sb $v0,1($s1)
    sw $zero,0($s0)
    move $v0,$s1
done:
    lw $ra,28($sp)
    lw $s0,24($sp)
    lw $s1,20($sp)
    jr $ra
    addiu $sp,$sp,32
    .space 24,0
