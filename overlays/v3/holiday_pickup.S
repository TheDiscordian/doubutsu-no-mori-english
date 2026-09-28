.set noreorder
.set noat
.set gp=64
.text
/* JAL at the ordinary pickup controller's outdoor-search boundary. All
 * original field/input/action checks and the full native caller frame remain. */
.globl af_holiday_pickup_entry
.type af_holiday_pickup_entry,@function
af_holiday_pickup_entry:
    addiu $sp,$sp,-32
    sd $ra,24($sp)
    sd $a0,16($sp)
    jal af_holiday_pickup_try
    nop
    ld $a0,16($sp)
    ld $ra,24($sp)
    beqz $v0,1f
    addiu $sp,$sp,32
    /* Original epilogue is 808BC2C8; caller RA is 808BC1E8. */
    addiu $t9,$ra,0xE0
    jr $t9
    addiu $v0,$zero,1
1:  j af_decor_native_player
    nop
.size af_holiday_pickup_entry,.-af_holiday_pickup_entry

/* All four seasonal callers have the same relative output function. s5 is
 * their actual foreground pointer. Unrelated items take the original call
 * directly, with no field lookup or C call added to their drawing. */
.globl af_holiday_pickup_ground
.type af_holiday_pickup_ground,@function
af_holiday_pickup_ground:
    lhu $t9,0($s5)
    addiu $at,$zero,0x2530
    bne $t9,$at,2f
    nop
    addiu $sp,$sp,-64
    sd $a0,16($sp)
    sd $a1,24($sp)
    sd $a2,32($sp)
    sd $a3,40($sp)
    sd $ra,48($sp)
    jal af_holiday_pickup_height
    lw $a0,80($sp)
    ld $a0,16($sp)
    ld $a1,24($sp)
    ld $a2,32($sp)
    ld $a3,40($sp)
    ld $ra,48($sp)
    addiu $sp,$sp,64
2:  addiu $t9,$ra,-0x320
    jr $t9
    nop
.size af_holiday_pickup_ground,.-af_holiday_pickup_ground
