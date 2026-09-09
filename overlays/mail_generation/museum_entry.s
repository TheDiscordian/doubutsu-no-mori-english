.set noreorder
.set noat
.text
.globl museum_entry
museum_entry:
    addiu $sp,$sp,-48
    sw $ra,44($sp)
    sh $a3,28($sp)
    sh $a2,30($sp)
    lui $t0,0x4146
    ori $t0,$t0,0x4D55
    sw $t0,24($sp)
    ori $t0,$zero,24
    sb $t0,32($sp)
    sb $zero,33($sp)
    sb $zero,34($sp)
    ori $t0,$zero,248
    sb $t0,35($sp)
    addiu $a2,$sp,24
    move $a3,$zero
    sw $zero,16($sp)
    sw $zero,20($sp)
    jal af_npc_mail_load
    nop
    move $a1,$zero
    lw $ra,44($sp)
    jr $ra
    addiu $sp,$sp,48
    .space 48

.org 0x800A3580-0x800A345C
    beqz $v0,home_return
    lw $v1,28($sp)
    ori $t0,$zero,164
    multu $v1,$t0
    mflo $t0
    lw $t9,36($sp)
    addu $a0,$t9,$t0
    addiu $a0,$a0,1144
    jal 0x8009C67C
    lw $a1,48($sp)
    addiu $t1,$zero,1
    sw $t1,24($sp)
    nop
home_return:

.org 0x800A3630-0x800A345C
    beqz $v0,queue_return
    move $v1,$v0
    jal 0x800B6A3C
    move $a0,$v0
    move $v1,$v0
queue_return:
