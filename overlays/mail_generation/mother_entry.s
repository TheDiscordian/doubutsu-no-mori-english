.set noreorder
.set noat
.text
.globl mother_entry
mother_entry:
    addiu $sp,$sp,-0x30
    sw $ra,0x2c($sp)
    lw $t0,0x40($sp)
    sltiu $at,$t0,0x1a4
    beqz $at,failed
    sltiu $at,$a3,64
    beqz $at,failed
    lui $t1,0x4146
    ori $t1,$t1,0x4d4f
    sw $t1,0x18($sp)
    sh $t0,0x1c($sp)
    sh $a2,0x1e($sp)
    sb $a3,0x20($sp)
    sb $zero,0x21($sp)
    sb $zero,0x22($sp)
    ori $t1,$zero,0xfe
    sb $t1,0x23($sp)
    addiu $a2,$sp,0x18
    or $a3,$zero,$zero
    sw $zero,0x10($sp)
    sw $zero,0x14($sp)
    jal af_npc_mail_load
    nop
    b finished
    nop
failed:
    or $v0,$zero,$zero
finished:
    lw $ra,0x2c($sp)
    jr $ra
    addiu $sp,$sp,0x30
    .org 0x80
    .org 0x124
mailbox_gate:
    beqz $v0,delivery_return
    lw $v1,0x28($sp)
    lw $t0,0x30($sp)
    sll $t1,$v1,2
    addu $t1,$t1,$v1
    sll $t1,$t1,3
    addu $t1,$t1,$v1
    sll $t1,$t1,2
    addu $a0,$t0,$t1
    addiu $a0,$a0,0x478
    jal 0x8009c67c
    or $a1,$v0,$zero
    .org 0x190
queue_gate:
    beqz $v0,delivery_return
    or $a0,$v0,$zero
    .org 0x1a4
delivery_return:
    .word 0
