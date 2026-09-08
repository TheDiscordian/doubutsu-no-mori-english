.set noreorder
.set noat
.text
.globl academy_entry
academy_entry:
    addiu $sp,$sp,-240
    sw $ra,236($sp)
    sltiu $at,$a0,4
    beqz $at,academy_fail
    addiu $t0,$a1,-0x1DC
    sltiu $at,$t0,20
    beqz $at,academy_fail
    sh $a1,36($sp)
    ori $t0,$zero,0xB48
    multu $a0,$t0
    mflo $t0
    lui $t1,0x8013
    addiu $t1,$t1,-0x5760
    addu $a0,$t0,$t1
    sw $a0,212($sp)
    jal 0x8009C534
    ori $a1,$zero,10
    bltz $v0,academy_fail
    sw $v0,216($sp)
    sw $zero,24($sp)
    sw $zero,28($sp)
    sw $zero,32($sp)
    sh $zero,38($sp)
    ori $t0,$zero,251
    sb $t0,40($sp)
    ori $t0,$zero,51
    sb $t0,41($sp)
    addiu $a0,$sp,48
    lui $a1,0x8013
    lw $a1,0x6FD8($a1)
    move $a2,$zero
    addiu $a3,$sp,24
    sw $zero,16($sp)
    ori $t0,$zero,1
    jal af_npc_mail_load
    sw $t0,20($sp)
    beqz $v0,academy_fail
    lw $t0,216($sp)
    ori $t1,$zero,164
    multu $t0,$t1
    mflo $t0
    lw $t1,212($sp)
    addu $a0,$t0,$t1
    jal 0x8009C67C
    move $a1,$v0
    ori $v0,$zero,1
    b academy_return
    nop
academy_fail:
    move $v0,$zero
academy_return:
    lw $ra,236($sp)
    jr $ra
    addiu $sp,$sp,240
    .space 68

.org 0x8009CE2C-0x8009CC94
    beqz $v0,scheduler_return
    lw $t1,56($sp)
    ori $t2,$zero,0xB48
    multu $t1,$t2
    mflo $t2
    lui $t3,0x8013
    addu $v0,$t2,$t3
    lbu $t5,-0x5BBC($v0)
    ori $t6,$t5,0x20
    sb $t6,-0x5BBC($v0)
    jal 0x8009CB5C
    move $a0,$s0
    b scheduler_return
    nop
hint_success_gate:
    beqz $v0,hint_return
    nop
    j 0x8009CB5C
    nop
hint_return:
    jr $ra
    nop

.org 0x8009CF94-0x8009CC94
    jal hint_success_gate
.org 0x8009CF9C-0x8009CC94
scheduler_return:
