.set noreorder
.set noat
.set gp=64

/* The pocket hooks run within native o32 functions. Their original prologues
   own the caller's saved return address; preserve every live argument. */
.section .text.af_v3_present_pocket,"ax",@progbits
.globl af_v3_present_pocket
af_v3_present_pocket:
    addiu $t6,$a2,-0x251F
    sltiu $t6,$t6,4
    beqz $t6,ordinary_pocket
    nop
    addiu $sp,$sp,-32
    sw $a0,16($sp)
    sw $a1,20($sp)
    jal af_v3_present_decode
    move $a0,$a2
    lw $a0,16($sp)
    lw $a1,20($sp)
    beqz $v0,rejected_pocket
    addiu $sp,$sp,32
    move $a2,$v0
    j 0x800B8B40
    addiu $a3,$zero,1
rejected_pocket:
    j 0x800B8B7C
    nop
ordinary_pocket:
    addiu $at,$zero,0x251C
    bne $a2,$at,native_pocket
    sll $t6,$a1,1
    j 0x800B8B24
    nop
native_pocket:
    j 0x800B8B44
    nop

.section .text.af_v3_present_free,"ax",@progbits
.globl af_v3_present_free
af_v3_present_free:
    andi $t0,$a1,0xFFFF
    addiu $t0,$t0,-0x251F
    sltiu $t0,$t0,4
    beqz $t0,ordinary_free
    nop
    addiu $sp,$sp,-32
    sw $ra,28($sp)
    sw $a0,16($sp)
    jal af_v3_present_decode
    andi $a0,$a1,0xFFFF
    lw $ra,28($sp)
    lw $a0,16($sp)
    beqz $v0,rejected_free
    addiu $sp,$sp,32
    move $a1,$v0
    addiu $a2,$zero,1
ordinary_free:
    addiu $sp,$sp,-24
    j 0x800B8B94
    sw $ra,20($sp)
rejected_free:
    jr $ra
    move $v0,$zero

/* Middle-of-function hooks preserve full-width GPRs and HI/LO, including
   callee-saved high words. The compiled integer helpers use no FPRs. */
.macro save_live
    addiu $sp,$sp,-272
    sd $at,16($sp)
    sd $v0,24($sp)
    sd $v1,32($sp)
    sd $a0,40($sp)
    sd $a1,48($sp)
    sd $a2,56($sp)
    sd $a3,64($sp)
    sd $t0,72($sp)
    sd $t1,80($sp)
    sd $t2,88($sp)
    sd $t3,96($sp)
    sd $t4,104($sp)
    sd $t5,112($sp)
    sd $t6,120($sp)
    sd $t7,128($sp)
    sd $t8,136($sp)
    sd $t9,144($sp)
    sd $ra,152($sp)
    mfhi $t0
    sd $t0,160($sp)
    mflo $t0
    sd $t0,168($sp)
    sd $s0,176($sp)
    sd $s1,184($sp)
    sd $s2,192($sp)
    sd $s3,200($sp)
    sd $s4,208($sp)
    sd $s5,216($sp)
    sd $s6,224($sp)
    sd $s7,232($sp)
    sd $gp,240($sp)
    sd $fp,248($sp)
.endm
.macro restore_live
    ld $t0,160($sp)
    mthi $t0
    ld $t0,168($sp)
    mtlo $t0
    ld $at,16($sp)
    ld $v0,24($sp)
    ld $v1,32($sp)
    ld $a0,40($sp)
    ld $a1,48($sp)
    ld $a2,56($sp)
    ld $a3,64($sp)
    ld $t0,72($sp)
    ld $t1,80($sp)
    ld $t2,88($sp)
    ld $t3,96($sp)
    ld $t4,104($sp)
    ld $t5,112($sp)
    ld $t6,120($sp)
    ld $t7,128($sp)
    ld $t8,136($sp)
    ld $t9,144($sp)
    ld $s0,176($sp)
    ld $s1,184($sp)
    ld $s2,192($sp)
    ld $s3,200($sp)
    ld $s4,208($sp)
    ld $s5,216($sp)
    ld $s6,224($sp)
    ld $s7,232($sp)
    ld $gp,240($sp)
    ld $fp,248($sp)
    ld $ra,152($sp)
    addiu $sp,$sp,272
.endm

.section .text.af_v3_present_hand,"ax",@progbits
.globl af_v3_present_hand
af_v3_present_hand:
    addiu $at,$v0,-0x251F
    sltiu $at,$at,4
    beqz $at,hand_return
    nop
    save_live
    jal af_v3_present_decode
    move $a0,$v0
    sd $v0,24($sp)
    sltu $t0,$zero,$v0
    lw $t1,156($sp) /* Low word of the actual relocated continuation. */
    sw $t0,0x554($t1)
    restore_live
hand_return:
    jr $ra
    addiu $at,$zero,0x251C

.section .text.af_v3_present_exchange,"ax",@progbits
.globl af_v3_present_exchange
af_v3_present_exchange:
    lw $v1,0x2E4($t9)
    addiu $v1,$v1,-1
    bnez $v1,exchange_return
    nop
    addiu $v1,$a3,-0x2239
    sltiu $v1,$v1,4
    beqz $v1,exchange_return
    nop
    save_live
    move $a0,$a3
    jal af_v3_present_encode
    addiu $a1,$zero,1
    sd $v0,64($sp)
    restore_live
exchange_return:
    jr $ra
    andi $v1,$a3,0xF000
