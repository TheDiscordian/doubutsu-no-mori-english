.set noreorder
.set noat
.text
.balign 4
.globl quest_reply_entry, quest_reply_end, quest_reply_gate, quest_reply_gate_end
/* Original five-argument creator ABI. Keep both native identities unchanged;
 * a separate eighteen-byte descriptor uses the existing loader's visitor slot.
 */
quest_reply_entry:
    sltiu $t0,$a3,12
    beq $t0,$zero,quest_reply_bad
    move $v0,$zero
    addiu $sp,$sp,-64
    sw $ra,60($sp)
    lui $t0,0x4146
    ori $t0,$t0,0x5152
    sw $t0,32($sp)
    sb $a3,36($sp)
    sb $zero,37($sp)
    lhu $t0,82($sp)
    sh $t0,38($sp)
    sw $zero,40($sp)
    sw $zero,44($sp)
    li $t0,246
    sb $t0,48($sp)
    sb $zero,49($sp)
    li $t0,1
    sw $zero,16($sp)
    sw $t0,20($sp)
    jal af_npc_mail_load
    addiu $a3,$sp,32
    lw $ra,60($sp)
    addiu $sp,$sp,64
quest_reply_bad:
    jr $ra
    nop
quest_reply_end:
    .org 0x1f8
/* Original SendRemail frame and eligibility checks remain. Failure skips copy
 * and returns the existing zero result, without completing the quest.
 */
quest_reply_gate:
    beq $v0,$zero,quest_reply_gate_end
    lw $v1,60($sp)
    lw $t0,64($sp)
    li $t1,164
    multu $v1,$t1
    mflo $t1
    addu $a0,$t0,$t1
    addiu $a0,$a0,0x478
    jal 0x8009c67c
    addiu $a1,$sp,76
    li $t2,1
    sw $t2,56($sp)
    nop
quest_reply_gate_end:
