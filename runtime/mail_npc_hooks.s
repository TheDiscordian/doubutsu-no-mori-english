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
