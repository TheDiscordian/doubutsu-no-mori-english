# Native name-entry cursor: use the rendered prefix width, retaining the
# original cursor graphic's -8.4-pixel origin adjustment. MIPS o32 hard-float.
# Replaces 24 instructions at linked RAM 0x80884A20. No new overlay symbols.
.set noreorder
.set noat
.text
.globl keyboard_cursor
keyboard_cursor:
    lw      $a0, 0x24($s4)
    lh      $a1, 0x16($s4)
    jal     0x800902CC
    addiu   $a2, $zero, 1
    mtc1    $v0, $f8
    cvt.s.w $f8, $f8
    lui     $at, 0x4106
    ori     $at, $at, 0x6666
    mtc1    $at, $f18
    sub.s   $f4, $f8, $f18
    lwc1    $f6, 0x78($sp)
    lw      $a0, 0x90($sp)
    lw      $a1, 0x94($sp)
    lw      $a3, 0x74($sp)
    add.s   $f8, $f6, $f4
    lui     $t9, 1
    lw      $t5, 0x2C($a0)
    mfc1    $a2, $f8
    addu    $t9, $t9, $t5
    lw      $t9, 0x6E0($t9)
    lw      $t9, 0x2C($t9)
    jalr    $t9
    nop
    nop
