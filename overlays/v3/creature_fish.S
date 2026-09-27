.set noreorder
.set noat
.text

/* Inline bridges preserve every live register except their named result.
   Retain the origin marker after a fish changes into rubbish. */
.macro VALUE actor, row, result
    addiu $sp,$sp,-16
    sw $at,0($sp)
    sw $t8,4($sp)
    lbu $at,0x1DA(\actor)
    beqz $at,9f
    lhu $t8,0x1D8(\actor)
    sltiu $at,$t8,7
    beqz $at,9f
    sll $t8,$t8,2
    lui $at,%hi(af_fish_values+32*\row)
    addu $at,$at,$t8
    lwc1 \result,%lo(af_fish_values+32*\row)($at)
9:
    lw $at,0($sp)
    lw $t8,4($sp)
    addiu $sp,$sp,16
.endm
.macro FLOAT name, row, result, high, low=0
.globl af_v3_fish_\name
af_v3_fish_\name:
    lui $at,\high
    ori $at,$at,\low
    mtc1 $at,\result
    VALUE $s0,\row,\result
    jr $ra
    nop
.endm
FLOAT initial_scale,4,$f0,0x3C23,0xD70A
FLOAT comeback_scale,4,$f0,0x3C23,0xD70A
FLOAT escape_distance,10,$f10,0x41B0
FLOAT near_distance,3,$f6,0x4170
FLOAT touch_distance,3,$f8,0x4170
FLOAT touch_speed,0,$f10,0x3FA0
FLOAT back_speed,1,$f18,0xBED7,0x0A3D

.globl af_v3_fish_bite_radius
af_v3_fish_bite_radius:
    VALUE $s0,9,$f6
    jr $ra
    swc1 $f6,0x1C($sp)

.globl af_v3_fish_splash_radius
af_v3_fish_splash_radius:
    /* The source effect routine takes the actor from its saved argument. */
    addiu $sp,$sp,-8
    sw $t7,0($sp)
    lw $t7,0x50($sp)
    VALUE $t7,5,$f6
    lw $t7,0($sp)
    addiu $sp,$sp,8
    jr $ra
    swc1 $f6,0x1C($sp)

.globl af_v3_fish_splash_kind
af_v3_fish_splash_kind:
    /* Replace the native arg==6 test with the source's range 4..8. */
    addiu $sp,$sp,-8
    sw $t8,0($sp)
    lw $t8,0x50($sp)
    lbu $at,0x1DA($t8)
    beqz $at,1f
    li $at,6
    addiu $at,$t2,-4
    sltiu $at,$at,5
    beqz $at,1f
    li $at,6
    move $at,$t2
1:
    lw $t8,0($sp)
    addiu $sp,$sp,8
    jr $ra
    mov.s $f2,$f0

.globl af_v3_fish_touch_count
af_v3_fish_touch_count:
    addiu $t8,$t7,19
    lbu $at,0x1DA($s0)
    beqz $at,1f
    nop
    lhu $t8,0x1D8($s0)
    sll $t8,$t8,2
    lui $at,%hi(af_fish_values+64)
    addu $at,$at,$t8
    lw $t8,%lo(af_fish_values+64)($at)
    addu $t8,$t8,$t7
1:
    jr $ra
    sw $t8,0x214($s0)

.globl af_v3_fish_trash
af_v3_fish_trash:
    /* t6 is the old fish index. Match original coelacanth/salmon choices. */
    li $at,31
    beq $t6,$at,1f
    li $t8,34
    li $t8,33
1:
    lbu $at,0x1DA($s0)
    beqz $at,2f
    nop
    lhu $t8,0x1D8($s0)
    sll $t8,$t8,2
    lui $at,%hi(af_fish_values+224)
    addu $at,$at,$t8
    lw $t8,%lo(af_fish_values+224)($at)
2:
    jr $ra
    sw $t8,0x1D4($s0)

.macro EFFECT name, row, old, delta
.globl af_v3_fish_\name
af_v3_fish_\name:
    li $a2,\old
    addiu $sp,$sp,-8
    sw $t8,0($sp)
    lbu $at,0x1DA($a0)
    beqz $at,1f
    nop
    lhu $t8,0x1D8($a0)
    sll $t8,$t8,2
    lui $at,%hi(af_fish_values+32*\row)
    addu $at,$at,$t8
    lw $a2,%lo(af_fish_values+32*\row)($at)
1:
    lw $t8,0($sp)
    addiu $sp,$sp,8
    /* Continue in the relocated native effect, relative to this call site. */
    addiu $at,$ra,\delta
    jr $at
    nop
.endm
EFFECT ripple,11,2,-0x858
EFFECT splash,8,6,-0x147C

.macro CLAMP name, reg
.globl af_v3_fish_\name
af_v3_fish_\name:
    sltiu $at,\reg,6
    bnez $at,1f
    nop
    li \reg,5
1:
    jr $ra
    sll \reg,\reg,2
.endm
CLAMP river_ripple,$t8
CLAMP river_splash,$t5

.globl af_v3_fish_dispatch
af_v3_fish_dispatch:
    addiu $at,$v0,-36
    sltiu $at,$at,9
    sb $at,0x1DA($s0)
    li $at,35
    bne $v0,$at,1f
    nop
    li $at,22
    sw $at,0x1D4($s0)
    jr $ra
    li $v0,1
1:
    li $at,31
    beq $v0,$at,2f
    addiu $v0,$v0,-39
    jr $ra
    sltiu $v0,$v0,4
2:
    jr $ra
    li $v0,1

.globl af_v3_fish_make_release
af_v3_fish_make_release:
    lw $t0,0x34($sp)
    addiu $t1,$t0,-0x2300
    sltiu $at,$t1,45
    beqz $at,1f
    sll $t1,$t1,1
    lui $at,%hi(AF_FISH_IDENTITIES)
    addu $at,$at,$t1
    lhu $t0,%lo(AF_FISH_IDENTITIES)($at)
    sw $t0,0x34($sp)
1:
    j 0x80057E24
    nop

.globl af_v3_fish_release_index
af_v3_fish_release_index:
    addiu $t7,$t6,-0x250E
    sltiu $at,$t7,3
    beqz $at,1f
    nop
    b 2f
    addiu $t7,$t7,32
1:
    addiu $t7,$t6,-0x2300
    sltiu $at,$t7,32
    bnez $at,2f
    nop
    addiu $t7,$t7,4
2:
    jr $ra
    sw $t7,0x178($s0)
