.set noreorder
.set noat
.text
.globl departed_entry
departed_entry:
    addiu $sp,$sp,-0x30
    sw $ra,0x2c($sp)
    beqz $a2,failed
    andi $t1,$a2,1
    bnez $t1,failed
    ori $t0,$zero,0x444d
    sh $t0,0x18($sp)
    lhu $t0,0($a2)
    sh $t0,0x1a($sp)
    lhu $t0,2($a2)
    sh $t0,0x1c($sp)
    lhu $t0,4($a2)
    sh $t0,0x1e($sp)
    lhu $t0,6($a2)
    sh $t0,0x20($sp)
    sb $zero,0x22($sp)
    ori $t0,$zero,0xfd
    sb $t0,0x23($sp)
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
    .org 0x178
    .org 0x1cc
delivery_gate:
    addiu $a0,$a0,0x4570
    lw $a1,0x28($sp)
    jal departed_entry
    lw $a2,0x1c($sp)
    beqz $v0,delivery_return
    or $a0,$v0,$zero
    jal 0x800b6a3c
    or $a1,$zero,$zero
    beqz $v0,delivery_return
    lw $a0,0x1c($sp)
    jal 0x800b7ab0
    nop
    nop
delivery_return:
    .word 0
