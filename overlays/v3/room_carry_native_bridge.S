.set noreorder
.set noat
.text
.globl af_v3_carry_move_bridge
af_v3_carry_move_bridge:
    j af_v3_carry_permit_move
    move $a2,$s0
.globl af_v3_carry_update_bridge
af_v3_carry_update_bridge:
    move $a0,$s0
    j af_v3_carry_after_move
    move $a1,$s6
.globl af_v3_carry_rotation_bridge
af_v3_carry_rotation_bridge:
    j af_v3_carry_draw_rotation
    move $a2,$s0
