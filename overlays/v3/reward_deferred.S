.set noreorder
.set noat
.text
.globl af_v3_reward_clear_submenu
af_v3_reward_clear_submenu:
    lui $t9, 0x8014
    sw $zero, 0x3930($t9)
    jr $ra
    nop

/* Native request tail: v0 is the actor, t6 the requested action. */
.globl af_v3_reward_clear_request
af_v3_reward_clear_request:
    addiu $t9, $zero, 63
    beq $t6, $t9, 1f
    addiu $t9, $zero, 81
    bne $t6, $t9, 2f
    nop
1:  sw $zero, 0xD70($v0)
2:  jr $ra
    nop

/* Called from the original tag frame; ra provides its actual loaded address. */
.globl af_v3_reward_exchange_entry
af_v3_reward_exchange_entry:
    j af_v3_reward_exchange
    move $a2, $ra
