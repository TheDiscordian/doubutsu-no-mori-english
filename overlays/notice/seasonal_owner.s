.set noreorder
.set noat
.text
.global af_notice_seasonal_bridge
/* Entered only from the native seasonal formatter call. The caller owns
 * s1=index pointer, s2=posting-year pointer, and s4=104-byte pending post.
 * Preserve its timestamp and every saved register. No pending cursor is
 * advanced until the complete encoded record has reached the native board.
 */
af_notice_seasonal_bridge:
    addiu $sp,$sp,-240
    sw $ra,236($sp)
    lui $t0,0x4146
    ori $t0,$t0,0x4E53
    sw $t0,212($sp)
    lw $t0,256($sp)
    sh $t0,216($sp)
    lhu $t0,0($s2)
    sh $t0,218($sp)
    sw $zero,220($sp)
    addiu $t0,$zero,243
    sb $t0,223($sp)
    sw $zero,196($sp)
    sw $zero,200($sp)
    sw $zero,204($sp)
    sw $zero,208($sp)
    sw $zero,16($sp)
    sw $zero,20($sp)
    addiu $a0,$sp,32
    addiu $a1,$sp,196
    addiu $a2,$sp,212
    or $a3,$zero,$zero
    jal af_npc_mail_load
    nop
    beq $v0,$zero,2f
    addiu $t0,$sp,32
    or $t1,$s4,$zero
    addiu $t2,$sp,128
1:
    lw $t3,0($t0)
    addiu $t0,$t0,4
    sw $t3,0($t1)
    bne $t0,$t2,1b
    addiu $t1,$t1,4
    jal 0x800A5D30
    or $a0,$s4,$zero
    lbu $t0,0($s1)
    lhu $t1,0($s2)
    lui $t2,0x8013
    sb $t0,0x7919($t2)
    sh $t1,0x791A($t2)
    addiu $v0,$zero,1
2:
    lw $ra,236($sp)
    jr $ra
    addiu $sp,$sp,240
    .space 448-(.-af_notice_seasonal_bridge)
