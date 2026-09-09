.set noreorder
.set noat
.text
.globl post_office_entry
post_office_entry:
    addiu $sp,$sp,-48
    sw $ra,44($sp)
    sh $a1,28($sp)
    sh $a2,30($sp)
    lui $t0,0x4146
    ori $t0,$t0,0x504F
    sw $t0,24($sp)
    ori $t0,$zero,55
    sb $t0,32($sp)
    sb $zero,33($sp)
    sb $zero,34($sp)
    ori $t0,$zero,249
    sb $t0,35($sp)
    move $a1,$a3
    addiu $a2,$sp,24
    move $a3,$zero
    sw $zero,16($sp)
    sw $zero,20($sp)
    jal af_npc_mail_load
    nop
    sltu $v0,$zero,$v0
    lw $ra,44($sp)
    jr $ra
    addiu $sp,$sp,48
    .space 32

.org 0x800B6C6C-0x800B6B94
    beqz $v0,order_return
    lw $a0,208($sp)
    jal 0x800B6AC8
    addiu $a1,$sp,44
order_return:
    lw $ra,20($sp)
    jr $ra
    addiu $sp,$sp,208

.org 0x800B6DB0-0x800B6B94
    beqz $v0,ticket_return
    lw $a0,192($sp)
    jal 0x800B6AC8
    addiu $a1,$sp,28
ticket_return:
    lw $ra,20($sp)
    jr $ra
    addiu $sp,$sp,192
