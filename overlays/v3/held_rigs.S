.set noreorder
.set noat
.section .text.af_v3_held_setup_original, "ax"
.globl af_v3_held_setup_original
.ent af_v3_held_setup_original
af_v3_held_setup_original:
    /* Recreate the overwritten prologue against the current loaded owner. */
    lui     $t9, 0x8014
    lw      $t9, 0x3900($t9)
    lui     $t8, %hi(af_v3_held_setup_displacement)
    addiu   $t8, $t8, %lo(af_v3_held_setup_displacement)
    subu    $t9, $t9, $t8
    addiu   $sp, $sp, -0x30
    jr      $t9
    sw      $s0, 0x24($sp)
.end af_v3_held_setup_original
