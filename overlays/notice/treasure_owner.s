.set noreorder
.set noat
.text
.global af_notice_owner_bridge
.global af_notice_place_enter
.global af_notice_deposit_bridge
af_notice_owner_bridge:
    addiu $sp,$sp,-224
    sw $ra,220($sp)
    lui $t0,0x4146
    ori $t0,$t0,0x4E52
    sw $t0,200($sp)
    addiu $t0,$sp,224
    sw $t0,204($sp)
    srl $t0,$ra,8
    andi $t0,$t0,3
    sw $zero,208($sp)
    sb $t0,208($sp)
    addiu $t0,$zero,244
    sb $t0,211($sp)
    sw $zero,16($sp)
    sw $zero,20($sp)
    addiu $a0,$sp,32
    or $a1,$s6,$zero
    addiu $a2,$sp,200
    or $a3,$zero,$zero
    jal af_npc_mail_load
    nop
    lw $ra,220($sp)
    andi $t0,$ra,0x100
    bne $t0,$zero,1f
    nop
    bne $v0,$zero,1f
    lw $t0,432($sp)
    lw $t1,436($sp)
    lhu $t2,440($sp)
    sh $t2,0($t0)
    lhu $t2,442($sp)
    sh $t2,0($t1)
1:
    jr $ra
    addiu $sp,$sp,224

/* Placement has already allocated 152 bytes and saved all native s registers.
 * Its original sw a1,156(sp) executes in the entry jump's delay slot.
 */
af_notice_place_enter:
    sw $a0,152($sp)
    sw $a3,164($sp)
    j 0x8008EA94
    nop

/* Original six arguments remain; forward the seventh context argument.
 * Tail jump retains the original return at 8008EC4C and all native RNG work.
 */
af_notice_deposit_bridge:
    lw $t9,164($sp)
    lw $t8,168($sp)
    jr $t9
    sw $t8,24($sp)
    .word 0,0
