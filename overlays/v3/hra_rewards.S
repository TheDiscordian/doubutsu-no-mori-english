.set noreorder
.set noat
.text
.globl af_hra_reward_send
af_hra_reward_send:
    addiu $sp,$sp,-256
    sw $ra,252($sp)
    sltiu $at,$a0,4
    beqz $at,failed
    nop
    sw $a0,216($sp)
    bltz $a1,failed
    sw $a1,24($sp)
    sw $a2,220($sp)
    sw $a3,224($sp)
    ori $t0,$zero,0xB48
    multu $a0,$t0
    mflo $t0
    lui $t1,0x8013
    addiu $t1,$t1,-22368
    addu $a0,$t0,$t1
    sw $a0,212($sp)
    jal af_hra_mail_free
    ori $a1,$zero,10
    sw $v0,208($sp)
    lw $a0,24($sp)
    jal af_hra_native_letter
    lw $a1,220($sp)
    jal af_hra_reward_choose
    sh $v0,36($sp)
    lhu $t0,274($sp)
    bnez $t0,have_item
    lhu $t1,278($sp)
    or $t0,$t1,$zero
have_item:
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
    jal af_hra_english_mail
    addiu $a0,$sp,44
    beqz $v0,failed
    lw $t0,208($sp)
    bltz $t0,queue_mail
    or $a1,$v0,$zero
    ori $t1,$zero,164
    multu $t0,$t1
    mflo $t0
    lw $t1,212($sp)
    jal af_hra_mail_copy
    addu $a0,$t0,$t1
    ori $v0,$zero,1
    b complete
    or $v1,$v0,$zero
queue_mail:
    addiu $a0,$sp,44
    jal af_hra_mail_receipt
    or $a1,$zero,$zero
    b complete
    sltu $v1,$zero,$v0
failed:
    or $v0,$zero,$zero
    or $v1,$zero,$zero
complete:
    beqz $v1,exit
    lw $t0,228($sp)
    beqz $t0,exit
    lw $t1,212($sp)
    lbu $t2,-1116($t1)
    or $t2,$t2,$t0
    sb $t2,-1116($t1)
exit:
    lw $ra,252($sp)
    jr $ra
    addiu $sp,$sp,256

/* The original selector consumes the same RNG draw before this helper.
 * Keep its ordinary result unless a selected, unearned source reward applies.
 * The house owns these flags; this does not create another player/save owner.
 */
af_hra_reward_choose:
    sw $ra,232($sp)
    sh $zero,38($sp)
    sw $zero,228($sp)
    lw $t0,24($sp)
    lui $at,1
    ori $at,$at,0x1170
    slt $at,$t0,$at
    bnez $at,choose_exit
    lw $t1,212($sp)
    lbu $t2,-1116($t1)
    andi $t2,$t2,8
    bnez $t2,second
    nop
    jal af_hra_import_selected
    ori $a0,$zero,1033
    beqz $v0,second
    nop
    ori $t0,$zero,0x3024
    sh $t0,38($sp)
    ori $t0,$zero,0x221
    sh $t0,36($sp)
    ori $t0,$zero,8
    b choose_exit
    sw $t0,228($sp)
second:
    lw $t0,24($sp)
    lui $at,1
    ori $at,$at,0x86A0
    slt $at,$t0,$at
    bnez $at,choose_exit
    lw $t1,212($sp)
    lbu $t2,-1116($t1)
    andi $t2,$t2,4
    bnez $t2,choose_exit
    nop
    jal af_hra_import_selected
    ori $a0,$zero,1034
    beqz $v0,choose_exit
    nop
    ori $t0,$zero,0x3028
    sh $t0,38($sp)
    ori $t0,$zero,0x222
    sh $t0,36($sp)
    ori $t0,$zero,4
    sw $t0,228($sp)
choose_exit:
    lw $ra,232($sp)
    jr $ra
    nop
