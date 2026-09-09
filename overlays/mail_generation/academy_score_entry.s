.set noreorder
.set noat
.text
.globl academy_score_entry
academy_score_entry:
    addiu $sp,$sp,-256
    sw $ra,252($sp)
    sltiu $at,$a0,4
    beqz $at,score_fail
    sw $a0,216($sp)
    bltz $a1,score_fail
    sw $a1,24($sp)
    sw $a2,220($sp)
    sw $a3,224($sp)
    ori $t0,$zero,0xB48
    multu $a0,$t0
    mflo $t0
    lui $t1,0x8013
    addiu $t1,$t1,-0x5760
    addu $a0,$t0,$t1
    sw $a0,212($sp)
    jal 0x8009C534
    ori $a1,$zero,10
    sw $v0,208($sp)
    lw $a0,24($sp)
    jal 0x80925BB8
    lw $a1,220($sp)
    sh $v0,36($sp)
    lhu $t0,274($sp)
    bnez $t0,item_selected
    lhu $t1,278($sp)
    move $t0,$t1
item_selected:
    sh $t0,28($sp)
    sh $zero,30($sp)
    lui $t0,0x8013
    addiu $t0,$t0,0x6FBC
    lhu $t1,6($t0)
    sh $t1,32($sp)
    lbu $t1,5($t0)
    sb $t1,34($sp)
    lbu $t1,3($t0)
    sb $t1,35($sp)
    sh $zero,38($sp)
    ori $t0,$zero,250
    sb $t0,40($sp)
    ori $t0,$zero,51
    sb $t0,41($sp)
    lui $a1,0x8013
    lw $a1,0x6FD8($a1)
    lw $a2,224($sp)
    addiu $a3,$sp,24
    sw $zero,16($sp)
    ori $t0,$zero,1
    sw $t0,20($sp)
    jal af_npc_mail_load
    addiu $a0,$sp,44
    beqz $v0,score_fail
    lw $t0,208($sp)
    bltz $t0,score_queue
    move $a1,$v0
    ori $t1,$zero,164
    multu $t0,$t1
    mflo $t0
    lw $t1,212($sp)
    jal 0x8009C67C
    addu $a0,$t0,$t1
    ori $v0,$zero,1
    b score_return
    move $v1,$v0
score_queue:
    addiu $a0,$sp,44
    jal 0x800B6A3C
    move $a1,$zero
    b score_return
    sltu $v1,$zero,$v0
score_fail:
    move $v0,$zero
    move $v1,$zero
score_return:
    lw $ra,252($sp)
    jr $ra
    addiu $sp,$sp,256
    .space 308

.org 0x809281C8-0x80925E48
    sltiu $at,$a0,4
    beqzl $at,invalid_player
    move $v1,$zero
.org 0x80928398-0x80925E48
invalid_player:

.section .scheduler,"ax"
.globl academy_score_scheduler
academy_score_scheduler:
    lui $t0,0x8010
    lw $t0,0x7B50($t0)
    ori $t1,$zero,0x27D8
    addu $t9,$t0,$t1
    jalr $t9
    move $a0,$s0
    sw $v1,44($sp)
    lui $a1,0x8010
    lw $a1,0x7B50($a1)
    jal 0x800BEC3C
    lw $a0,64($sp)
    lw $v0,44($sp)
    jal 0x8009CE64
    move $a0,$s0
    b scheduler_return
    nop
    nop
.org 0x8009CF9C-0x8009CF28
scheduler_return:
