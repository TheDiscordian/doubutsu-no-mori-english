/* Called with padmgr's serial queue, after both controller reads completed.
   This bridge uses two checked, fully replaced native size-reader tails.
   Original size-reader entries remain unchanged. No fallback enters the tails.
   The main-RAM bridge is available before Expansion Pak code is loaded. */
.set noreorder
.set noat
.section .text.af_v3_room_rumble_bridge,"ax",@progbits
.globl af_v3_room_rumble_bridge
af_v3_room_rumble_bridge:
    addiu $sp,$sp,-24
    sw $ra,20($sp)
    sw $a0,16($sp)
    jal 0x800D6B8C
    nop
    /* Startup leaves installed zero unless the 8-MiB load/check succeeds. */
    lui $t0,0x801A
    lw $t0,-0x5330($t0)
    beqz $t0,1f
    nop
    j af_v3_room_rumble_ready
    nop
.section .text.af_v3_room_rumble_ready,"ax",@progbits
.globl af_v3_room_rumble_ready
af_v3_room_rumble_ready:
    lui $t0,0x804B
    lw $t0,0x1E00($t0)
    lui $t1,(AF_ROOM_CRC >> 16)
    ori $t1,$t1,(AF_ROOM_CRC & 65535)
    bne $t0,$t1,1f
    nop
    lui $a1,0x8011
    lw $a1,-0x0C10($a1)
    jal AF_ROOM_RUMBLE_RETRACE
    lw $a0,16($sp)
1:
    lw $ra,20($sp)
    jr $ra
    addiu $sp,$sp,24
