.set noreorder
.set noat
.text
.globl af_v3_goods_ctor_bridge
af_v3_goods_ctor_bridge:
    j af_v3_goods_ctor
    move $a0,$s0

/* Preserve the native Matrix_scale float ABI while inserting Y rotation.
   All source-stack offsets are relative to the original caller's frame. */
.globl af_v3_goods_single_scale_bridge
af_v3_goods_single_scale_bridge:
    addiu $sp,$sp,-64
    sw $ra,60($sp)
    swc1 $f12,32($sp)
    swc1 $f14,36($sp)
    sw $a2,40($sp)
    sw $a3,44($sp)
    jal af_v3_goods_single_angle
    lw $a0,(64+0x48)($sp)
    b goods_rotate_scale
    nop

.globl af_v3_goods_grid_scale_bridge
af_v3_goods_grid_scale_bridge:
    addiu $sp,$sp,-64
    sw $ra,60($sp)
    swc1 $f12,32($sp)
    swc1 $f14,36($sp)
    sw $a2,40($sp)
    sw $a3,44($sp)
    lw $a0,(64+0x68)($sp)
    lw $a1,(64+0x74)($sp)
    lw $a2,(64+0x78)($sp)
    lw $a3,(64+0x80)($sp)
    lw $t0,(64+0x7C)($sp)
    jal af_v3_goods_grid_angle
    sw $t0,16($sp)
goods_rotate_scale:
    beqz $v0,goods_scale
    move $a0,$v0
    jal Matrix_RotateY
    li $a1,1
goods_scale:
    lwc1 $f12,32($sp)
    lwc1 $f14,36($sp)
    lw $a2,40($sp)
    lw $a3,44($sp)
    lw $ra,60($sp)
    j Matrix_scale
    addiu $sp,$sp,64

.globl af_v3_goods_drop_fg_bridge
af_v3_goods_drop_fg_bridge:
    addiu $sp,$sp,-32
    sw $ra,28($sp)
    lw $t0,(32+0x58)($sp)
    lw $t1,(32+0x5C)($sp)
    sw $t0,16($sp)
    jal af_v3_goods_drop_fg
    sw $t1,20($sp)
    lw $ra,28($sp)
    jr $ra
    addiu $sp,$sp,32
