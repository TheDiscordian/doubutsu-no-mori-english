.set noreorder
.section .text
.balign 16
.globl af_mail_send_original
af_mail_send_original:
    addiu $sp, $sp, -104
    sw $ra, 20($sp)
    j 0x800A8870
    nop
.globl af_mail_length_original
af_mail_length_original:
    addiu $sp, $sp, -40
    sw $ra, 20($sp)
    j 0x800A861C
    nop

/* Called only at the guarded post-office clear call after NPC delivery.
 * Failure returns through that caller's own epilogue without clearing/counting.
 * Success tail-calls the original clear routine with its original return PC.
 */
.globl af_mail_post_send
af_mail_post_send:
    bnez $v0, 1f
    nop
    j 0x800B6A24
    move $v1, $zero
1:
    j 0x8009C384
    nop

/* Called immediately after Pelly's receipt call, with that caller's frame.
 * Success resumes the original success path. Failure enters the existing
 * letter-return path with a distinct reason, never the success animation.
 */
.globl af_pelly_receipt_result
af_pelly_receipt_result:
    bnez $v0, 2f
    li $t9, 5
    lw $a2, 28($sp)
    li $a3, 4
    li $t1, 1
    addiu $ra, $ra, 12
2:
    jr $ra
    nop

/* Original refusal reasons keep their original table indices. Reason four
 * uses the ordinary hand-back introduction, with its own later explanation.
 */
.globl af_pelly_refusal_index
af_pelly_refusal_index:
    li $v1, 4
    bne $a3, $v1, 3f
    addiu $v1, $a3, 1
    li $v1, 2
3:
    jr $ra
    nop

/* State eight repeats the neutral introduction after hand-back. Its original
 * table is indexed by reason, without the receive menu's extra table entry.
 */
.globl af_pelly_handback_index
af_pelly_handback_index:
    li $at, 4
    bne $t6, $at, 4f
    sll $t7, $t6, 2
    li $t7, 4
4:
    jr $ra
    nop

.section .rodata
.balign 4
.globl af_pelly_refusal_messages
af_pelly_refusal_messages:
    .word 0x2DDA, 0x2DDE, 0x2DE8
