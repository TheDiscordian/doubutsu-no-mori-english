.set noreorder
.set noat
.section .text.af_v3_room_colour_update_bridge,"ax",@progbits
.globl af_v3_room_colour_update_bridge
af_v3_room_colour_update_bridge:
    /* The actor field names a resident trampoline, not its relocated owner.
       Resolve through the native initfunc's actual Player_actor_move_func. */
    lui $a2,0x8014
    lw $a2,0x3908($a2)
    lui $t9,(((0x808BD1A8-0x808DDB5C)>>16)&65535)
    ori $t9,$t9,((0x808BD1A8-0x808DDB5C)&65535)
    addu $a2,$a2,$t9
    lui $t0,0x804B
    lw $t0,0x1E00($t0)
    lui $t1,((AF_ROOM_CRC>>16)&65535)
    ori $t1,$t1,(AF_ROOM_CRC&65535)
    bne $t0,$t1,1f
    nop
    j AF_ROOM_COLOUR_UPDATE
    nop
1:  jr $a2
    nop
.section .text.af_v3_room_colour_draw_bridge,"ax",@progbits
.globl af_v3_room_colour_draw_bridge
af_v3_room_colour_draw_bridge:
    lui $t0,0x804B
    lw $t0,0x1E00($t0)
    lui $t1,((AF_ROOM_CRC>>16)&65535)
    ori $t1,$t1,(AF_ROOM_CRC&65535)
    bne $t0,$t1,2f
    nop
    j AF_ROOM_COLOUR_DRAW
    nop
2:  j 0x800530D8
    nop
