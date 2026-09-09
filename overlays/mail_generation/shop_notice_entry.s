.set noreorder
.set noat
.text
.balign 4
.globl shop_spotlight_entry, shop_spotlight_end
.globl shop_reopening_entry, shop_reopening_end
/* Original ABI: home, shop level, item, type, send procedure.
 * The selector at 800C1070 remains untouched. Mode zero publishes a cleared
 * saved leaflet; nonzero publishes directly to the mapped home mailbox.
 */
shop_spotlight_entry:
    addiu $sp,$sp,-304
    sw $ra,300($sp)
    sw $s0,296($sp)
    sw $s1,292($sp)
    sw $s2,288($sp)
    sw $s3,284($sp)
    sw $s4,280($sp)
    sw $s5,276($sp)
    sw $s6,272($sp)
    move $s0,$a0
    move $s1,$a1
    andi $s2,$a2,0xffff
    move $s3,$a3
    lw $s4,320($sp)
    sltiu $t0,$s0,4
    beq $t0,$zero,spotlight_done
    sltiu $t0,$s1,4
    beq $t0,$zero,spotlight_done
    li $t0,0x0b48
    multu $s0,$t0
    mflo $s5
    lui $t0,0x8012
    addiu $t0,$t0,0x6ea0
    addu $s5,$s5,$t0
    lhu $t0,0x3596($s5)
    li $t1,0xffff
    beq $t0,$t1,spotlight_done
    addiu $a0,$s5,0x3a00
    jal 0x8009c534
    li $a1,10
    move $s6,$v0
    jal 0x80094c10
    move $a0,$s0
    andi $s0,$v0,3
    jal 0x800816c0
    move $a0,$s0
    li $t0,1
    beq $v0,$t0,spotlight_done
    li $t0,0x0bd0
    multu $s0,$t0
    mflo $t1
    lui $a1,0x8012
    addiu $a1,$a1,0x6ec0
    addu $a1,$a1,$t1
    andi $t0,$s3,1
    sll $t0,$t0,2
    sll $t1,$s1,3
    addu $t0,$t0,$t1
    lui $t1,0x8011
    addiu $t1,$t1,-0x23c4
    addu $t0,$t0,$t1
    lw $t0,0($t0)
    sh $t0,60($sp)
    sh $s2,62($sp)
    lui $t0,0x4146
    ori $t0,$t0,0x534e
    sw $t0,56($sp)
    li $t0,55
    sb $t0,64($sp)
    sltu $t0,$zero,$s4
    sb $t0,65($sp)
    sb $zero,66($sp)
    li $t0,247
    sb $t0,67($sp)
    addiu $a0,$sp,96
    addiu $a2,$sp,56
    move $a3,$zero
    sw $zero,16($sp)
    jal af_npc_mail_load
    sw $zero,20($sp)
    beq $v0,$zero,spotlight_done
    nop
    bne $s4,$zero,spotlight_home
    addiu $a0,$sp,96
    jal 0x800b6a3c
    li $a1,1
    b spotlight_done
    nop
spotlight_home:
    bltz $s6,spotlight_done
    li $t0,164
    multu $s6,$t0
    mflo $t0
    addu $a0,$s5,$t0
    addiu $a0,$a0,0x3a00
    jal 0x8009c67c
    addiu $a1,$sp,96
spotlight_done:
    lw $ra,300($sp)
    lw $s0,296($sp)
    lw $s1,292($sp)
    lw $s2,288($sp)
    lw $s3,284($sp)
    lw $s4,280($sp)
    lw $s5,276($sp)
    lw $s6,272($sp)
    jr $ra
    addiu $sp,$sp,304
shop_spotlight_end:
    .org 0x1d8
/* Preserve the entire original selection caller between the two owners. */
    .org 0x398
shop_reopening_entry:
    addiu $sp,$sp,-288
    sw $ra,284($sp)
    sw $s0,280($sp)
    sw $s1,276($sp)
    sw $s2,272($sp)
    sw $s3,268($sp)
    lui $t0,0x8013
    lbu $t0,0x5c12($t0)
    andi $t0,$t0,0x20
    beq $t0,$zero,reopening_done
    nop
    jal 0x8007d318
    lui $a0,0x2000
    bne $v0,$zero,reopening_done
    nop
    jal 0x800c16f0
    nop
    sltiu $t0,$v0,4
    beq $t0,$zero,reopening_done
    sll $t0,$v0,2
    lui $t1,0x8011
    addiu $t1,$t1,-0x23a4
    addu $t0,$t0,$t1
    lw $t0,0($t0)
    sh $t0,36($sp)
    sh $zero,38($sp)
    lui $t0,0x4146
    ori $t0,$t0,0x534e
    sw $t0,32($sp)
    lui $t0,0x3700
    ori $t0,$t0,0x00f7
    sw $t0,40($sp)
    addiu $a0,$sp,80
    lui $a1,0x8012
    addiu $a1,$a1,0x6ec0
    addiu $a2,$sp,32
    move $a3,$zero
    sw $zero,16($sp)
    jal af_npc_mail_load
    sw $zero,20($sp)
    beq $v0,$zero,reopening_done
    move $s0,$zero
    lui $s1,0x8012
    addiu $s1,$s1,0x6ea0
reopening_home:
    jal 0x80094c10
    move $a0,$s0
    andi $s3,$v0,3
    addiu $a0,$s1,0x3a00
    jal 0x8009c534
    li $a1,10
    bltz $v0,reopening_next
    move $s2,$v0
    lhu $t0,0x3596($s1)
    li $t1,0xffff
    beq $t0,$t1,reopening_next
    nop
    jal 0x800816c0
    move $a0,$s3
    bne $v0,$zero,reopening_next
    li $t0,0x0bd0
    multu $s3,$t0
    mflo $t0
    lui $a1,0x8012
    addiu $a1,$a1,0x6ec0
    addu $a1,$a1,$t0
    jal 0x800b79e0
    addiu $a0,$sp,80
    li $t0,164
    multu $s2,$t0
    mflo $t0
    addu $a0,$s1,$t0
    addiu $a0,$a0,0x3a00
    sb $zero,96($sp)
    jal 0x8009c67c
    addiu $a1,$sp,80
reopening_next:
    addiu $s0,$s0,1
    li $t0,4
    bne $s0,$t0,reopening_home
    addiu $s1,$s1,0x0b48
    lui $t0,0x8013
    lbu $t1,0x5c12($t0)
    andi $t1,$t1,0xffdf
    sb $t1,0x5c12($t0)
reopening_done:
    lw $ra,284($sp)
    lw $s0,280($sp)
    lw $s1,276($sp)
    lw $s2,272($sp)
    lw $s3,268($sp)
    jr $ra
    addiu $sp,$sp,288
shop_reopening_end:
    .org 0x590
