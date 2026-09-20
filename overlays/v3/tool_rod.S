.set noreorder
.set noat
.section .af_tool_rod, "ax"
.align 2

/* Resolve the current player owner; use its selected-equipment reader. */
.ent af_v3_fish_kind
af_v3_fish_kind:
    lui     $t9, 0x8014
    lw      $t9, 0x3900($t9)
    lui     $t0, 0xFFFE
    addiu   $t0, $t0, -848
    addu    $t9, $t9, $t0
    jr      $t9
    nop
.end af_v3_fish_kind

/* Both search windows have v0=class*4, a0=signed target angle, f2=angle scale.
   The remainder of each original function owns all comparisons and branches. */
.globl af_v3_fish_angle
.ent af_v3_fish_angle
af_v3_fish_angle:
    addiu   $sp, $sp, -40
    sw      $ra, 28($sp)
    sw      $a0, 24($sp)
    sw      $v0, 16($sp)
    sdc1    $f2, 32($sp)
    jal     af_v3_fish_kind
    nop
    addiu   $at, $zero, 88
    bne     $v0, $at, 1f
    lw      $t0, 16($sp)
    addiu   $t0, $t0, 20
1:
    lui     $at, %hi(af_v3_fish_angles)
    addiu   $at, $at, %lo(af_v3_fish_angles)
    addu    $at, $at, $t0
    lwc1    $f0, 0($at)
    ldc1    $f2, 32($sp)
    lw      $a0, 24($sp)
    lw      $ra, 28($sp)
    jr      $ra
    addiu   $sp, $sp, 40
.end af_v3_fish_angle

/* t8 is the original native bite duration, a0 the fish. The source audit binds
   every native row to one of these five classes, without GC's doubled ticks.
   Reproduce the original speed-reset helper as well as its displaced store. */
.globl af_v3_fish_bite
.ent af_v3_fish_bite
af_v3_fish_bite:
    addiu   $sp, $sp, -32
    sw      $ra, 24($sp)
    sw      $a0, 20($sp)
    sw      $t8, 16($sp)
    jal     af_v3_fish_kind
    nop
    lw      $t8, 16($sp)
    addiu   $at, $zero, 88
    bne     $v0, $at, 3f
    lw      $a0, 20($sp)
    addiu   $at, $zero, 45
    beq     $t8, $at, 2f
    addiu   $t0, $zero, 60
    addiu   $at, $zero, 15
    beq     $t8, $at, 2f
    addiu   $t0, $zero, 18
    addiu   $t0, $t8, 1
2:
    move    $t8, $t0
3:
    sw      $t8, 0x214($a0)
    mtc1    $zero, $f0
    sw      $zero, 0x74($a0)
    sw      $zero, 0x7C($a0)
    lw      $ra, 24($sp)
    jr      $ra
    addiu   $sp, $sp, 32
.end af_v3_fish_bite

.globl af_v3_fish_angles
af_v3_fish_angles:
    /* Verified against the complete donor table by the shared installer. */
    .float 3.0, 7.0, 30.0, 50.0, 180.0
    .float 7.5, 15.0, 40.0, 60.0, 180.0
