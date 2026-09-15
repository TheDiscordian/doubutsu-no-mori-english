/* Scene 35 shares sound 0x306 with native floor-audio slot 68. This is a
 * transient audio selector, not replacement flooring or a furniture identity.
 * All other scenes execute their original complete floor getter.
 *
 * The point-light hook supplies the donor's tent position/colour/power to the
 * native light owner. The separate timed lamp/effect lifecycle is not here. */
.set noreorder
.set noat
.set nomacro
.section .text.environment, "ax", @progbits
.balign 4
.globl af_v3_campsite_floor
af_v3_campsite_floor:
    lui $v0, %hi(native_scene)
    lw $v0, %lo(native_scene)($v0)
    addiu $v0, $v0, -35
    bne $v0, $zero, floor_native
     addiu $v0, $zero, 68
    jr $ra
     nop
floor_native:
    addiu $sp, $sp, -24
    j native_floor_body
     sw $ra, 20($sp)

.globl af_v3_campsite_point_info
af_v3_campsite_point_info:
    lui $t0, %hi(native_field_draw)
    lbu $t0, %lo(native_field_draw)($t0)
    addiu $t0, $t0, -1
    bne $t0, $zero, point_native
     lui $t0, %hi(native_scene)
    lw $t0, %lo(native_scene)($t0)
    addiu $t0, $t0, -35
    bne $t0, $zero, point_native
     addiu $t0, $zero, 120
    sh $t0, 0($a1)
    sh $t0, 4($a1)
    addiu $t0, $zero, 80
    sh $t0, 2($a1)
    addiu $t0, $zero, 235
    sb $t0, 0($a2)
    addiu $t0, $zero, 190
    sb $t0, 1($a2)
    addiu $t0, $zero, 185
    sb $t0, 2($a2)
    addiu $t0, $zero, 6000
    sh $t0, 0($a3)
    lw $t0, 16($sp)
    sh $zero, 0($t0)
    jr $ra
     addiu $v0, $zero, 1
point_native:
    addiu $sp, $sp, -32
    sw $a0, 32($sp)
    j native_point_body
     nop
